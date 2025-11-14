from datetime import datetime, time, timedelta
from django.utils import timezone
from apps.pages.models import WeeklyAvailability, AvailabilityException, Consultation

def generate_slots(professional, date_obj, duration_minutes=60):
    """Return list of available start times (as 'HH:MM') for professional on given date.
    Excludes slots outside availability window and those overlapping existing consultations."""
    # Determine weekday availability
    weekday = date_obj.weekday()  # Monday=0
    try:
        weekly = professional.weekly_availability.get(weekday=weekday)
    except WeeklyAvailability.DoesNotExist:
        return []
    if weekly.is_closed:
        return []

    # Check exception override
    try:
        exception = professional.availability_exceptions.get(date=date_obj)
        if exception.is_closed:
            return []
        start = exception.start_time or weekly.start_time
        end = exception.end_time or weekly.end_time
    except AvailabilityException.DoesNotExist:
        start = weekly.start_time
        end = weekly.end_time

    if not start or not end:
        return []

    # Existing consultations that day
    day_consults = Consultation.objects.filter(professional=professional, date=date_obj).order_by('time')
    occupied = []
    for c in day_consults:
        start_dt = datetime.combine(date_obj, c.time)
        end_dt = start_dt + timedelta(minutes=c.duration)
        occupied.append((start_dt, end_dt))

    # Generate candidate slots
    slots = []
    cursor = datetime.combine(date_obj, start)
    end_limit = datetime.combine(date_obj, end)
    block = timedelta(minutes=duration_minutes)

    while cursor + block <= end_limit:
        slot_start = cursor
        slot_end = cursor + block
        # Check overlap
        conflict = False
        for o_start, o_end in occupied:
            if slot_start < o_end and o_start < slot_end:
                conflict = True
                break
        if not conflict:
            slots.append(slot_start.strftime('%H:%M'))
        cursor += timedelta(minutes=duration_minutes)
    return slots
