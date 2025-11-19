from datetime import datetime,timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import views as auth_views
from django.db import IntegrityError
from django.db.models import Sum
from .models import Patient, Professional, Consultation, ConsultationNote, ConsultationAttachment, Consultorio
from .models import PatientAIThread, PatientAIMessage
from django.contrib import messages
from .forms import CustomLoginForm, UsernameRecoveryForm
from .forms import ProfessionalProfileForm, ProfessionalContactForm
from .forms import AvailabilityExceptionForm
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
import io
import markdown as md
from datetime import datetime as dt, date as ddate
from .utils.availability import generate_slots
from datetime import time as dtime
from django.utils import timezone
import os
from openai import OpenAI
from django.conf import settings

# Create your views here.

@login_required
def index(request):
    return render(request, 'pages/index.html', {'segment': 'dashboard'})

class CustomLoginView(auth_views.LoginView):
    template_name = 'pages/sign-in.html'
    form_class = CustomLoginForm
    success_url = '/'

def username_recovery(request):
    if request.method == 'POST':
        form = UsernameRecoveryForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            users = User.objects.filter(email=email)
            usernames = [user.username for user in users]
            
            # For now, we'll display the usernames directly
            # In a production environment, you'd send this via email
            context = {
                'form': form,
                'usernames': usernames,
                'email': email,
                'success': True
            }
            return render(request, 'pages/username_recovery.html', context)
    else:
        form = UsernameRecoveryForm()
    
    context = {
        'form': form,
        'success': False
    }
    return render(request, 'pages/username_recovery.html', context)

@login_required
def patients(request):
    # Determine if user is a professional or admin
    is_admin = request.user.is_staff
    professional = None

    if not is_admin:
        try:
            professional = Professional.objects.get(user=request.user)
        except Professional.DoesNotExist:
            messages.error(request, "No tienes acceso a los registros de pacientes.")
            return redirect('index')

    if request.method == 'POST':
        # Process form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        date_of_birth = request.POST.get('date_of_birth')
        address = request.POST.get('address')

        # If admin, they can specify the professional
        if is_admin:
            professional_id = request.POST.get('professional')
            assigned_professional = Professional.objects.get(id=professional_id) if professional_id else None
        else:
            # If professional, assign to self
            assigned_professional = professional

        # Create new patient
        Patient.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            date_of_birth=date_of_birth,
            address=address,
            professional=assigned_professional
        )
        messages.success(request, 'Paciente Agregado con Exito!')
        return redirect('patients')

    # Get the appropriate patients list
    if is_admin:
        patients_list = Patient.objects.all().order_by('-created_at')
        all_professionals = Professional.objects.all()
    else:
        patients_list = Patient.objects.filter(professional=professional).order_by('-created_at')
        all_professionals = None

    return render(request, 'pages/patients.html', {
        'segment': 'patients',
        'patients': patients_list,
        'all_professionals': all_professionals,
        'is_admin': is_admin
    })


@login_required
def edit_patient(request, patient_id):
    # Get the patient object or return 404 if not found
    patient = get_object_or_404(Patient, id=patient_id)

    # Check if the user is an admin
    is_admin = request.user.is_superuser

    # If user is not admin, check if the patient belongs to the professional
    if not is_admin:
        professional = Professional.objects.filter(user=request.user).first()
        if not professional or patient.professional != professional:
            messages.error(request, "No tienes permiso para editar este paciente.")
            return redirect('patients')

    # Get all professionals for the dropdown
    all_professionals = Professional.objects.all()

    if request.method == 'POST':
        # Process the form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        date_of_birth = request.POST.get('date_of_birth') or None
        address = request.POST.get('address')
        color = request.POST.get('color') or ''

        # Update patient information
        patient.first_name = first_name
        patient.last_name = last_name
        patient.email = email
        patient.phone = phone
        if date_of_birth:
            patient.date_of_birth = date_of_birth
        patient.address = address
        if color:
            patient.color = color

        # Only update professional if admin and value provided
        if is_admin and request.POST.get('professional'):
            try:
                professional = Professional.objects.get(id=request.POST.get('professional'))
                patient.professional = professional
            except Professional.DoesNotExist:
                messages.error(request, "El profesional seleccionado no existe.")
                return redirect('edit_patient', patient_id=patient_id)

        patient.save()
        messages.success(request, f"Paciente {patient.first_name} {patient.last_name} actualizado correctamente.")
        return redirect('patients')

    # Create context for rendering the template
    context = {
        'patient': patient,
        'is_admin': is_admin,
        'all_professionals': all_professionals,
    }

    return render(request, 'pages/edit_patient.html', context)


@login_required
def delete_patient(request, patient_id):
    if request.method != 'POST':
        messages.error(request, "Método no permitido.")
        return redirect('patients')

    # Get the patient
    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        messages.error(request, "Paciente no encontrado.")
        return redirect('patients')

    # Check if user has access to delete this patient
    is_admin = request.user.is_staff
    if not is_admin:
        try:
            professional = Professional.objects.get(user=request.user)
            if patient.professional != professional:
                messages.error(request, "No tienes permiso para eliminar este paciente.")
                return redirect('patients')
        except Professional.DoesNotExist:
            messages.error(request, "No tienes acceso a los registros de pacientes.")
            return redirect('index')

    # Delete the patient
    patient_name = f"{patient.first_name} {patient.last_name}"
    patient.delete()
    messages.success(request, f'Paciente {patient_name} eliminado con éxito!')
    return redirect('patients')

def is_admin(user):
    return user.is_staff

@login_required
@user_passes_test(is_admin)
def professionals(request):
    if request.method == 'POST':
        # Process form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        specialty = request.POST.get('specialty')

        # User account data
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Validate that username is not already taken
        if User.objects.filter(username=username).exists():
            messages.error(request, f'El nombre de usuario "{username}" ya está en uso. Por favor, elige un nombre de usuario diferente.')
            return redirect('professionals')

        # Validate that email is not already taken (optional, but good practice)
        if email and User.objects.filter(email=email).exclude(email='').exists():
            messages.error(request, f'El correo electrónico "{email}" ya está registrado. Por favor, usa un correo diferente.')
            return redirect('professionals')

        try:
            # Create user account
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Create professional linked to user
            Professional.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                role=role,
                email=email,
                phone=phone,
                specialty=specialty
            )
            messages.success(request, 'Profesional agregado con exito!')
            return redirect('professionals')
        
        except IntegrityError as e:
            # Handle database integrity errors (duplicate username/email)
            if 'username' in str(e).lower():
                messages.error(request, f'El nombre de usuario "{username}" ya está en uso. Por favor, elige un nombre de usuario diferente.')
            elif 'email' in str(e).lower():
                messages.error(request, f'El correo electrónico "{email}" ya está registrado. Por favor, usa un correo diferente.')
            else:
                messages.error(request, 'Error de integridad de datos. Por favor, verifica la información e inténtalo de nuevo.')
            return redirect('professionals')
        
        except Exception as e:
            # If something goes wrong, delete the user if it was created
            print(f"Error creating professional: {e}")
            if 'user' in locals():
                try:
                    user.delete()
                except:
                    pass
            messages.error(request, 'Error al crear el profesional. Por favor, inténtalo de nuevo.')
            return redirect('professionals')

    # Get all professionals
    professionals_list = Professional.objects.all().order_by('-created_at')

    return render(request, 'pages/professionals.html', {
        'segment': 'profesional',
        'professionals': professionals_list
    })


