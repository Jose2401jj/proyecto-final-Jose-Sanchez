from django.views.generic import FormView, CreateView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.urls import reverse_lazy, reverse
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth import logout
from app.security.models import User
from django.views import View
from django.contrib.auth.models import User
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
from google.auth import exceptions as google_auth_exceptions
from app.core.models import DoctorProfile
import os
import secrets

# Configuración de OAuth2
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Solo para desarrollo

class SigninView(FormView):
    form_class = AuthenticationForm
    template_name = "security/auth/login.html"
    success_url = reverse_lazy("core:dashboard")

    def form_valid(self, form):
        username = form.cleaned_data.get('username')  
        password = form.cleaned_data.get('password')

        user = authenticate(self.request, username=username, password=password)

        if user is None:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(self.request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None and user.is_active:
            backend = 'django.contrib.auth.backends.ModelBackend'
            user.backend = backend
            auth_login(self.request, user)  
            return redirect(self.get_success_url())
        else:
            messages.error(self.request, "Credenciales incorrectas o cuenta inactiva.")
            return self.form_invalid(form)


def logout_view(request):
    logout(request)
    messages.success(request, 'Sesión cerrada exitosamente')
    return redirect('security:login')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                login(request, user)
                messages.success(request, 'Inicio de sesión exitoso')
                return redirect('core:dashboard')
            else:
                messages.error(request, 'Contraseña incorrecta')
        except User.DoesNotExist:
            messages.error(request, 'Usuario no encontrado')
        
    return render(request, 'security/auth/login.html')

class GoogleLoginView(View):
    def get(self, request, *args, **kwargs):
        try:
            # Limpiar cualquier estado anterior
            if 'google_auth_state' in request.session:
                del request.session['google_auth_state']
            
            # Crear la URL de callback absoluta
            callback_uri = request.build_absolute_uri(reverse('security:google_login_callback'))
            
            # Usar el archivo de configuración del cliente
            flow = Flow.from_client_secrets_file(
                'client_secrets.json',
                scopes=settings.GOOGLE_OAUTH2_SCOPES
            )
            
            # Establecer la URI de redirección
            flow.redirect_uri = callback_uri
            
            # Generar estado aleatorio para seguridad
            state = secrets.token_urlsafe(16)
            
            # URL de autorización
            authorization_url = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=state,
                prompt='consent'
            )[0]
            
            # Guardar el estado en la sesión
            request.session['google_auth_state'] = state
            
            return redirect(authorization_url)
            
        except Exception as e:
            messages.error(request, f'Error al iniciar la autenticación con Google: {str(e)}')
            return redirect('security:login')

class GoogleLoginCallbackView(View):
    def get(self, request, *args, **kwargs):
        try:
            # Verificar el estado
            state = request.GET.get('state')
            stored_state = request.session.get('google_auth_state')
            
            if not state or not stored_state or state != stored_state:
                raise ValueError('Estado de autenticación inválido')
            
            # Crear la URL de callback absoluta
            callback_uri = request.build_absolute_uri(reverse('security:google_login_callback'))
            
            # Crear un nuevo flow para el callback
            flow = Flow.from_client_secrets_file(
                'client_secrets.json',
                scopes=settings.GOOGLE_OAUTH2_SCOPES,
                state=stored_state
            )
            flow.redirect_uri = callback_uri
            
            # Obtener el token
            flow.fetch_token(
                authorization_response=request.build_absolute_uri()
            )
            
            # Obtener las credenciales
            credentials = flow.credentials
            
            try:
                # Obtener información del usuario
                id_info = id_token.verify_oauth2_token(
                    credentials.id_token,
                    requests.Request(),
                    settings.GOOGLE_OAUTH2_CLIENT_ID,
                    clock_skew_in_seconds=300
                )
            except google_auth_exceptions.GoogleAuthError as auth_error:
                if hasattr(credentials, 'id_token'):
                    id_info = id_token.decode_unverified_id_token(credentials.id_token)
                else:
                    raise auth_error
            
            # Verificar que el token sea para nuestra aplicación
            if id_info['aud'] != settings.GOOGLE_OAUTH2_CLIENT_ID:
                raise ValueError('Token no válido para esta aplicación')
            
            # Obtener el email del usuario de Google
            email = id_info['email']
            
            # Buscar usuario por cuenta de Google vinculada
            try:
                doctor_profile = DoctorProfile.objects.get(google_account=email)
                user = doctor_profile.user
                messages.success(request, 'Inicio de sesión con Google exitoso')
            except DoctorProfile.DoesNotExist:
                # Si no hay cuenta vinculada, buscar por email
                try:
                    user = User.objects.get(email=email)
                    # Vincular la cuenta de Google
                    if hasattr(user, 'doctorprofile'):
                        user.doctorprofile.google_account = email
                        user.doctorprofile.save()
                        messages.success(request, 'Cuenta vinculada y sesión iniciada')
                        login(request, user)
                        return redirect('core:dashboard')
                    else:
                        messages.error(request, 'La cuenta de Google no está vinculada a un perfil de doctor.')
                        return redirect('security:login')
                except User.DoesNotExist:
                    messages.error(request, 'No existe una cuenta con este correo electrónico. Por favor, contacte al administrador.')
                    return redirect('security:login')
            
            # Iniciar sesión
            login(request, user)
            
            # Limpiar el estado de la sesión
            if 'google_auth_state' in request.session:
                del request.session['google_auth_state']
            
            return redirect('core:dashboard')
            
        except Exception as e:
            # Limpiar el estado en caso de error
            if 'google_auth_state' in request.session:
                del request.session['google_auth_state']
            messages.error(request, f'Error al iniciar sesión con Google: {str(e)}')
            return redirect('security:login')