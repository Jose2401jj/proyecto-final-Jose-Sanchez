from django.views.generic import TemplateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.oauth2 import id_token
from google.auth.transport import requests
from google.auth import exceptions as google_auth_exceptions
import json
import os
import secrets
from botocore.exceptions import ClientError

# Configuración de OAuth2
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Solo para desarrollo

class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/settings/settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Información básica del usuario
        context['user_info'] = {
            'full_name': user.get_full_name(),
            'email': user.email,
            'username': user.username,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        
        # Información del perfil de doctor si existe
        if hasattr(user, 'doctorprofile'):
            doctor = user.doctorprofile
            context['doctor_info'] = {
                'specialty': doctor.especialidad,
                'license_number': doctor.numero_licencia,
                'contact': doctor.contacto,
                'biography': doctor.biografia,
                'profile_image': doctor.imagen_perfil.url if doctor.imagen_perfil else None,
                'email_notifications': doctor.notificaciones_email,
                'push_notifications': doctor.notificaciones_push,
                'sound_notifications': doctor.notificaciones_sonido,
                'theme': doctor.tema,
                'primary_color': doctor.color_principal,
                'animations': doctor.animaciones_activas,
                'image_quality': doctor.calidad_imagen,
                'google_account': doctor.google_account
            }
            
            # Estadísticas
            total_diagnosticos = doctor.diagnosticos.count() if hasattr(doctor, 'diagnosticos') else 0
            total_pacientes = doctor.pacientes_atendidos if hasattr(doctor, 'pacientes_atendidos') else 0
            
            # Cálculo de precisión
            if hasattr(doctor, 'diagnosticos'):
                diagnosticos_correctos = doctor.diagnosticos.filter(estado='validado').count()
                precision = (diagnosticos_correctos / total_diagnosticos * 100) if total_diagnosticos > 0 else 0
            else:
                precision = 0
            
            context['statistics'] = {
                'total_diagnosticos': total_diagnosticos,
                'total_pacientes': total_pacientes,
                'precision': round(precision, 1),
                'diagnosticos_correctos': diagnosticos_correctos if 'diagnosticos_correctos' in locals() else 0
            }
            
            # Configuraciones adicionales
            context['settings'] = {
                'appearance': {
                    'themes': [
                        {'value': 'light', 'label': 'Claro'},
                        {'value': 'dark', 'label': 'Oscuro'},
                        {'value': 'system', 'label': 'Sistema'}
                    ],
                    'colors': [
                        {'value': '#2b4c7e', 'label': 'Azul'},
                        {'value': '#1a5f7a', 'label': 'Verde'},
                        {'value': '#86344a', 'label': 'Rojo'}
                    ]
                },
                'image_quality_options': [
                    {'value': 'low', 'label': 'Baja'},
                    {'value': 'medium', 'label': 'Media'},
                    {'value': 'high', 'label': 'Alta'}
                ]
            }
        
        return context

class UpdateProfileView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user = request.user
            
            # Validar datos requeridos
            required_fields = ['first_name', 'last_name', 'email']
            for field in required_fields:
                if not data.get(field):
                    raise ValueError(f'El campo {field} es requerido')
            
            # Actualizar información básica del usuario
            user.first_name = data['first_name']
            user.last_name = data['last_name']
            user.email = data['email']
            user.save()
            
            # Actualizar perfil de doctor si existe
            if hasattr(user, 'doctorprofile'):
                doctor = user.doctorprofile
                doctor.especialidad = data.get('specialty', doctor.especialidad)
                doctor.numero_licencia = data.get('license_number', doctor.numero_licencia)
                doctor.contacto = data.get('contact', doctor.contacto)
                doctor.biografia = data.get('biography', doctor.biografia)
                doctor.save()
            
            messages.success(request, 'Perfil actualizado correctamente')
            return JsonResponse({
                'status': 'success',
                'message': 'Perfil actualizado correctamente'
            })
            
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Error al actualizar el perfil'
            }, status=500)