@login_required
def my_patients(request):
    is_staff = request.user.is_staff
    prof = Professional.objects.filter(user=request.user).first()
    if not is_staff and not prof:
        messages.error(request, 'No tienes acceso a esta sección.')
        return redirect('index')

    patients_qs = Patient.objects.all() if is_staff else Patient.objects.filter(professional=prof)
    patients_qs = patients_qs.order_by('first_name', 'last_name')

    # Precompute aggregates
    from apps.finance.models import Payment
    data = []
    for p in patients_qs:
        consultations = Consultation.objects.filter(patient=p)
        total_paid = Payment.objects.filter(request__consultation__in=consultations).aggregate(total=Sum('amount'))['total'] or 0
        data.append({
            'patient': p,
            'consult_count': consultations.count(),
            'total_paid': total_paid,
        })

    return render(request, 'pages/my_patients.html', {
        'segment': 'my_patients',
        'patients_data': data,
        'is_admin': is_staff,
    })


@login_required
def patient_history(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    is_staff = request.user.is_staff
    prof = Professional.objects.filter(user=request.user).first()
    if not is_staff:
        if not prof or patient.professional_id != prof.id:
            messages.error(request, 'No tienes permiso para ver este paciente.')
            return redirect('my_patients')

    consultations = list(Consultation.objects.filter(patient=patient).order_by('-date','-time'))
    from apps.finance.models import Payment
    totals = Payment.objects.filter(request__consultation__in=consultations) \
        .values('request__consultation_id').annotate(total=Sum('amount'))
    by_consult = {row['request__consultation_id']: row['total'] for row in totals}
    for c in consultations:
        c.paid_amount = by_consult.get(c.id, 0)
    total_paid = sum(by_consult.values()) if by_consult else 0
    attachments = ConsultationAttachment.objects.filter(consultation__in=consultations).order_by('-uploaded_at')

    return render(request, 'pages/patient_history.html', {
        'segment': 'my_patients',
        'patient': patient,
        'consultations': consultations,
        'attachments': attachments,
        'total_paid': total_paid,
        'is_admin': is_staff,
    })


@login_required
def consult(request):
    # Determine if user is a professional or admin
    is_admin = request.user.is_staff
    professional = None

    if not is_admin:
        try:
            professional = Professional.objects.get(user=request.user)
        except Professional.DoesNotExist:
            messages.error(request, "Solo los profesionales pueden gestionar consultas.")
            return redirect(request.META.get('HTTP_REFERER', 'index'))
    else:
        # For admin users, we need to ensure they can view consultations
        # but we'll need a professional selected for any new consultations
        if Professional.objects.exists():
            professional = Professional.objects.first()  # Default for form display
        else:
            messages.warning(request, "No hay profesionales registrados para gestionar consultas.")
            return redirect('professionals')

    if request.method == 'POST':
        # Support deletion via calendar quick action (delete_consultation_id)
        delete_id = request.POST.get('delete_consultation_id')
        if delete_id and delete_id.isdigit():
            cons = Consultation.objects.filter(id=int(delete_id)).first()
            if cons:
                # Authorization: staff or owning professional
                if request.user.is_staff or cons.professional.user_id == request.user.id:
                    cons.delete()
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'ok': True, 'message': 'Consulta eliminada.'})
                    messages.success(request, 'Consulta eliminada.')
                    return redirect('consult')
                else:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'ok': False, 'message': 'Sin permiso para eliminar.'}, status=403)
                    messages.error(request, 'Sin permiso para eliminar esta consulta.')
                    return redirect('consult')
        # Process form data
        patient_id = request.POST.get('patient')
        consultory_id = request.POST.get('consultory')
        date = request.POST.get('date')
        time = request.POST.get('time')
        duration = request.POST.get('duration')
        # charge handled in Finance module; defaulted in model
        notes = request.POST.get('notes')

        # If admin, they can specify the professional
        if is_admin and request.POST.get('professional'):
            professional = Professional.objects.get(id=request.POST.get('professional'))

        # Parse and validate date is not in the past
        try:
            date_obj = dt.strptime(date, '%Y-%m-%d').date()
        except Exception:
            date_obj = None
        if not date_obj or date_obj < ddate.today():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'message': 'La fecha no puede ser anterior a hoy.'}, status=400)
            messages.error(request, 'La fecha no puede ser anterior a hoy.')
            return redirect('consult')

        # Resolve consultorio
        consultorio_obj = None
        if consultory_id:
            consultorio_obj = Consultorio.objects.filter(id=consultory_id).first()
            if not consultorio_obj:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'ok': False, 'message': 'Consultorio no válido.'}, status=400)
                messages.error(request, 'Consultorio no válido.')
                return redirect('consult')

        # Validation: prevent double booking same consultorio/date/time
        if consultorio_obj and Consultation.objects.filter(date=date_obj, time=time, consultorio_fk=consultorio_obj).exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'message': 'Ya existe una consulta en ese consultorio para la misma fecha y hora.'}, status=400)
            messages.error(request, 'Ya existe una consulta en ese consultorio para la misma fecha y hora.')
            return redirect('consult')

        patient = Patient.objects.get(id=patient_id)
        Consultation.objects.create(
            patient=patient,
            professional=professional,
            consultory=(consultorio_obj.name if consultorio_obj else ''),
            consultorio_fk=consultorio_obj,
            date=date_obj,
            time=time,
            duration=duration,
            notes=notes
        )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'message': 'Consulta programada con éxito!'})
        messages.success(request, 'Consulta programada con éxito!')
        return redirect('consult')

    # Get patients based on user role
    patients = Patient.objects.all() if is_admin else Patient.objects.filter(professional=professional)

    # Get all professionals for admin selection
    all_professionals = Professional.objects.all() if is_admin else None

    # Auto update: mark past pending as no_show
    now_dt = datetime.now()
    pending_qs = Consultation.objects.filter(date__lt=now_dt.date(), status='pending')
    # also same-day but time passed
    pending_qs_same = Consultation.objects.filter(date=now_dt.date(), time__lt=now_dt.time(), status='pending')
    pending_qs = pending_qs.union(pending_qs_same)
    for c in pending_qs:
        c.status = 'no_show'
        c.save(update_fields=['status'])

    # Get consultations with filters
    qs = Consultation.objects.all() if is_admin else Consultation.objects.filter(professional=professional)
    patient_filter = request.GET.get('patient')
    consultory_filter = request.GET.get('consultory')
    date_filter = request.GET.get('date')
    status_filter = request.GET.get('status')
    if patient_filter:
        qs = qs.filter(patient_id=patient_filter)
    if consultory_filter:
        qs = qs.filter(consultory=consultory_filter)
    if date_filter:
        qs = qs.filter(date=date_filter)
    if status_filter:
        qs = qs.filter(status=status_filter)
    consultations = qs.order_by('date', 'time')

    # Get next consultation for the professional
    next_consultation = Consultation.objects.all() if is_admin else Consultation.objects.filter(
        professional=professional,
        date__gte=datetime.now().date()
    ).order_by('date', 'time').first()

    consultorios = Consultorio.objects.filter(is_active=True)

    return render(request, 'pages/consult.html', {
        'segment': 'consult',
        'patients': patients,
        'consultations': consultations,
        'all_professionals': all_professionals,
        'is_admin': is_admin,
        'status_choices': Consultation.STATUS_CHOICES,
        'consultorios': consultorios,
        'today': ddate.today(),
    })


