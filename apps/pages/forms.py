from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import ConsultationNote, ConsultationAttachment
from .models import Professional, ProfessionalContact, WeeklyAvailability, AvailabilityException
from django.forms import DateInput, TimeInput

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
            'title': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'Título (opcional)'}),
            'content': forms.Textarea(attrs={'class': 'form-control bg-light', 'rows': 4, 'placeholder': 'Escribe tus notas aquí...'}),
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
            'file_type': forms.Select(attrs={'class': 'form-select'}),
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
            'file_type': forms.Select(attrs={'class': 'form-select'}),
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


class ProfessionalProfileForm(forms.ModelForm):
    class Meta:
        model = Professional
        fields = [
            'first_name','last_name','profile_picture','biography','birth_date','gender','nationality',
            'identification_type','identification_number','identification_extension','license_number',
            'education','specializations','years_experience','languages_spoken','phone','email','specialty'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type':'date','class':'form-control'}),
            'biography': forms.Textarea(attrs={'class':'form-control','rows':3}),
            'education': forms.Textarea(attrs={'class':'form-control','rows':3}),
            'specializations': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'languages_spoken': forms.TextInput(attrs={'class':'form-control','placeholder':'Ej: Español, Inglés'}),
            'years_experience': forms.NumberInput(attrs={'class':'form-control'}),
            'first_name': forms.TextInput(attrs={'class':'form-control'}),
            'last_name': forms.TextInput(attrs={'class':'form-control'}),
            'nationality': forms.TextInput(attrs={'class':'form-control'}),
            'identification_number': forms.TextInput(attrs={'class':'form-control'}),
            'identification_extension': forms.TextInput(attrs={'class':'form-control'}),
            'license_number': forms.TextInput(attrs={'class':'form-control'}),
            'phone': forms.TextInput(attrs={'class':'form-control'}),
            'email': forms.EmailInput(attrs={'class':'form-control'}),
            'specialty': forms.TextInput(attrs={'class':'form-control'}),
            'gender': forms.Select(attrs={'class':'form-select'}),
            'identification_type': forms.Select(attrs={'class':'form-select'}),
        }

class ProfessionalContactForm(forms.ModelForm):
    class Meta:
        model = ProfessionalContact
        fields = ['type','label','value']
        widgets = {
            'type': forms.Select(attrs={'class':'form-select'}),
            'label': forms.TextInput(attrs={'class':'form-control','placeholder':'Etiqueta/Descripción'}),
            'value': forms.TextInput(attrs={'class':'form-control','placeholder':'Valor (URL, número, etc.)'}),
        }

    def clean_value(self):
        value = self.cleaned_data['value']
        prof = self.initial.get('professional')
        if prof and ProfessionalContact.objects.filter(professional=prof, value=value).exists():
            raise forms.ValidationError('Este valor ya está registrado.')
        return value


class AvailabilityExceptionForm(forms.ModelForm):
    class Meta:
        model = AvailabilityException
        fields = ['date','start_time','end_time','is_closed']
        widgets = {
            'date': DateInput(attrs={'type':'date','class':'form-control'}),
            'start_time': TimeInput(attrs={'type':'time','class':'form-control'}),
            'end_time': TimeInput(attrs={'type':'time','class':'form-control'}),
            'is_closed': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }
        labels = {
            'date': 'Fecha',
            'start_time': 'Hora Inicio',
            'end_time': 'Hora Fin',
            'is_closed': 'Cerrar todo el día',
        }

    def clean(self):
        cleaned = super().clean()
        is_closed = cleaned.get('is_closed')
        start = cleaned.get('start_time')
        end = cleaned.get('end_time')
        if not is_closed and (not start or not end):
            raise forms.ValidationError('Debe proporcionar hora inicio y fin o marcar como cerrado.')
        if start and end and start >= end:
            raise forms.ValidationError('La hora de inicio debe ser menor que la hora fin.')
        return cleaned

