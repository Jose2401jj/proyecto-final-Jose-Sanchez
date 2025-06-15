from django.urls import path
from app.core import views
from django.conf import settings
from django.conf.urls.static import static
from app.core.view.paciente_views import PacienteListView, PacienteCreateView, PacienteUpdateView, PacienteDeleteView
from app.core.view.escaneo_views import AnalisisImagenView , BuscarPacienteAPIView,ProcesarAnalisisAPIView, DiagnosticoDeleteView
from app.core.view.report_views import ReportListView,ReportDetailView
from app.core.view.revision_escaneo import RevisionManualView, ValidarResultadoView
from app.core.views import statistics_view
from app.core.view.settings_views import (
    SettingsView, UpdateProfileView, UpdateProfileImageView,
    UpdatePasswordView, UpdateNotificationsView,
    UpdateAppearanceView, UpdateSystemSettingsView,
    GoogleAuthView, UnlinkGoogleAccountView, GoogleAuthCallbackView
)
from app.core.view.doctor_views import DoctorCreateView, DoctorListView

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('pacientes/', PacienteListView.as_view(), name='pacient_list'),
    path('pacientes/crear/', PacienteCreateView.as_view(), name='pacient_create'),
    path('pacientes/editar/<int:pk>/', PacienteUpdateView.as_view(), name='pacient_update'),
    path('pacientes/eliminar/<int:pk>/', PacienteDeleteView.as_view(), name='pacient_delete'),
    path('scan_list/', views.scan_list, name='scan_list'),
    path('scan/eliminar/<int:pk>/', DiagnosticoDeleteView.as_view(), name='scan_delete'),
    path('procesar-analisis/', AnalisisImagenView.as_view(), name='form_procesar_analisis'),
    path('api/buscar-paciente/', BuscarPacienteAPIView.as_view(), name='buscar_paciente_dni'),
    path('api/procesar-analisis/', ProcesarAnalisisAPIView.as_view(), name='procesar_analisis'),
    path('report_list/', ReportListView.as_view(), name='report_list'),
    path('report_detail/<int:pk>/', ReportDetailView.as_view(), name='report_detail'),
    
    # URLs de revisión manual
    path('revision-manual/', RevisionManualView.as_view(), name='revision_manual'),
    path('revision-manual/<int:diagnostico_id>/', RevisionManualView.as_view(), name='revision_manual_detalle'),
    path('validar-resultado/<int:diagnostico_id>/', ValidarResultadoView.as_view(), name='validar_resultado'),
    
    # URLs de configuración
    path('settings/', SettingsView.as_view(), name='settings'),
    path('settings/profile/update/', UpdateProfileView.as_view(), name='update_profile'),
    path('statistics/', statistics_view, name='statistics'),
    path('settings/profile/image/', UpdateProfileImageView.as_view(), name='update_profile_image'),
    path('settings/password/', UpdatePasswordView.as_view(), name='update_password'),
    path('settings/notifications/', UpdateNotificationsView.as_view(), name='update_notifications'),
    path('settings/appearance/', UpdateAppearanceView.as_view(), name='update_appearance'),
    path('settings/system/', UpdateSystemSettingsView.as_view(), name='update_system_settings'),
    path('settings/google/auth/', GoogleAuthView.as_view(), name='google_auth'),
    path('settings/google/unlink/', UnlinkGoogleAccountView.as_view(), name='unlink_google'),
    path('settings/google/callback/', GoogleAuthCallbackView.as_view(), name='google_callback'),
    path('doctor/create/', DoctorCreateView.as_view(), name='doctor_create'),
    path('doctores/', DoctorListView.as_view(), name='doctor_list'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
