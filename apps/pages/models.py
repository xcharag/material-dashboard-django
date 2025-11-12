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

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"


class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='consultations')
    consultory = models.CharField(max_length=20)
    date = models.DateField()
    time = models.TimeField()
    duration = models.IntegerField(default=60)  # in minutes
    charge = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} - {self.date} {self.time}"


# --- New models for session notes and attachments ---
def consultation_upload_path(instance, filename):
    # Files stored under consultations/<consultation_id>/<type>/<filename>
    folder = instance.file_type if hasattr(instance, 'file_type') and instance.file_type else 'otros'
    return f"consultations/{instance.consultation_id}/{folder}/{filename}"


class ConsultationNote(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='session_notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
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
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='consultation_attachments')

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Adjunto #{self.id} - {self.file_type}"