class UpdateProfileImageView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            if 'profile_image' not in request.FILES:
                raise ValueError('No se ha proporcionado ninguna imagen')
            
            image = request.FILES['profile_image']
            
            # Validar tipo de archivo
            allowed_types = ['image/jpeg', 'image/png']
            if image.content_type not in allowed_types:
                raise ValueError('Tipo de archivo no permitido. Use JPEG o PNG')
                
            # Validar tamaño máximo (5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValueError('La imagen no debe superar los 5MB')
            
            user = request.user
            if hasattr(user, 'doctorprofile'):
                doctor = user.doctorprofile
                # Delete old image from S3 if it exists
                if doctor.imagen_perfil:
                    try:
                        doctor.imagen_perfil.delete()
                    except ClientError as e:
                        # Log the error but proceed with the new upload
                        print(f"Error deleting old image from S3: {str(e)}")
                
                # Save new image to S3
                doctor.imagen_perfil.save(image.name, image, save=True)
                
                messages.success(request, 'Imagen de perfil actualizada')
                return JsonResponse({
                    'status': 'success',
                    'message': 'Imagen de perfil actualizada',
                    'image_url': doctor.imagen_perfil.url
                })
            else:
                raise ValueError('Usuario no tiene perfil de doctor')
                
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except ClientError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al subir la imagen a S3: {str(e)}'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Error al actualizar la imagen'
            }, status=500)

class UpdatePasswordView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user = request.user
            
            # Validar datos requeridos
            required_fields = ['current_password', 'new_password', 'confirm_password']
            for field in required_fields:
                if not data.get(field):
                    raise ValueError(f'El campo {field} es requerido')
            
            # Verificar contraseña actual
            if not user.check_password(data['current_password']):
                raise ValueError('La contraseña actual es incorrecta')
            
            # Verificar que las nuevas contraseñas coincidan
            if data['new_password'] != data['confirm_password']:
                raise ValueError('Las nuevas contraseñas no coinciden')
            
            # Validar complejidad de la contraseña
            if len(data['new_password']) < 8:
                raise ValueError('La contraseña debe tener al menos 8 caracteres')
            
            # Actualizar contraseña
            user.set_password(data['new_password'])
            user.save()
            
            messages.success(request, 'Contraseña actualizada correctamente')
            return JsonResponse({
                'status': 'success',
                'message': 'Contraseña actualizada correctamente'
            })
            
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Error al actualizar la contraseña'
            }, status=500)

class UpdateNotificationsView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user = request.user
            
            if hasattr(user, 'doctorprofile'):
                doctor = user.doctorprofile
                doctor.notificaciones_email = data.get('email_notifications', True)
                doctor.notificaciones_push = data.get('push_notifications', True)
                doctor.notificaciones_sonido = data.get('sound_notifications', True)
                doctor.save()
                
                messages.success(request, 'Preferencias de notificaciones actualizadas')
                return JsonResponse({
                    'status': 'success',
                    'message': 'Preferencias de notificaciones actualizadas'
                })
            else:
                raise ValueError('Usuario no tiene perfil de doctor')
                
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Error al actualizar las notificaciones'
            }, status=500)

class UpdateAppearanceView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user = request.user
            
            if hasattr(user, 'doctorprofile'):
                doctor = user.doctorprofile
                
                # Validar tema
                valid_themes = ['light', 'dark', 'system']
                theme = data.get('theme')
                if theme and theme not in valid_themes:
                    raise ValueError('Tema no válido')
                
                doctor.tema = theme or doctor.tema
                doctor.color_principal = data.get('primary_color', doctor.color_principal)
                doctor.save()
                
                messages.success(request, 'Apariencia actualizada')
                return JsonResponse({
                    'status': 'success',
                    'message': 'Apariencia actualizada'
                })
            else:
                raise ValueError('Usuario no tiene perfil de doctor')
                
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Error al actualizar la apariencia'
            }, status=500)

