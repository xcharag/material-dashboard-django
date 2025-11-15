from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class Product(models.Model):
    id    = models.AutoField(primary_key=True)
    name  = models.CharField(max_length = 100) 
    info  = models.CharField(max_length = 100, default = '')
    price = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name

class Patient(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    professional = models.ForeignKey('Professional', on_delete=models.SET_NULL, blank=True, null=True, related_name='patients')
    color = models.CharField(max_length=7, blank=True, default='', help_text="Hex color (#RRGGBB) for calendar display")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Professional(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    ROLE_CHOICES = [
        ('psychologist', 'Psicólogo'),
        ('psychiatrist', 'Psiquiatra'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    specialty = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Extended profile fields
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    biography = models.TextField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    GENDER_CHOICES = [
        ('male', 'Masculino'),
        ('female', 'Femenino'),
        ('other', 'Otro'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    ID_TYPE_CHOICES = [
        ('ci', 'CI'),
        ('passport', 'Pasaporte'),
        ('ci_extranjero', 'CI Extranjero'),
    ]
    identification_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES, blank=True, null=True)
    identification_number = models.CharField(max_length=50, blank=True, null=True)
    identification_extension = models.CharField(max_length=50, blank=True, null=True)
    license_number = models.CharField(max_length=100, blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    specializations = models.TextField(blank=True, null=True)
    years_experience = models.IntegerField(blank=True, null=True)
    languages_spoken = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"


class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='consultations')
    consultory = models.CharField(max_length=20)
    consultorio_fk = models.ForeignKey('Consultorio', on_delete=models.SET_NULL, null=True, blank=True, related_name='consultations')
    date = models.DateField()
    time = models.TimeField()
    duration = models.IntegerField(default=60)  # in minutes
    charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('attended', 'Atendida'),
        ('completed', 'Terminada'),
        ('no_show', 'No Atendida'),
        ('cancelled', 'Cancelada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.patient} - {self.date} {self.time}"


class Consultorio(models.Model):
    name = models.CharField(max_length=50, unique=True)
    address = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# --- New models for session notes and attachments ---
def consultation_upload_path(instance, filename):
    # Files stored under consultations/<consultation_id>/<type>/<filename>
    folder = instance.file_type if hasattr(instance, 'file_type') and instance.file_type else 'otros'
    return f"consultations/{instance.consultation_id}/{folder}/{filename}"


class ConsultationNote(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='session_notes')
    title = models.CharField(max_length=200, blank=True, default='')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='consultation_notes')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Nota #{self.id} - Cita {self.consultation_id}"


class ConsultationAttachment(models.Model):
    TYPE_CHOICES = [
        ('notas', 'Notas'),
        ('examenes', 'Exámenes'),
        ('resultados', 'Resultados'),
        ('documentos', 'Documentos'),
    ]

    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=consultation_upload_path)
    file_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    display_name = models.CharField(max_length=255, blank=True, default='')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='consultation_attachments')
    # OpenAI Files API id to allow the model to access the attachment
    openai_file_id = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Adjunto #{self.id} - {self.file_type}"

    def save(self, *args, **kwargs):
        # If no display name, fallback to file base name
        if not self.display_name and self.file:
            self.display_name = str(self.file.name).split('/')[-1]
        super().save(*args, **kwargs)


# --- New models for professional contacts and availability ---
class ProfessionalContact(models.Model):
    class ContactType(models.TextChoices):
        WEBSITE = 'website', 'Website'
        PHONE = 'phone', 'Teléfono'
        EMAIL = 'email', 'Correo'
        SOCIAL = 'social', 'Redes Sociales'

    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='contacts')
    type = models.CharField(max_length=20, choices=ContactType.choices)
    label = models.CharField(max_length=100, blank=True, default='')
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ('professional', 'value')

    def __str__(self):
        return f"{self.get_type_display()}: {self.value}"


class WeeklyAvailability(models.Model):
    WEEKDAY_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='weekly_availability')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('professional', 'weekday')
        ordering = ['weekday']

    def __str__(self):
        return f"{self.get_weekday_display()} - {'Cerrado' if self.is_closed else f'{self.start_time}-{self.end_time}'}"


class AvailabilityException(models.Model):
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='availability_exceptions')
    date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('professional', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.date} - {'Cerrado' if self.is_closed else f'{self.start_time}-{self.end_time}'}"


class ProfessionalMedia(models.Model):
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='media')
    image = models.ImageField(upload_to='professional_media/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Media #{self.id} for {self.professional}"


# --- AI assistant models ---
class PatientAIThread(models.Model):
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='ai_threads')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='ai_threads')
    title = models.CharField(max_length=255, blank=True, default='')
    context = models.TextField(blank=True, default='')  # Aggregated clinical context used as system/basis context
    model = models.CharField(max_length=100, blank=True, default='gpt-4o-mini')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('professional', 'patient')
        ordering = ['-updated_at']

    def __str__(self):
        return f"AI Thread {self.id} - {self.patient}"


class PatientAIMessage(models.Model):
    ROLE_CHOICES = [
        ('system', 'system'),
        ('user', 'user'),
        ('assistant', 'assistant'),
    ]
    thread = models.ForeignKey(PatientAIThread, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role} msg #{self.id} on thread {self.thread_id}"