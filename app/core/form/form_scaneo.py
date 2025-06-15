from django import forms
from django.core.exceptions import ValidationError
from app.core.models import Paciente
import os

class EscaneoForm(forms.Form):
    paciente = forms.ModelChoiceField(
        queryset=Paciente.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control form-control-lg',
            'required': True
        }),
        label='Seleccionar Paciente'
    )
    
    imagen = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control form-control-lg',
            'accept': '.jpg,.jpeg,.png,.dcm',
            'required': True
        }),
        label='Imagen para Diagnóstico',
        help_text='Formatos permitidos: JPG, PNG, DCM. Tamaño máximo: 10MB'
    )
    
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Observaciones adicionales del médico...'
        }),
        label='Observaciones Médicas',
        required=False,
        max_length=1000
    )
    
    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        
        if imagen:
            # Validar tamaño del archivo (10MB máximo)
            if imagen.size > 10 * 1024 * 1024:
                raise ValidationError('El archivo es demasiado grande. Máximo 10MB.')
            
            # Validar extensión
            nombre_archivo = imagen.name.lower()
            extensiones_validas = ['.jpg', '.jpeg', '.png', '.dcm']
            if not any(nombre_archivo.endswith(ext) for ext in extensiones_validas):
                raise ValidationError('Formato de archivo no válido. Use JPG, PNG o DCM.')
            
            # Validar que sea una imagen real (excepto DCM)
            if not nombre_archivo.endswith('.dcm'):
                try:
                    from PIL import Image
                    imagen.seek(0)
                    img = Image.open(imagen)
                    img.verify()
                    imagen.seek(0)  # Reset file pointer
                except Exception:
                    raise ValidationError('El archivo no es una imagen válida.')
        
        return imagen

class BuscarPacienteForm(forms.Form):
    """Formulario para buscar pacientes"""
    busqueda = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por DNI, nombres o apellidos...',
            'autocomplete': 'off'
        }),
        label='',
        max_length=255
    )

class ValidarDiagnosticoForm(forms.Form):
    """Formulario para validar o rechazar diagnósticos"""
    ACCIONES = [
        ('validar', 'Validar Diagnóstico'),
        ('rechazar', 'Rechazar Diagnóstico'),
    ]
    
    accion = forms.ChoiceField(
        choices=ACCIONES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Acción'
    )
    
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones sobre la validación...'
        }),
        label='Observaciones',
        required=False,
        max_length=500
    )