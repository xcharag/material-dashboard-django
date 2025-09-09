from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

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
