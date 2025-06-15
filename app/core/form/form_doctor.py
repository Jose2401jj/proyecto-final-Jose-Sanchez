from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from app.core.models import DoctorProfile

class DoctorCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='Nombres')
    last_name = forms.CharField(max_length=30, required=True, label='Apellidos')
    email = forms.EmailField(max_length=254, required=True, label='Correo Electrónico')
    especialidad = forms.CharField(max_length=100, required=True, label='Especialidad')
    numero_licencia = forms.CharField(max_length=50, required=True, label='Número de Licencia')
    contacto = forms.CharField(max_length=100, required=True, label='Teléfono de Contacto')
    biografia = forms.CharField(widget=forms.Textarea, required=False, label='Biografía')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            doctor_profile = DoctorProfile.objects.create(
                user=user,
                especialidad=self.cleaned_data['especialidad'],
                numero_licencia=self.cleaned_data['numero_licencia'],
                contacto=self.cleaned_data['contacto'],
                biografia=self.cleaned_data['biografia']
            )
        
        return user 