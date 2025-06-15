from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from datetime import date
import os
from storages.backends.s3boto3 import S3Boto3Storage

# Custom S3 storage for profile images
class S3ProfileImageStorage(S3Boto3Storage):
    location = 'doctores/perfiles'
    file_overwrite = False

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    especialidad = models.CharField(max_length=100)
    numero_licencia = models.CharField(max_length=50, blank=True, null=True)
    contacto = models.CharField(max_length=100, blank=True, null=True)
    biografia = models.TextField(blank=True, null=True)
    imagen_perfil = models.ImageField(
        storage=S3ProfileImageStorage(),
        upload_to='',
        blank=True,
        null=True
    )
    
    # Cuenta de Google
    google_account = models.EmailField(max_length=255, blank=True, null=True)
    
    # Configuraciones de notificaciones
    notificaciones_email = models.BooleanField(default=True)
    notificaciones_push = models.BooleanField(default=True)
    notificaciones_sonido = models.BooleanField(default=True)
    
    # Configuraciones de apariencia
    tema = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Claro'),
        ('dark', 'Oscuro'),
        ('system', 'Sistema')
    ])
    color_principal = models.CharField(max_length=7, default='#2b4c7e')
    
    # Configuraciones del sistema
    animaciones_activas = models.BooleanField(default=True)
    calidad_imagen = models.CharField(max_length=10, default='high', choices=[
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta')
    ])
    
    # Estadísticas
    pacientes_atendidos = models.IntegerField(default=0)

    def __str__(self):
        return f'Dr. {self.user.get_full_name()}'

    @property
    def total_diagnosticos(self):
        return self.diagnosticos.count()

    @property
    def diagnosticos_correctos(self):
        return self.diagnosticos.filter(estado='validado').count()

    @property
    def precision(self):
        total = self.total_diagnosticos
        if total > 0:
            return (self.diagnosticos_correctos / total) * 100
        return 0
class Paciente(models.Model):
    SEXO_CHOICES = [('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')]
    dni = models.CharField(max_length=10, unique=True)
    nombres = models.CharField(max_length=255)
    apellidos = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    direccion = models.TextField()
    contacto = models.CharField(max_length=100)
    historial_clinico = models.TextField(blank=True)

    def __str__(self):
        return f'{self.nombres} {self.apellidos}'

    def edad(self):
        if self.birth_date:
            today = date.today()
            age = today.year - self.birth_date.year
            if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
                age -= 1
            return age
        return None
    
class Diagnostico(models.Model):
    ESTADO_DIAGNOSTICO = [('pendiente', 'Pendiente'), ('validado', 'Validado'), ('rechazado', 'Rechazado')]
    
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='diagnosticos')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True, related_name='diagnosticos')
    fecha_diagnostico = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_DIAGNOSTICO, default='pendiente')
    observaciones_medicas = models.TextField(blank=True)

    def __str__(self):
        return f'Dx de {self.paciente.nombres} ({self.fecha_diagnostico.date()})'

class ImagenDiagnostico(models.Model):
    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE, related_name='imagenes')
    
    imagen_original = models.FileField(
        upload_to='imagenes/originales/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'png', 'dcm'])]
    )
    imagen_procesada = models.FileField(
        upload_to='imagenes/procesadas/%Y/%m/%d/',
        null=True, blank=True
    )
    gradcam = models.FileField(
        upload_to='imagenes/gradcam/%Y/%m/%d/',
        null=True, blank=True
    )
    fecha_carga = models.DateTimeField(auto_now_add=True)

    def delete(self, *args, **kwargs):
        for f in [self.imagen_original, self.imagen_procesada, self.gradcam]:
            if f and os.path.isfile(f.path):
                os.remove(f.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f'Imagen Dx {self.diagnostico.id} - {self.pk}'
class ResultadoIA(models.Model):
    TIPO_DIAGNOSTICO = [
        ('normal', 'Normal'),
        ('neumonia_viral', 'Neumonía Viral'),
        ('neumonia_bacteriana', 'Neumonía Bacteriana'),
        ('otros', 'Otros'),
    ]

    imagen = models.OneToOneField(ImagenDiagnostico, on_delete=models.CASCADE, related_name='resultado_ia')
    diagnostico_principal = models.CharField(max_length=100)
    tipo_diagnostico = models.CharField(max_length=30, choices=TIPO_DIAGNOSTICO)
    confianza = models.FloatField()
    hallazgos = models.TextField()
    recomendaciones = models.TextField()
    areas_afectadas = models.JSONField(null=True, blank=True)
    severidad = models.CharField(max_length=50, null=True, blank=True)
    coordenadas_roi = models.JSONField(null=True, blank=True)
    fecha_procesamiento = models.DateTimeField(auto_now_add=True)
    tiempo_procesamiento = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f'IA Dx: {self.tipo_diagnostico} ({self.confianza}%)'
    
class InformePDF(models.Model):
    diagnostico = models.OneToOneField(Diagnostico, on_delete=models.CASCADE)
    archivo_pdf = models.FileField(upload_to='informes/')
    generado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Informe PDF Dx {self.diagnostico.id}'

class AlertaMedica(models.Model):
    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE)
    mensaje = models.TextField()
    enviada = models.BooleanField(default=False)
    fecha_alerta = models.DateTimeField(auto_now_add=True)

class Retroalimentacion(models.Model):
    diagnostico = models.OneToOneField(Diagnostico, on_delete=models.CASCADE)
    valida = models.BooleanField()
    comentarios = models.TextField(blank=True)
    fecha_retroalimentacion = models.DateTimeField(auto_now_add=True)
