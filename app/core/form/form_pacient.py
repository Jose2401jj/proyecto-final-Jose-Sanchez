from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from app.core.models import Paciente

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['dni', 'nombres', 'apellidos', 'birth_date', 'sexo', 'direccion', 'contacto', 'historial_clinico']

        widgets = {
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el DNI'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el nombre'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese los apellidos'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexo': forms.Select(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese la dirección'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el contacto'}),
            'historial_clinico': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ingrese el historial clínico'}),
        }

        labels = {
            'dni': 'DNI',
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'birth_date': 'Fecha de Nacimiento',
            'sexo': 'Género',
            'direccion': 'Dirección',
            'contacto': 'Contacto',
            'historial_clinico': 'Historial Clínico',
        }

        help_texts = {
            'dni': 'Debe contener exactamente 10 dígitos.',
            'contacto': 'Ejemplo: 0991234567',
        }

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if not dni.isdigit():
            raise ValidationError("El DNI debe contener solo números.")
        if len(dni) != 10:
            raise ValidationError("El DNI debe tener exactamente 10 dígitos.")
        if Paciente.objects.exclude(pk=self.instance.pk).filter(dni=dni).exists():
            raise ValidationError("Este DNI ya está registrado.")
        return dni

    def clean_nombres(self):
        nombres = self.cleaned_data.get('nombres')
        if not all(part.isalpha() for part in nombres.split()):
            raise ValidationError("El nombre solo debe contener letras y espacios.")
        return nombres

    def clean_apellidos(self):
        apellidos = self.cleaned_data.get('apellidos')
        if not all(part.isalpha() for part in apellidos.split()):
            raise ValidationError("Los apellidos solo deben contener letras y espacios.")
        return apellidos

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date and birth_date > timezone.now().date():
            raise ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        return birth_date

    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion')
        if not direccion.strip():
            raise ValidationError("La dirección no puede estar vacía.")
        return direccion

    def clean_contacto(self):
        contacto = self.cleaned_data.get('contacto')
        
        if not contacto.isdigit():
            raise ValidationError("El contacto debe contener solo números.")
        
        if len(contacto) != 10:
            raise ValidationError("El contacto debe tener exactamente 10 dígitos.")
        
        return contacto

    def clean_historial_clinico(self):
        historial = self.cleaned_data.get('historial_clinico')
        if not historial.strip():
            raise ValidationError("El historial clínico no puede estar vacío.")
        return historial
