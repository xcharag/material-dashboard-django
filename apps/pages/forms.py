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
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título (opcional)'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Escribe tus notas aquí...'}),
        }
        labels = {
            'title': 'Título',
            'content': 'Contenido',
        }


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = ConsultationAttachment
        fields = ['file_type', 'display_name', 'file']
        widgets = {
            'file_type': forms.Select(attrs={'class': 'form-control'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre para mostrar (opcional)'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.txt,.md'}),
        }
        labels = {
            'file_type': 'Tipo de documento',
            'display_name': 'Nombre',
            'file': 'Archivo',
        }

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if f:
            allowed = ('.pdf', '.doc', '.docx', '.txt', '.md')
            if not f.name.lower().endswith(allowed):
                raise forms.ValidationError('Formatos permitidos: PDF, DOC, DOCX, TXT, MD.')
        return f


class AttachmentRenameForm(forms.ModelForm):
    class Meta:
        model = ConsultationAttachment
        fields = ['display_name', 'file_type']
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'file_type': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'display_name': 'Nombre',
            'file_type': 'Tipo',
        }

class NoteEditForm(forms.ModelForm):
    class Meta:
        model = ConsultationNote
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'title': 'Título',
            'content': 'Contenido',
        }
