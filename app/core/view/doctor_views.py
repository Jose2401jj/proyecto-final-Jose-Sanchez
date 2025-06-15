from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from app.core.form.form_doctor import DoctorCreationForm
from django.core.mail import send_mail
from django.conf import settings
from app.core.models import DoctorProfile
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

class DoctorCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = DoctorCreationForm
    template_name = 'dashboard/doctor/doctor_form.html'
    success_url = reverse_lazy('core:dashboard')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "Solo los administradores pueden crear cuentas de doctores.")
        return super().handle_no_permission()

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        password = form.cleaned_data.get('password1')

        # Enviar credenciales por correo
        subject = 'Credenciales de Acceso - Sistema NeumScan'
        
        # Contenido HTML del correo
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #2C3E50; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
                    <h1 style="color: #ffffff; margin: 0;">NeumScan</h1>
                </div>
                
                <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e9e9e9; border-radius: 0 0 5px 5px;">
                    <h2 style="color: #2C3E50; margin-top: 0;">Bienvenido/a Dr. {user.get_full_name()}</h2>
                    
                    <p style="color: #666666;">Se ha creado una cuenta para usted en el sistema NeumScan. A continuación, encontrará sus credenciales de acceso:</p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0; color: #2C3E50;">
                            <strong>Usuario:</strong> {user.username}<br>
                            <strong>Contraseña:</strong> {password}
                        </p>
                    </div>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0; color: #856404;">
                            <strong>Importante:</strong> Por motivos de seguridad, le recomendamos cambiar su contraseña después de iniciar sesión por primera vez.
                        </p>
                    </div>
                    
                    <p style="color: #666666;">Para acceder al sistema, haga clic en el siguiente botón:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:8000/security/login" 
                           style="background-color: #2C3E50; 
                                  color: #ffffff; 
                                  padding: 12px 30px; 
                                  text-decoration: none; 
                                  border-radius: 5px; 
                                  display: inline-block;">
                            Iniciar Sesión
                        </a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #e9e9e9; margin: 30px 0;">
                    
                    <p style="color: #666666; font-size: 14px; text-align: center; margin: 0;">
                        Si tiene alguna pregunta, no dude en contactar al equipo de soporte.<br>
                        Saludos cordiales,<br>
                        <strong>Equipo NeumScan</strong>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Contenido de texto plano como respaldo
        text_content = f"""
        Estimado/a Dr. {user.get_full_name()},

        Se ha creado una cuenta para usted en el sistema NeumScan.
        Sus credenciales de acceso son:

        Usuario: {user.username}
        Contraseña: {password}

        Por favor, ingrese al sistema y cambie su contraseña por motivos de seguridad.

        Saludos cordiales,
        Equipo NeumScan
        """
        
        try:
            # Crear el correo con ambas versiones (HTML y texto plano)
            email = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            messages.success(self.request, f"Cuenta creada exitosamente. Las credenciales han sido enviadas a {user.email}")
        except Exception as e:
            messages.warning(self.request, "Cuenta creada pero hubo un problema al enviar las credenciales por correo.")
        
        return response

class DoctorListView(LoginRequiredMixin, ListView):
    model = DoctorProfile
    template_name = 'dashboard/doctor/doctor_list.html'
    context_object_name = 'doctores'
    paginate_by = 5
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        filter_type = self.request.GET.get('filter_type', 'nombre')
        
        if search_query:
            if filter_type == 'nombre':
                queryset = queryset.filter(user__first_name__icontains=search_query) | \
                          queryset.filter(user__last_name__icontains=search_query)
            elif filter_type == 'especialidad':
                queryset = queryset.filter(especialidad__icontains=search_query)
            elif filter_type == 'licencia':
                queryset = queryset.filter(numero_licencia__icontains=search_query)
            elif filter_type == 'email':
                queryset = queryset.filter(user__email__icontains=search_query)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['filter_type'] = self.request.GET.get('filter_type', 'nombre')
        
        for doctor in context['doctores']:
            # Agregar estadísticas para cada doctor
            total_diagnosticos = doctor.diagnosticos.count() if hasattr(doctor, 'diagnosticos') else 0
            diagnosticos_correctos = doctor.diagnosticos.filter(estado='validado').count() if hasattr(doctor, 'diagnosticos') else 0
            precision = (diagnosticos_correctos / total_diagnosticos * 100) if total_diagnosticos > 0 else 0
            
            doctor.stats = {
                'total_diagnosticos': total_diagnosticos,
                'total_pacientes': doctor.pacientes_atendidos,
                'precision': round(precision, 1)
            }
        return context 