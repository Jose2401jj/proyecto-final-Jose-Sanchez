from django.contrib import admin

# Register your models here.
from .models import (
    DoctorProfile,
    Paciente, 
    Diagnostico,
    ImagenDiagnostico,
    ResultadoIA,
    InformePDF
 
)
admin.site.register(DoctorProfile)
admin.site.register(Paciente)
admin.site.register(Diagnostico)
admin.site.register(ImagenDiagnostico)
admin.site.register(ResultadoIA)
admin.site.register(InformePDF)

