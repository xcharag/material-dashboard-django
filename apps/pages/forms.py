from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import ConsultationNote, ConsultationAttachment

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
        }),
    )

    error_messages = {
        'invalid_login': _(
            "Por favor, introduzca un nombre de usuario y contraseña correctos. "
            "Observe que ambos campos pueden ser sensibles a mayúsculas."
        ),
        'inactive': _("Esta cuenta está inactiva."),
    }

class UsernameRecoveryForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        }),
        label='Correo Electrónico',  # Remove label to avoid duplication
        help_text='Ingresa tu correo electrónico y te enviaremos tu nombre de usuario.'
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "No se encontró ninguna cuenta con este correo electrónico."
            )
        return email


class NoteForm(forms.ModelForm):
    class Meta:
        model = ConsultationNote
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Escribe tus notas aquí...'}),
        }
        labels = {
            'content': 'Notas de la sesión',
        }


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = ConsultationAttachment
        fields = ['file_type', 'file']
        widgets = {
            'file_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'application/pdf'}),
        }
        labels = {
            'file_type': 'Tipo de documento',
            'file': 'Archivo (PDF)',
        }

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if f and not f.name.lower().endswith('.pdf'):
            raise forms.ValidationError('Solo se permiten archivos PDF.')
        return f
