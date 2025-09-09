from datetime import datetime,timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import views as auth_views
from .models import Patient, Professional, Consultation
from django.contrib import messages
from .forms import CustomLoginForm

# Create your views here.

@login_required
def index(request):
    return render(request, 'pages/index.html', {'segment': 'dashboard'})

class CustomLoginView(auth_views.LoginView):
    template_name = 'pages/sign-in.html'
    form_class = CustomLoginForm
    success_url = '/'

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
@login_required
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

    # Get all professionals
    professionals_list = Professional.objects.all().order_by('-created_at')

    return render(request, 'pages/professionals.html', {
        'segment': 'profesional',
        'professionals': professionals_list
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
        consultory = request.POST.get('consultory')
        date = request.POST.get('date')
        time = request.POST.get('time')
        duration = request.POST.get('duration')
        charge = request.POST.get('charge')
        notes = request.POST.get('notes')

        # If admin, they can specify the professional
        if is_admin and request.POST.get('professional'):
            professional = Professional.objects.get(id=request.POST.get('professional'))

        # Create new consultation
        patient = Patient.objects.get(id=patient_id)
        Consultation.objects.create(
            patient=patient,
            professional=professional,
            consultory=consultory,
            date=date,
            time=time,
            duration=duration,
            charge=charge,
            notes=notes
        )
        messages.success(request, 'Consulta programada con éxito!')
        return redirect('consult')

    # Get patients based on user role
    patients = Patient.objects.all() if is_admin else Patient.objects.filter(professional=professional)

    # Get all professionals for admin selection
    all_professionals = Professional.objects.all() if is_admin else None

    # Get consultations
    consultations = Consultation.objects.all() if is_admin else Consultation.objects.filter(
        professional=professional,
    )
    consultations = consultations.order_by('date', 'time')

    # Get next consultation for the professional
    next_consultation = Consultation.objects.all() if is_admin else Consultation.objects.filter(
        professional=professional,
        date__gte=datetime.now().date()
    ).order_by('date', 'time').first()

    return render(request, 'pages/consult.html', {
        'segment': 'citas',
        'patients': patients,
        'consultations': consultations,
        'all_professionals': all_professionals,
        'is_admin': is_admin
    })


# Add this temporary view for the "start session" button
@login_required
def start_session(request, consultation_id):
    # This will be implemented later
    messages.success(request, 'Sesión iniciada')
    return redirect('consult')