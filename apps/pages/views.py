from datetime import datetime,timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import views as auth_views
from django.db import IntegrityError
from .models import Patient, Professional, Consultation, ConsultationNote, ConsultationAttachment, Consultorio
from django.contrib import messages
from .forms import CustomLoginForm, UsernameRecoveryForm
from .forms import ProfessionalProfileForm, ProfessionalContactForm
from .forms import AvailabilityExceptionForm
from django.http import JsonResponse
from datetime import datetime as dt, date as ddate
from .utils.availability import generate_slots
from datetime import time as dtime

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

        # Update patient information
        patient.first_name = first_name
        patient.last_name = last_name
        patient.email = email
        patient.phone = phone
        if date_of_birth:
            patient.date_of_birth = date_of_birth
        patient.address = address

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
    data = []
    for p in patients_qs:
        consultations = Consultation.objects.filter(patient=p)
        total_paid = sum([c.charge for c in consultations]) if consultations.exists() else 0
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

    consultations = Consultation.objects.filter(patient=patient).order_by('-date','-time')
    total_paid = sum([c.charge for c in consultations]) if consultations.exists() else 0
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
        # Process form data
        patient_id = request.POST.get('patient')
        consultory_id = request.POST.get('consultory')
        date = request.POST.get('date')
        time = request.POST.get('time')
        duration = request.POST.get('duration')
        charge = request.POST.get('charge')
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
            charge=charge,
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
                ex = exception_form.save(commit=False)
                ex.professional = professional
                ex.save()
                messages.success(request, 'Excepción agregada.')
                return redirect('profile')
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
    consultations = qs.order_by('date', 'time')

    return render(request, 'pages/_consult_table.html', {
        'consultations': consultations,
    })


@login_required
@staff_required
def consultorios_calendar(request):
    # Params
    date_str = request.GET.get('date')
    try:
        target_date = dt.strptime(date_str, '%Y-%m-%d').date() if date_str else ddate.today()
    except Exception:
        target_date = ddate.today()

    consultorio_id = request.GET.get('consultorio')
    if consultorio_id and str(consultorio_id).isdigit():
        consultorios = list(Consultorio.objects.filter(id=int(consultorio_id)))
    else:
        consultorios = list(Consultorio.objects.filter(is_active=True))

    # Time grid setup (07:00 to 21:00 in 30 min steps)
    from datetime import time as dtime
    start_time = dtime(7, 0)
    end_time = dtime(21, 0)
    step_minutes = 30
    total_slots = int(((end_time.hour*60 + end_time.minute) - (start_time.hour*60 + start_time.minute)) / step_minutes)
    times = []
    sh = start_time.hour; sm = start_time.minute
    for i in range(total_slots):
        minutes = sh*60 + sm + i*step_minutes
        h = minutes // 60; m = minutes % 60
        times.append(f"{h:02d}:{m:02d}")

    # Build grid per consultorio
    columns_rows = {}
    for c in consultorios:
        rows = [None] * total_slots
        qs = Consultation.objects.filter(date=target_date).filter(consultorio_fk=c)
        if not qs.exists():
            qs = Consultation.objects.filter(date=target_date, consultory=c.name)
        for cons in qs.order_by('time'):
            idx = int(((cons.time.hour*60 + cons.time.minute) - (start_time.hour*60 + start_time.minute)) / step_minutes)
            if idx < 0:
                continue
            # ceil division for span
            span = (cons.duration or 60)
            span = int((span + step_minutes - 1) / step_minutes)
            span = min(span, max(0, total_slots - idx))
            if idx >= total_slots:
                continue
            if rows[idx] is None:
                rows[idx] = {'type': 'start', 'consult': cons, 'rowspan': span}
                for k in range(1, span):
                    if idx + k < total_slots:
                        rows[idx + k] = {'type': 'skip'}
        columns_rows[c.id] = rows

    cal_rows = []
    for i, t in enumerate(times):
        cells = []
        for c in consultorios:
            cell = columns_rows[c.id][i]
            if cell is None:
                cells.append({'type': 'empty'})
            else:
                cells.append(cell)
        cal_rows.append({'time': t, 'cells': cells})

    context = {
        'segment': 'consultorios_calendar',
        'consultorios': consultorios,
        'times': times,
        'cal_rows': cal_rows,
        'target_date': target_date,
        'selected_consultorio_id': int(consultorio_id) if consultorio_id and str(consultorio_id).isdigit() else '',
    }
    return render(request, 'pages/consultorios_calendar.html', context)