# Add this temporary view for the "start session" button
@login_required
def start_session(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)

    # Authorization: allow if admin or assigned professional
    is_admin = request.user.is_staff
    try:
        user_professional = Professional.objects.get(user=request.user)
    except Professional.DoesNotExist:
        user_professional = None
    if not is_admin and (not user_professional or user_professional != consultation.professional):
        messages.error(request, 'No tienes permiso para acceder a esta consulta.')
        return redirect('consult')

    # Only allow starting sessions when the consultation is pending
    if consultation.status != 'pending':
        messages.error(request, 'Solo puedes iniciar consultas con estado Pendiente.')
        return redirect('consult')

    from .forms import NoteForm, AttachmentForm, NoteEditForm, AttachmentRenameForm  # local import to avoid circular in some reload cases

    note_form = NoteForm(prefix='note')
    attachment_form = AttachmentForm(prefix='attach')
    note_edit_form = None
    attachment_rename_form = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_note':
            note_form = NoteForm(request.POST, prefix='note')
            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.consultation = consultation
                note.created_by = request.user
                note.save()
                messages.success(request, 'Nota agregada correctamente.')
                return redirect('start_session', consultation_id=consultation.id)
        elif action == 'edit_note':
            note_id = request.POST.get('note_id')
            note = get_object_or_404(ConsultationNote, id=note_id, consultation=consultation)
            if not is_admin and note.created_by != request.user:
                messages.error(request, 'No puedes editar esta nota.')
                return redirect('start_session', consultation_id=consultation.id)
            note_edit_form = NoteEditForm(request.POST, instance=note, prefix='editnote')
            if note_edit_form.is_valid():
                note_edit_form.save()
                messages.success(request, 'Nota actualizada correctamente.')
                return redirect('start_session', consultation_id=consultation.id)
        elif action == 'delete_note':
            note_id = request.POST.get('note_id')
            note = get_object_or_404(ConsultationNote, id=note_id, consultation=consultation)
            if not is_admin and note.created_by != request.user:
                messages.error(request, 'No puedes eliminar esta nota.')
                return redirect('start_session', consultation_id=consultation.id)
            note.delete()
            messages.success(request, 'Nota eliminada correctamente.')
            return redirect('start_session', consultation_id=consultation.id)
        elif action == 'add_attachment':
            attachment_form = AttachmentForm(request.POST, request.FILES, prefix='attach')
            if attachment_form.is_valid():
                attachment = attachment_form.save(commit=False)
                attachment.consultation = consultation
                attachment.uploaded_by = request.user
                attachment.save()
                messages.success(request, 'Documento agregado correctamente.')
                return redirect('start_session', consultation_id=consultation.id)
        elif action == 'edit_attachment':
            att_id = request.POST.get('attachment_id')
            att = get_object_or_404(ConsultationAttachment, id=att_id, consultation=consultation)
            if not is_admin and att.uploaded_by != request.user:
                messages.error(request, 'No puedes editar este adjunto.')
                return redirect('start_session', consultation_id=consultation.id)
            attachment_rename_form = AttachmentRenameForm(request.POST, instance=att, prefix='rename')
            if attachment_rename_form.is_valid():
                attachment_rename_form.save()
                messages.success(request, 'Adjunto actualizado correctamente.')
                return redirect('start_session', consultation_id=consultation.id)
        elif action == 'delete_attachment':
            att_id = request.POST.get('attachment_id')
            att = get_object_or_404(ConsultationAttachment, id=att_id, consultation=consultation)
            if not is_admin and att.uploaded_by != request.user:
                messages.error(request, 'No puedes eliminar este adjunto.')
                return redirect('start_session', consultation_id=consultation.id)
            # delete file then model
            storage = att.file.storage
            name = att.file.name
            att.delete()
            try:
                storage.delete(name)
            except Exception:
                pass
            messages.success(request, 'Adjunto eliminado correctamente.')
            return redirect('start_session', consultation_id=consultation.id)

    # Update status to attended when session starts if still pending
    if consultation.status == 'pending':
        consultation.status = 'attended'
        consultation.save(update_fields=['status'])

    notes = consultation.session_notes.all()
    attachments = consultation.attachments.all()

    # Group attachments by type for easier display
    grouped_attachments = {}
    for att in attachments:
        grouped_attachments.setdefault(att.file_type, []).append(att)

    return render(request, 'pages/consult_session.html', {
        'segment': 'consult',
        'consultation': consultation,
        'note_form': note_form,
        'attachment_form': attachment_form,
        'note_edit_form': note_edit_form,
        'attachment_rename_form': attachment_rename_form,
        'notes': notes,
        'grouped_attachments': grouped_attachments,
    })


@login_required
def view_session(request, consultation_id):
    """View a consultation's notes and attachments without changing its status.
    Allows adding notes/attachments, editing and deleting (same auth as start_session)."""
    consultation = get_object_or_404(Consultation, id=consultation_id)

    # Authorization: allow if admin or assigned professional
    is_admin = request.user.is_staff
    try:
        user_professional = Professional.objects.get(user=request.user)
    except Professional.DoesNotExist:
        user_professional = None
    if not is_admin and (not user_professional or user_professional != consultation.professional):
        messages.error(request, 'No tienes permiso para acceder a esta consulta.')
        return redirect('consult')

    from .forms import NoteForm, AttachmentForm, NoteEditForm, AttachmentRenameForm

    note_form = NoteForm(prefix='note')
    attachment_form = AttachmentForm(prefix='attach')
    note_edit_form = None
    attachment_rename_form = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_note':
            note_form = NoteForm(request.POST, prefix='note')
            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.consultation = consultation
                note.created_by = request.user
                note.save()
                messages.success(request, 'Nota agregada correctamente.')
                return redirect('view_session', consultation_id=consultation.id)
        elif action == 'edit_note':
            note_id = request.POST.get('note_id')
            note = get_object_or_404(ConsultationNote, id=note_id, consultation=consultation)
            if not is_admin and note.created_by != request.user:
                messages.error(request, 'No puedes editar esta nota.')
                return redirect('view_session', consultation_id=consultation.id)
            note_edit_form = NoteEditForm(request.POST, instance=note, prefix='editnote')
            if note_edit_form.is_valid():
                note_edit_form.save()
                messages.success(request, 'Nota actualizada correctamente.')
                return redirect('view_session', consultation_id=consultation.id)
        elif action == 'delete_note':
            note_id = request.POST.get('note_id')
            note = get_object_or_404(ConsultationNote, id=note_id, consultation=consultation)
            if not is_admin and note.created_by != request.user:
                messages.error(request, 'No puedes eliminar esta nota.')
                return redirect('view_session', consultation_id=consultation.id)
            note.delete()
            messages.success(request, 'Nota eliminada correctamente.')
            return redirect('view_session', consultation_id=consultation.id)
        elif action == 'add_attachment':
            attachment_form = AttachmentForm(request.POST, request.FILES, prefix='attach')
            if attachment_form.is_valid():
                attachment = attachment_form.save(commit=False)
                attachment.consultation = consultation
                attachment.uploaded_by = request.user
                attachment.save()
                messages.success(request, 'Documento agregado correctamente.')
                return redirect('view_session', consultation_id=consultation.id)
        elif action == 'edit_attachment':
            att_id = request.POST.get('attachment_id')
            att = get_object_or_404(ConsultationAttachment, id=att_id, consultation=consultation)
            if not is_admin and att.uploaded_by != request.user:
                messages.error(request, 'No puedes editar este adjunto.')
                return redirect('view_session', consultation_id=consultation.id)
            attachment_rename_form = AttachmentRenameForm(request.POST, instance=att, prefix='rename')
            if attachment_rename_form.is_valid():
                attachment_rename_form.save()
                messages.success(request, 'Adjunto actualizado correctamente.')
                return redirect('view_session', consultation_id=consultation.id)
        elif action == 'delete_attachment':
            att_id = request.POST.get('attachment_id')
            att = get_object_or_404(ConsultationAttachment, id=att_id, consultation=consultation)
            if not is_admin and att.uploaded_by != request.user:
                messages.error(request, 'No puedes eliminar este adjunto.')
                return redirect('view_session', consultation_id=consultation.id)
            storage = att.file.storage
            name = att.file.name
            att.delete()
            try:
                storage.delete(name)
            except Exception:
                pass
            messages.success(request, 'Adjunto eliminado correctamente.')
            return redirect('view_session', consultation_id=consultation.id)

    # DO NOT change the consultation status in view mode

    notes = consultation.session_notes.all()
    attachments = consultation.attachments.all()

    grouped_attachments = {}
    for att in attachments:
        grouped_attachments.setdefault(att.file_type, []).append(att)

    return render(request, 'pages/consult_session.html', {
        'segment': 'consult',
        'consultation': consultation,
        'note_form': note_form,
        'attachment_form': attachment_form,
        'note_edit_form': note_edit_form,
        'attachment_rename_form': attachment_rename_form,
        'notes': notes,
        'grouped_attachments': grouped_attachments,
        'view_mode': True,
    })