class UpdateSystemSettingsView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user = request.user
            
            if hasattr(user, 'doctorprofile'):
                doctor = user.doctorprofile
                
                # Validar calidad de imagen
                valid_qualities = ['low', 'medium', 'high']
                quality = data.get('image_quality')
                if quality and quality not in valid_qualities:
                    raise ValueError('Calidad de imagen no válida')
                
                doctor.animaciones_activas = data.get('animations', doctor.animaciones_activas)
                doctor.calidad_imagen = quality or doctor.calidad_imagen
                doctor.save()
                
                messages.success(request, 'Configuración del sistema actualizada')
                return JsonResponse({
                    'status': 'success',
                    'message': 'Configuración del sistema actualizada'
                })
            else:
                raise ValueError('Usuario no tiene perfil de doctor')
                
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Error al actualizar la configuración del sistema'
            }, status=500)

class GoogleAuthView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            # Usar el archivo de configuración del cliente
            flow = Flow.from_client_secrets_file(
                'client_secrets.json',
                scopes=settings.GOOGLE_OAUTH2_SCOPES
            )
            
            # Establecer la URI de redirección
            flow.redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
            
            # Generar estado aleatorio para seguridad
            state = secrets.token_urlsafe(16)
            
            # URL de autorización
            authorization_url = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=state
            )[0]
            
            # Guardar el estado y el flow en la sesión
            request.session['google_auth_state'] = state
            
            return redirect(authorization_url)
            
        except Exception as e:
            messages.error(request, f'Error al iniciar la autenticación con Google: {str(e)}')
            return redirect('core:settings')

class UnlinkGoogleAccountView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            if hasattr(user, 'doctorprofile'):
                doctor = user.doctorprofile
                doctor.google_account = None
                doctor.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Cuenta de Google desvinculada correctamente'
                })
            else:
                raise ValueError('Usuario no tiene perfil de doctor')
                
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Error al desvincular la cuenta de Google'
            }, status=500)

class GoogleAuthCallbackView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            # Verificar el estado
            state = request.GET.get('state')
            stored_state = request.session.get('google_auth_state')
            
            if not state or not stored_state or state != stored_state:
                raise ValueError('Estado de autenticación inválido')
            
            # Crear un nuevo flow para el callback
            flow = Flow.from_client_secrets_file(
                'client_secrets.json',
                scopes=settings.GOOGLE_OAUTH2_SCOPES,
                state=stored_state
            )
            flow.redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
            
            # Obtener el token
            authorization_response = request.build_absolute_uri()
            flow.fetch_token(authorization_response=authorization_response)
            
            # Obtener las credenciales
            credentials = flow.credentials
            
            try:
                # Obtener información del usuario con verificación de tiempo más flexible
                request_obj = requests.Request()
                id_info = id_token.verify_oauth2_token(
                    credentials.id_token,
                    request_obj,
                    settings.GOOGLE_OAUTH2_CLIENT_ID,
                    clock_skew_in_seconds=300
                )
            except google_auth_exceptions.GoogleAuthError as auth_error:
                # Si falla la verificación, intentar obtener la información directamente
                if hasattr(credentials, 'id_token'):
                    id_info = id_token.decode_unverified_id_token(credentials.id_token)
                else:
                    raise auth_error
            
            # Verificar que el token sea para nuestra aplicación
            if id_info['aud'] != settings.GOOGLE_OAUTH2_CLIENT_ID:
                raise ValueError('Token no válido para esta aplicación')
            
            # Guardar el email en el perfil del doctor
            user = request.user
            if hasattr(user, 'doctorprofile'):
                doctor = user.doctorprofile
                doctor.google_account = id_info['email']
                doctor.save()
                
                messages.success(request, 'Cuenta de Google vinculada correctamente')
            else:
                messages.error(request, 'Usuario no tiene perfil de doctor')
            
            # Limpiar el estado de la sesión
            if 'google_auth_state' in request.session:
                del request.session['google_auth_state']
                
            # Redirigir con parámetro de éxito
            return redirect(f"{reverse_lazy('core:settings')}?google_success=true")
            
        except Exception as e:
            messages.error(request, f'Error al vincular la cuenta de Google: {str(e)}')
            return redirect('core:settings')