@login_required
def end_session(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)

    # Authorization: allow if admin or assigned professional
    is_admin = request.user.is_staff
    user_professional = Professional.objects.filter(user=request.user).first()
    if not is_admin and (not user_professional or user_professional != consultation.professional):
        messages.error(request, 'No tienes permiso para terminar esta consulta.')
        return redirect('consult')

    consultation.status = 'completed'
    consultation.save(update_fields=['status'])
    messages.success(request, 'Consulta marcada como Terminada.')
    return redirect('start_session', consultation_id=consultation.id)


@login_required
def profile(request):
    # Logged in user may or may not be a professional
    professional = None
    try:
        professional = Professional.objects.get(user=request.user)
    except Professional.DoesNotExist:
        professional = None

    # Forms
    profile_form = ProfessionalProfileForm(instance=professional) if professional else None
    contact_form = ProfessionalContactForm()
    exception_form = AvailabilityExceptionForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_profile' and professional:
            profile_form = ProfessionalProfileForm(request.POST, request.FILES, instance=professional)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Perfil actualizado correctamente.')
                return redirect('profile')
        elif action == 'add_contact' and professional:
            contact_form = ProfessionalContactForm(request.POST)
            contact_form.initial['professional'] = professional
            if contact_form.is_valid():
                pc = contact_form.save(commit=False)
                pc.professional = professional
                pc.save()
                messages.success(request, 'Contacto agregado.')
                return redirect('profile')
        elif action == 'delete_contact' and professional:
            cid = request.POST.get('contact_id')
            from .models import ProfessionalContact
            contact = get_object_or_404(ProfessionalContact, id=cid, professional=professional)
            contact.delete()
            messages.success(request, 'Contacto eliminado.')
            return redirect('profile')
        elif action == 'update_availability' and professional:
            # Expect fields like availability-<weekday>-closed, availability-<weekday>-start, availability-<weekday>-end
            for wd in range(7):
                key = f'availability-{wd}-closed'
                is_closed = request.POST.get(key) == 'on'
                start_raw = request.POST.get(f'availability-{wd}-start')
                end_raw = request.POST.get(f'availability-{wd}-end')
                avail, _ = professional.weekly_availability.get_or_create(weekday=wd)
                avail.is_closed = is_closed
                if not is_closed:
                    try:
                        start_parts = [int(x) for x in (start_raw or '09:00').split(':')]
                        end_parts = [int(x) for x in (end_raw or '17:00').split(':')]
                        avail.start_time = dtime(start_parts[0], start_parts[1])
                        avail.end_time = dtime(end_parts[0], end_parts[1])
                    except Exception:
                        pass
                else:
                    avail.start_time = None
                    avail.end_time = None
                avail.save()
            messages.success(request, 'Disponibilidad semanal actualizada.')
            return redirect('profile')
        elif action == 'add_exception' and professional:
            exception_form = AvailabilityExceptionForm(request.POST)
            if exception_form.is_valid():
                try:
                    ex = exception_form.save(commit=False)
                    ex.professional = professional
                    ex.save()
                    messages.success(request, 'Excepción agregada.')
                    return redirect('profile')
                except IntegrityError:
                    messages.error(request, 'Ya existe una excepción para esa fecha.')
            else:
                # Surface validation errors in messages for clarity
                for field, errs in exception_form.errors.items():
                    for e in errs:
                        messages.error(request, f"Error en {field or 'formulario'}: {e}")
        elif action == 'delete_exception' and professional:
            ex_id = request.POST.get('exception_id')
            from .models import AvailabilityException
            ex = get_object_or_404(AvailabilityException, id=ex_id, professional=professional)
            ex.delete()
            messages.success(request, 'Excepción eliminada.')
            return redirect('profile')

    contacts = professional.contacts.all() if professional else []
    availability = professional.weekly_availability.all() if professional else []
    exceptions = professional.availability_exceptions.filter(date__gte=datetime.now().date()).order_by('date') if professional else []

    return render(request, 'pages/profile.html', {
        'segment': 'profile',
        'professional': professional,
        'profile_form': profile_form,
        'contact_form': contact_form,
        'contacts': contacts,
        'availability': availability,
        'exception_form': exception_form,
        'exceptions': exceptions,
    })


@login_required
def available_slots_api(request):
    # Params: date (YYYY-MM-DD), duration (int minutes), professional_id(optional for admin)
    date_str = request.GET.get('date')
    duration = int(request.GET.get('duration', '60'))
    prof_id = request.GET.get('professional_id')
    if not date_str:
        return JsonResponse({'error': 'Missing date'}, status=400)
    try:
        date_obj = dt.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    # Determine professional
    if request.user.is_staff:
        if not prof_id:
            # For admin, require explicit professional selection; return empty list (no error)
            return JsonResponse({'slots': []})
        professional = get_object_or_404(Professional, id=prof_id)
    else:
        try:
            professional = Professional.objects.get(user=request.user)
        except Professional.DoesNotExist:
            return JsonResponse({'error': 'Professional not found'}, status=404)

    # Always step in 30 minute increments regardless of duration
    slots = generate_slots(professional, date_obj, duration_minutes=duration, step_minutes=30)
    return JsonResponse({'slots': slots})


def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'No tienes permiso para este apartado')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@staff_required
def config_consultorios(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            name = request.POST.get('name')
            address = request.POST.get('address')
            if not name:
                messages.error(request, 'Nombre requerido')
                return redirect('config_consultorios')
            if Consultorio.objects.filter(name=name).exists():
                messages.error(request, 'Ya existe un consultorio con ese nombre')
                return redirect('config_consultorios')
            Consultorio.objects.create(name=name, address=address or '')
            messages.success(request, 'Consultorio agregado')
            return redirect('config_consultorios')
        elif action == 'delete':
            cid = request.POST.get('consultorio_id')
            consultorio = Consultorio.objects.filter(id=cid).first()
            if consultorio:
                consultorio.delete()
                messages.success(request, 'Consultorio eliminado')
            else:
                messages.error(request, 'Consultorio no encontrado')
            return redirect('config_consultorios')
        elif action == 'toggle':
            cid = request.POST.get('consultorio_id')
            consultorio = Consultorio.objects.filter(id=cid).first()
            if consultorio:
                consultorio.is_active = not consultorio.is_active
                consultorio.save()
                messages.success(request, 'Estado actualizado')
            else:
                messages.error(request, 'Consultorio no encontrado')
            return redirect('config_consultorios')

    consultorios = Consultorio.objects.all().order_by('name')
    return render(request, 'pages/config_consultorios.html', {
        'segment': 'config_consultorios',
        'consultorios': consultorios,
    })


@login_required
def consult_table(request):
    # Same filters as consult view, but only return the table fragment
    is_admin = request.user.is_staff
    if is_admin:
        qs = Consultation.objects.all()
    else:
        prof = Professional.objects.filter(user=request.user).first()
        qs = Consultation.objects.filter(professional=prof) if prof else Consultation.objects.none()

    patient_filter = request.GET.get('patient')
    consultory_filter = request.GET.get('consultory')
    date_filter = request.GET.get('date')
    status_filter = request.GET.get('status')
    if patient_filter:
        qs = qs.filter(patient_id=patient_filter)
    if consultory_filter:
        if str(consultory_filter).isdigit():
            qs = qs.filter(consultorio_fk_id=int(consultory_filter))
        else:
            qs = qs.filter(consultory=consultory_filter)
    if date_filter:
        qs = qs.filter(date=date_filter)
    if status_filter:
        qs = qs.filter(status=status_filter)
    consultations = list(qs.order_by('date', 'time'))
    # Attach paid_amount from finance payments
    try:
        from apps.finance.models import Payment
        totals = Payment.objects.filter(request__consultation__in=consultations) \
            .values('request__consultation_id').annotate(total=Sum('amount'))
        by_consult = {row['request__consultation_id']: row['total'] for row in totals}
        for c in consultations:
            c.paid_amount = by_consult.get(c.id, 0)
    except Exception:
        for c in consultations:
            c.paid_amount = 0

    return render(request, 'pages/_consult_table.html', {
        'consultations': consultations,
    })


@login_required
def consultorios_calendar(request):
    # Params
    date_str = request.GET.get('date')
    mode = request.GET.get('mode', 'day')
    try:
        target_date = dt.strptime(date_str, '%Y-%m-%d').date() if date_str else ddate.today()
    except Exception:
        target_date = ddate.today()

    consultorio_id = request.GET.get('consultorio')
    if consultorio_id and str(consultorio_id).isdigit():
        consultorios = list(Consultorio.objects.filter(id=int(consultorio_id)))
    else:
        consultorios = list(Consultorio.objects.filter(is_active=True))

    from datetime import time as dtime
    start_time = dtime(7, 0); end_time = dtime(21, 0); step_minutes = 30
    total_slots = int(((end_time.hour*60 + end_time.minute) - (start_time.hour*60 + start_time.minute)) / step_minutes)
    times = []
    base_minutes = start_time.hour*60 + start_time.minute
    for i in range(total_slots):
        minutes = base_minutes + i*step_minutes
        h = minutes // 60; m = minutes % 60
        times.append(f"{h:02d}:{m:02d}")

    day_rows = []
    week_days = []
    week_grid = []
    month_weeks = []
    month_map = {}

    if mode == 'day':
        columns_rows = {}
        for c in consultorios:
            rows = [None] * total_slots
            qs = Consultation.objects.filter(date=target_date).filter(consultorio_fk=c)
            if not qs.exists():
                qs = Consultation.objects.filter(date=target_date, consultory=c.name)
            for cons in qs.order_by('time'):
                idx = int(((cons.time.hour*60 + cons.time.minute) - base_minutes) / step_minutes)
                if idx < 0 or idx >= total_slots:
                    continue
                span = cons.duration or 60
                span = int((span + step_minutes - 1) / step_minutes)
                span = min(span, max(1, total_slots - idx))
                if rows[idx] is None:
                    rows[idx] = {'type': 'start', 'consult': cons, 'rowspan': span}
                    for k in range(1, span):
                        if idx + k < total_slots:
                            rows[idx + k] = {'type': 'skip'}
            columns_rows[c.id] = rows
        for i, t in enumerate(times):
            row_cells = []
            for c in consultorios:
                cell = columns_rows[c.id][i]
                row_cells.append(cell if cell is not None else {'type': 'empty'})
            day_rows.append({'time': t, 'cells': row_cells})

    elif mode == 'week':
        start_week = target_date - timedelta(days=target_date.weekday())
        week_days = [start_week + timedelta(days=d) for d in range(7)]
        selected = None
        if consultorio_id and str(consultorio_id).isdigit():
            selected = Consultorio.objects.filter(id=int(consultorio_id)).first()
        if not selected and consultorios:
            selected = consultorios[0]
        for t in times:
            row_cells = []
            hour, minute = [int(x) for x in t.split(':')]
            for day in week_days:
                qs = Consultation.objects.filter(date=day)
                if selected:
                    qs = qs.filter(consultorio_fk=selected) | qs.filter(consultory=selected.name)
                match = qs.filter(time__hour=hour, time__minute=minute).order_by('time').first()
                if match:
                    row_cells.append({'type': 'start', 'consult': match, 'rowspan': 1})
                else:
                    row_cells.append({'type': 'empty'})
            week_grid.append({'time': t, 'cells': row_cells})

    elif mode == 'month':
        first_day = target_date.replace(day=1)
        start_cal = first_day - timedelta(days=first_day.weekday())
        for w in range(6):
            week_days_row = [start_cal + timedelta(days=w*7 + d) for d in range(7)]
            month_weeks.append(week_days_row)
        end_cal = month_weeks[-1][-1]
        qs_month = Consultation.objects.filter(date__gte=month_weeks[0][0], date__lte=end_cal)
        if consultorio_id and str(consultorio_id).isdigit():
            qs_month = qs_month.filter(consultorio_fk_id=int(consultorio_id))
        for cons in qs_month.select_related('patient'):
            month_map.setdefault(cons.date, []).append(cons)

    # Restrict for professionals (non-staff)
    if not request.user.is_staff:
        prof = Professional.objects.filter(user=request.user).first()
        pid = prof.id if prof else None
        if mode == 'day':
            for r in day_rows:
                for cell in r['cells']:
                    if cell.get('type') == 'start' and cell['consult'].professional_id != pid:
                        cell.clear(); cell['type'] = 'empty'
        elif mode == 'week':
            for r in week_grid:
                for cell in r['cells']:
                    if cell.get('type') == 'start' and cell['consult'].professional_id != pid:
                        cell.clear(); cell['type'] = 'empty'
        elif mode == 'month':
            for d, items in list(month_map.items()):
                month_map[d] = [c for c in items if c.professional_id == pid]
                if not month_map[d]:
                    month_map.pop(d, None)

    context = {
        'segment': 'consultorios_calendar',
        'consultorios': consultorios,
        'times': times,
        'day_rows': day_rows,
        'week_days': week_days,
        'week_grid': week_grid,
        'month_weeks': month_weeks,
        'month_map': month_map,
        'target_date': target_date,
        'selected_consultorio_id': int(consultorio_id) if consultorio_id and str(consultorio_id).isdigit() else '',
        'mode': mode,
    }
    return render(request, 'pages/consultorios_calendar.html', context)

@login_required
def consultation_delete_api(request, consultation_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Método no permitido'}, status=405)
    cons = Consultation.objects.filter(id=consultation_id).first()
    if not cons:
        return JsonResponse({'ok': False, 'message': 'Consulta no encontrada'}, status=404)
    if not (request.user.is_staff or cons.professional.user_id == request.user.id):
        return JsonResponse({'ok': False, 'message': 'Sin permiso'}, status=403)
    cons.delete()
    return JsonResponse({'ok': True, 'message': 'Consulta eliminada'})

@login_required
def patient_color_update_api(request, patient_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Método no permitido'}, status=405)
    pat = Patient.objects.filter(id=patient_id).first()
    if not pat:
        return JsonResponse({'ok': False, 'message': 'Paciente no encontrado'}, status=404)
    if not (request.user.is_staff or (pat.professional and pat.professional.user_id == request.user.id)):
        return JsonResponse({'ok': False, 'message': 'Sin permiso'}, status=403)
    color = request.POST.get('color', '').strip()
    if not color.startswith('#') or len(color) not in (4,7):
        return JsonResponse({'ok': False, 'message': 'Color inválido'}, status=400)
    pat.color = color
    pat.save(update_fields=['color'])
    return JsonResponse({'ok': True, 'message': 'Color actualizado', 'color': color})

def _fallback_color(pid: int):
    palette = ['#D4E157','#4FC3F7','#FFB74D','#BA68C8','#81C784','#64B5F6','#E57373','#FFD54F','#4DB6AC','#A1887F']
    return palette[pid % len(palette)]

@login_required
def calendar_events_api(request):
    """Return consultations as FullCalendar events.
    Optional query params: consultorio (id), start, end (ISO dates)
    """
    consultorio_id = request.GET.get('consultorio')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    exclude_str = request.GET.get('exclude')  # comma separated statuses to hide
    qs = Consultation.objects.all().select_related('patient','professional','consultorio_fk')
    if consultorio_id and consultorio_id.isdigit():
        qs = qs.filter(consultorio_fk_id=int(consultorio_id)) | qs.filter(consultory=Consultorio.objects.filter(id=int(consultorio_id)).values_list('name', flat=True).first())
    # Date range filtering
    if start_str and end_str:
        try:
            start_date = dt.strptime(start_str[:10], '%Y-%m-%d').date()
            end_date = dt.strptime(end_str[:10], '%Y-%m-%d').date()
            qs = qs.filter(date__gte=start_date, date__lte=end_date)
        except Exception:
            pass
    # Status exclusion
    if exclude_str:
        to_exclude = [s.strip() for s in exclude_str.split(',') if s.strip()]
        if to_exclude:
            qs = qs.exclude(status__in=to_exclude)
    # Restrict for non-staff professionals
    if not request.user.is_staff:
        prof = Professional.objects.filter(user=request.user).first()
        if prof:
            qs = qs.filter(professional=prof)
        else:
            qs = qs.none()

    events = []
    for c in qs:
        if not c.time:
            continue
        start_dt = dt.combine(c.date, c.time)
        end_dt = start_dt + timedelta(minutes=c.duration or 60)
        patient = c.patient
        color = patient.color if patient and patient.color else _fallback_color(patient.id if patient else c.id)
        professional = c.professional
        consultorio_name = c.consultorio_fk.name if c.consultorio_fk else c.consultory
        patient_name = ((patient.first_name + ' ' + patient.last_name).strip()) if patient else 'Consulta'
        professional_name = ((professional.first_name + ' ' + professional.last_name).strip()) if professional else ''
        events.append({
            'id': c.id,
            'title': patient_name,
            'start': start_dt.isoformat(),
            'end': end_dt.isoformat(),
            'extendedProps': {
                'status': c.status,
                'statusDisplay': c.get_status_display() if hasattr(c, 'get_status_display') else c.status,
                'consultorio': consultorio_name,
                'consultorioId': c.consultorio_fk_id if c.consultorio_fk_id else None,
                'patientId': patient.id if patient else None,
                'patientName': patient_name,
                'professionalId': professional.id if professional else None,
                'professionalName': professional_name,
                'duration': c.duration,
                'charge': c.charge,
                'notes': c.notes or '',
            },
            'backgroundColor': color,
            'borderColor': color,
        })
    return JsonResponse(events, safe=False)

@login_required
def consultation_time_update_api(request, consultation_id):
    """Update start/end (thus date/time & duration) of a consultation for drag/resize operations."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Método no permitido'}, status=405)
    cons = Consultation.objects.select_related('professional','consultorio_fk','patient').filter(id=consultation_id).first()
    if not cons:
        return JsonResponse({'ok': False, 'message': 'Consulta no encontrada'}, status=404)
    if not (request.user.is_staff or (cons.professional and cons.professional.user_id == request.user.id)):
        return JsonResponse({'ok': False, 'message': 'Sin permiso'}, status=403)
    start_iso = request.POST.get('start')
    end_iso = request.POST.get('end')
    try:
        new_start = dt.fromisoformat(start_iso)
        new_end = dt.fromisoformat(end_iso)
    except Exception:
        return JsonResponse({'ok': False, 'message': 'Formato de fecha inválido'}, status=400)
    if new_end <= new_start:
        return JsonResponse({'ok': False, 'message': 'Fin debe ser posterior al inicio'}, status=400)
    # Prevent reprogramming to days before today (date-only check)
    if new_start.date() < ddate.today():
        return JsonResponse({'ok': False, 'message': 'No se puede reprogramar a días anteriores a hoy'}, status=400)
    new_date = new_start.date()
    new_time = new_start.time().replace(second=0, microsecond=0)
    new_duration = int((new_end - new_start).total_seconds() // 60)
    # Conflict detection within same consultorio
    base_qs = Consultation.objects.filter(date=new_date)
    if cons.consultorio_fk:
        base_qs = base_qs.filter(consultorio_fk=cons.consultorio_fk) | base_qs.filter(consultory=cons.consultorio_fk.name)
    elif cons.consultory:
        base_qs = base_qs.filter(consultory=cons.consultory)
    conflicts = []
    new_start_dt = dt.combine(new_date, new_time)
    new_end_dt = new_start_dt + timedelta(minutes=new_duration)
    for other in base_qs.exclude(id=cons.id):
        o_start_dt = dt.combine(other.date, other.time)
        o_end_dt = o_start_dt + timedelta(minutes=other.duration or 60)
        if new_start_dt < o_end_dt and o_start_dt < new_end_dt:
            conflicts.append(other.id)
            break
    if conflicts:
        return JsonResponse({'ok': False, 'message': 'Conflicto con otra consulta'}, status=409)
    cons.date = new_date
    cons.time = new_time
    cons.duration = new_duration
    cons.status = 'pending'
    cons.save(update_fields=['date','time','duration','status'])
    return JsonResponse({'ok': True, 'message': 'Actualizado', 'id': cons.id, 'date': str(cons.date), 'time': cons.time.strftime('%H:%M'), 'duration': cons.duration, 'status': cons.status})

@login_required
def consultation_cancel_api(request, consultation_id):
    """Cancel a consultation or reschedule it to another date/time.
    POST params:
      - mode: 'cancel' (default) or 'reschedule'
      - date (YYYY-MM-DD) and time (HH:MM) when mode == 'reschedule'
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Método no permitido'}, status=405)
    cons = Consultation.objects.select_related('professional','consultorio_fk','patient').filter(id=consultation_id).first()
    if not cons:
        return JsonResponse({'ok': False, 'message': 'Consulta no encontrada'}, status=404)
    if not (request.user.is_staff or (cons.professional and cons.professional.user_id == request.user.id)):
        return JsonResponse({'ok': False, 'message': 'Sin permiso'}, status=403)

    mode = (request.POST.get('mode') or 'cancel').strip()
    if mode == 'cancel':
        cons.status = 'cancelled'
        cons.save(update_fields=['status'])
        return JsonResponse({'ok': True, 'message': 'Consulta cancelada'})
    elif mode == 'reschedule':
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        if not date_str or not time_str:
            return JsonResponse({'ok': False, 'message': 'Fecha y hora requeridas'}, status=400)
        try:
            new_date = dt.strptime(date_str, '%Y-%m-%d').date()
            hh, mm = [int(x) for x in time_str.split(':')]
            new_time = dtime(hh, mm)
        except Exception:
            return JsonResponse({'ok': False, 'message': 'Formato de fecha/hora inválido'}, status=400)
        # Validate date not before today (date-only rule)
        if new_date < ddate.today():
            return JsonResponse({'ok': False, 'message': 'No se puede reprogramar a días anteriores a hoy'}, status=400)
        new_start_dt = dt.combine(new_date, new_time)
        tz = timezone.get_current_timezone()
        if timezone.is_naive(new_start_dt):
            new_start_dt = timezone.make_aware(new_start_dt, tz)
        new_end_dt = new_start_dt + timedelta(minutes=cons.duration or 60)
        # Conflict detection in same consultorio
        base_qs = Consultation.objects.filter(date=new_date)
        if cons.consultorio_fk:
            base_qs = base_qs.filter(consultorio_fk=cons.consultorio_fk) | base_qs.filter(consultory=cons.consultorio_fk.name)
        elif cons.consultory:
            base_qs = base_qs.filter(consultory=cons.consultory)
        conflict = False
        for other in base_qs.exclude(id=cons.id):
            o_start = dt.combine(other.date, other.time)
            if timezone.is_naive(o_start):
                o_start = timezone.make_aware(o_start, tz)
            o_end = o_start + timedelta(minutes=other.duration or 60)
            if new_start_dt < o_end and o_start < new_end_dt:
                conflict = True
                break
        if conflict:
            return JsonResponse({'ok': False, 'message': 'Conflicto con otra consulta'}, status=409)
        cons.date = new_date
        cons.time = new_time
        cons.status = 'pending'
        cons.save(update_fields=['date','time','status'])
        return JsonResponse({'ok': True, 'message': 'Consulta reprogramada', 'date': str(cons.date), 'time': cons.time.strftime('%H:%M'), 'status': cons.status})
    else:
        return JsonResponse({'ok': False, 'message': 'Modo inválido'}, status=400)


def _get_professional(user):
    return Professional.objects.filter(user=user).first()


def _build_patient_context(professional: Professional, patient: Patient) -> str:
    cons_qs = Consultation.objects.filter(professional=professional, patient=patient).order_by('date', 'time')
    note_qs = ConsultationNote.objects.filter(consultation__in=cons_qs).select_related('consultation')
    att_qs = ConsultationAttachment.objects.filter(consultation__in=cons_qs).select_related('consultation')
    parts = []
    parts.append(f"Paciente: {patient.first_name} {patient.last_name}\n")
    parts.append(f"Total de consultas: {cons_qs.count()}\n")
    for c in cons_qs:
        parts.append(f"- Consulta: {c.date} {c.time}, estado={c.get_status_display()}, duración={c.duration} min\n")
        notes = [n for n in note_qs if n.consultation_id == c.id]
        if notes:
            parts.append("  Notas:\n")
            for n in notes:
                title = (n.title or '').strip()
                tshow = f"{title}: " if title else ''
                parts.append(f"   • {tshow}{(n.content or '').strip()[:500]}\n")
        atts = [a for a in att_qs if a.consultation_id == c.id]
        if atts:
            parts.append("  Adjuntos:\n")
            for a in atts:
                parts.append(f"   • {a.get_file_type_display()} - {a.display_name or a.file.name}\n")
    return ''.join(parts)


def _openai_client():
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def _ensure_openai_file(client: OpenAI, attachment: ConsultationAttachment) -> str:
    """Upload file to OpenAI Files API if missing, return file_id."""
    if attachment.openai_file_id:
        return attachment.openai_file_id
    try:
        # Use absolute path from FileField
        local_path = attachment.file.path
        with open(local_path, 'rb') as f:
            fobj = client.files.create(file=f, purpose='user_data')
        file_id = getattr(fobj, 'id', None) or (fobj.get('id') if isinstance(fobj, dict) else None)
        if file_id:
            attachment.openai_file_id = file_id
            attachment.save(update_fields=['openai_file_id'])
        return file_id
    except Exception:
        return None


def _collect_attachment_file_ids(client: OpenAI, professional: Professional, patient: Patient):
    """Return list of OpenAI file_ids for this patient's attachments, uploading if needed."""
    file_ids = []
    cons_qs = Consultation.objects.filter(professional=professional, patient=patient)
    atts = ConsultationAttachment.objects.filter(consultation__in=cons_qs)
    for att in atts:
        fid = _ensure_openai_file(client, att)
        if fid:
            file_ids.append(fid)
    return file_ids


@login_required
def report_sessions_reupload(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)
    prof = _get_professional(request.user)
    if not (request.user.is_staff or prof):
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)
    patient_id = request.POST.get('patient')
    if not patient_id:
        return JsonResponse({'ok': False, 'error': 'Falta parámetro patient'}, status=400)
    patient = Patient.objects.filter(id=patient_id).first()
    if not patient:
        return JsonResponse({'ok': False, 'error': 'Paciente no encontrado'}, status=404)
    # Access control: staff or assigned professional
    if not request.user.is_staff:
        if not patient.professional_id or patient.professional_id != prof.id:
            return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)

    client = _openai_client()
    if not client:
        return JsonResponse({'ok': False, 'error': 'Falta OPENAI_API_KEY'}, status=400)

    cons_qs = Consultation.objects.filter(patient=patient)
    if not request.user.is_staff and prof:
        cons_qs = cons_qs.filter(professional=prof)
    atts = list(ConsultationAttachment.objects.filter(consultation__in=cons_qs))
    uploaded = 0
    errors = []
    for att in atts:
        try:
            # Force re-upload: ignore existing id, upload anew and overwrite
            local_path = att.file.path
            with open(local_path, 'rb') as f:
                fobj = client.files.create(file=f, purpose='user_data')
            file_id = getattr(fobj, 'id', None) or (fobj.get('id') if isinstance(fobj, dict) else None)
            if file_id:
                att.openai_file_id = file_id
                att.save(update_fields=['openai_file_id'])
                uploaded += 1
        except Exception as e:
            errors.append(f"{att.id}: {e}")
    return JsonResponse({'ok': True, 'uploaded': uploaded, 'total': len(atts), 'errors': errors})


def _ai_summary_prompt(context: str) -> list:
    system = (
        "Eres un asistente clínico para profesionales de salud mental. "
        "Usa el contexto del paciente provisto para: "
        "1) Resumen detallado de la historia clínica (en viñetas si ayuda). "
        "2) Resumen breve en viñetas de la última sesión y dónde quedó. "
        "3) Recomendaciones prácticas y cautelas para el profesional en la próxima sesión. "
        "Responde en español, claro y estructurado. Si falta información, decláralo."
    )
    user = (
        "Contexto del paciente (consultas, notas, adjuntos):\n\n" + context + "\n\n" +
        "Genera: (A) Historia, (B) Última sesión, (C) Recomendaciones."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


@login_required
def report_sessions(request):
    # Professionals only (or staff)
    prof = _get_professional(request.user)
    if not (request.user.is_staff or prof):
        messages.error(request, 'No autorizado.')
        return redirect('index')

    patient_id = request.GET.get('patient') or request.POST.get('patient')
    selected_patient = Patient.objects.filter(id=patient_id).first() if patient_id else None
    thread = None
    generated = None
    error = None
    info = None

    if request.method == 'POST' and selected_patient:
        # Resolve professional for thread: current professional or patient's assigned professional (for staff)
        thread_prof = prof or selected_patient.professional
        if not thread_prof:
            error = 'El paciente no está asignado a un profesional. Asígnalo primero para generar el reporte.'
        else:
            # Create or reuse thread and generate initial summary
            thread, created = PatientAIThread.objects.get_or_create(
                professional=thread_prof,
                patient=selected_patient,
            )
            # Default model to gpt-5 if empty/legacy
            if created or not thread.model or thread.model == 'gpt-4o-mini':
                thread.model = 'gpt-5'
                thread.save(update_fields=['model'])
            # Compute current stats and decide whether to rebuild context
            cons_qs = Consultation.objects.filter(professional=thread_prof, patient=selected_patient)
            cur_consult_count = cons_qs.count()
            cur_last_consult = cons_qs.order_by('-date', '-time', '-id').first()
            cur_note_count = ConsultationNote.objects.filter(consultation__in=cons_qs).count()
            cur_att_count = ConsultationAttachment.objects.filter(consultation__in=cons_qs).count()

            force = (request.POST.get('force') == '1')
            unchanged = (
                hasattr(thread, 'context_consult_count') and
                thread.context_consult_count == cur_consult_count and
                thread.context_note_count == cur_note_count and
                thread.context_attachment_count == cur_att_count and
                ((getattr(thread, 'context_last_consultation_id', None) or None) == (cur_last_consult.id if cur_last_consult else None))
            )
            if not force and unchanged:
                info = 'No hay cambios desde el último resumen. Se mantiene el anterior.'
            else:
                # Build context and persist tracking fields
                context_text = _build_patient_context(thread_prof, selected_patient)
                thread.context = context_text
                if hasattr(thread, 'context_consult_count'):
                    thread.context_consult_count = cur_consult_count
                    thread.context_note_count = cur_note_count
                    thread.context_attachment_count = cur_att_count
                    thread.context_last_consultation = cur_last_consult
                    thread.save(update_fields=['context', 'context_consult_count', 'context_note_count', 'context_attachment_count', 'context_last_consultation', 'updated_at'])
                else:
                    thread.save(update_fields=['context', 'updated_at'])

            client = _openai_client()
            if not client:
                error = 'Configura OPENAI_API_KEY para generar el resumen.'
            else:
                try:
                    # Only call if we actually built/updated context this POST
                    if not info:
                        file_ids = _collect_attachment_file_ids(client, thread_prof, selected_patient)
                        input_parts = []
                        for fid in file_ids:
                            input_parts.append({"type": "input_file", "file_id": fid})
                        system_text = (
                            "Eres un asistente clínico para profesionales de salud mental. "
                            "Usa el contexto del paciente y los archivos adjuntos para: "
                            "1) Historia clínica detallada. 2) Breve resumen de la última sesión. "
                            "3) Recomendaciones prácticas para la próxima sesión. Responde en español."
                        )
                        input_parts.append({"type": "input_text", "text": system_text + "\n\n" + (thread.context or '')})
                        resp = client.responses.create(
                            model=thread.model or 'gpt-5',
                            input=[{"role": "user", "content": input_parts}],
                        )
                        content = getattr(resp, 'output_text', None) or ''
                        if not content and hasattr(resp, 'output'):
                            try:
                                content = ' '.join([o.get('content', [{}])[0].get('text', {}).get('value', '') for o in resp.output])
                            except Exception:
                                content = ''
                        if content:
                            PatientAIMessage.objects.create(thread=thread, role='assistant', content=content or '', is_summary=True)
                            generated = content
                except Exception as e:
                    error = f'Error al invocar OpenAI: {e}'

    patients = Patient.objects.filter(professional=prof) if prof else Patient.objects.all()
    # Load thread and last messages if exists (respect staff fallback to patient's professional)
    if selected_patient and not thread:
        view_prof = prof or selected_patient.professional
        if view_prof:
            thread = PatientAIThread.objects.filter(professional=view_prof, patient=selected_patient).first()
    messages_qs = thread.messages.all() if thread else []

    return render(request, 'pages/report_sessions.html', {
        'segment': 'report_sessions',
        'patients': patients,
        'selected_patient': selected_patient,
        'thread': thread,
        'messages': messages_qs,
        'generated': generated,
        'error': error,
        'info': info,
    })


@login_required
def report_sessions_pdf(request):
    # Resolve professional and thread/patient
    prof = _get_professional(request.user)
    if not (request.user.is_staff or prof):
        messages.error(request, 'No autorizado.')
        return redirect('index')
    thread_id = request.GET.get('thread') or request.POST.get('thread')
    patient_id = request.GET.get('patient') or request.POST.get('patient')
    thread = None
    if thread_id:
        thread = PatientAIThread.objects.select_related('professional', 'patient').filter(id=thread_id).first()
        if not thread:
            messages.error(request, 'Hilo no encontrado')
            return redirect('report_sessions')
        if not (request.user.is_staff or (prof and prof.id == thread.professional_id)):
            messages.error(request, 'No autorizado')
            return redirect('report_sessions')
    elif patient_id:
        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            messages.error(request, 'Paciente no encontrado')
            return redirect('report_sessions')
        view_prof = prof or patient.professional
        if not view_prof:
            messages.error(request, 'No autorizado')
            return redirect('report_sessions')
        thread = PatientAIThread.objects.select_related('professional', 'patient').filter(professional=view_prof, patient=patient).first()
        if not thread:
            messages.error(request, 'No hay resumen para este paciente aún')
            return redirect('report_sessions')
    else:
        messages.error(request, 'Parámetros inválidos')
        return redirect('report_sessions')

    # Pick latest assistant message marked as a formal summary; fallback to any assistant
    last_summary = thread.messages.filter(role='assistant', is_summary=True).order_by('-created_at').first()
    if not last_summary:
        last_summary = thread.messages.filter(role='assistant').order_by('-created_at').first()
    content_md = last_summary.content if last_summary else 'No hay resumen disponible.'
    content_html = md.markdown(content_md)

    html = render_to_string('pages/report_sessions_pdf.html', {
        'patient': thread.patient,
        'professional': thread.professional,
        'content_html': content_html,
        'thread': thread,
    })
    try:
        from xhtml2pdf import pisa
        result = io.BytesIO()
        pisa.CreatePDF(src=html, dest=result, encoding='utf-8')
        pdf_data = result.getvalue()
        filename = f"Resumen_{thread.patient.first_name}_{thread.patient.last_name}.pdf"
        resp = HttpResponse(pdf_data, content_type='application/pdf')
        resp['Content-Disposition'] = f'attachment; filename="{filename}"'
        return resp
    except Exception:
        # Fallback: return HTML if PDF generation fails
        return HttpResponse(html)


@login_required
def report_sessions_chat(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)
    prof = _get_professional(request.user)
    thread_id = request.POST.get('thread_id')
    question = (request.POST.get('message') or '').strip()
    if not thread_id or not question:
        return JsonResponse({'ok': False, 'error': 'Faltan parámetros'}, status=400)
    thread = PatientAIThread.objects.select_related('professional', 'patient').filter(id=thread_id).first()
    if not thread:
        return JsonResponse({'ok': False, 'error': 'Hilo no encontrado'}, status=404)
    if not (request.user.is_staff or (prof and prof.id == thread.professional_id)):
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)

    client = _openai_client()
    if not client:
        return JsonResponse({'ok': False, 'error': 'Falta OPENAI_API_KEY'}, status=400)

    # Prepare input for Responses API: include files, context, short history, and the new question
    history = list(thread.messages.order_by('-created_at')[:10])
    history.reverse()
    try:
        file_ids = _collect_attachment_file_ids(client, thread.professional, thread.patient)
    except Exception:
        file_ids = []
    input_parts = []
    for fid in file_ids:
        input_parts.append({"type": "input_file", "file_id": fid})
    # Base instruction + context
    base_text = (
        "Eres un asistente clínico y debes responder solo sobre este paciente. "
        "Usa exclusivamente el contexto y adjuntos.\n\n" + (thread.context or '')
    )
    input_parts.append({"type": "input_text", "text": base_text})
    # Short conversation transcript as text blocks
    for m in history:
        role = 'Usuario' if m.role == 'user' else ('Asistente' if m.role == 'assistant' else 'Sistema')
        input_parts.append({"type": "input_text", "text": f"{role}:\n{m.content}"})
    # The new question
    input_parts.append({"type": "input_text", "text": f"Usuario:\n{question}"})

    try:
        PatientAIMessage.objects.create(thread=thread, role='user', content=question)
        resp = client.responses.create(model=thread.model or 'gpt-5', input=[{"role": "user", "content": input_parts}])
        answer = getattr(resp, 'output_text', None) or ''
        if not answer and hasattr(resp, 'output'):
            try:
                answer = ' '.join([o.get('content', [{}])[0].get('text', {}).get('value', '') for o in resp.output])
            except Exception:
                answer = ''
        PatientAIMessage.objects.create(thread=thread, role='assistant', content=answer or '')
        return JsonResponse({'ok': True, 'answer': answer})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error IA: {e}'}, status=500)


@login_required
def patient_history_manager(request, patient_id):
    prof = _get_professional(request.user)
    patient = get_object_or_404(Patient, id=patient_id)
    if not (request.user.is_staff or (prof and patient.professional_id == prof.id)):
        messages.error(request, 'No autorizado')
        return redirect('my_patients')
    consultations = Consultation.objects.filter(patient=patient, professional=prof).filter(status__in=['attended', 'completed']).order_by('-date', '-time')
    notes = ConsultationNote.objects.filter(consultation__in=consultations).select_related('consultation').order_by('-created_at')
    atts = ConsultationAttachment.objects.filter(consultation__in=consultations).select_related('consultation').order_by('-uploaded_at')
    return render(request, 'pages/patient_history_manager.html', {
        'segment': 'patient_history_manager',
        'patient': patient,
        'consultations': consultations,
        'notes': notes,
        'attachments': atts,
    })