from datetime import datetime, time, timedelta
from django.utils import timezone
from apps.pages.models import WeeklyAvailability, AvailabilityException, Consultation

def generate_slots(professional, date_obj, duration_minutes=60, step_minutes=30):
    """Return list of available start times (as 'HH:MM') for professional on a date.
    - Uses weekly availability window as the working day
    - AvailabilityException:
        * is_closed=True => entire day unavailable
        * start_time+end_time => block that range only (rest of day remains available)
    - Excludes overlaps with existing consultations.
    """
    # Determine weekday availability
    weekday = date_obj.weekday()  # Monday=0
    try:
        weekly = professional.weekly_availability.get(weekday=weekday)
    except WeeklyAvailability.DoesNotExist:
        return []
    if weekly.is_closed:
        return []

    day_start = weekly.start_time
    day_end = weekly.end_time
    if not day_start or not day_end:
        return []

    # Exception acts as a blocked interval inside the day (unless closed)
    blocked_intervals = []
    try:
        exception = professional.availability_exceptions.get(date=date_obj)
        if exception.is_closed:
            return []
        if exception.start_time and exception.end_time:
            ex_start_dt = datetime.combine(date_obj, exception.start_time)
            ex_end_dt = datetime.combine(date_obj, exception.end_time)
            if ex_start_dt < ex_end_dt:
                blocked_intervals.append((ex_start_dt, ex_end_dt))
    except AvailabilityException.DoesNotExist:
        pass

    # Existing consultations that day (treat as occupied intervals)
    day_consults = Consultation.objects.filter(professional=professional, date=date_obj).order_by('time')
    occupied = []
    for c in day_consults:
        c_start_dt = datetime.combine(date_obj, c.time)
        c_end_dt = c_start_dt + timedelta(minutes=c.duration)
        occupied.append((c_start_dt, c_end_dt))

    # Add blocked intervals from exception to occupied list
    occupied.extend(blocked_intervals)

    # Generate candidate slots across the working day
    slots = []
    cursor = datetime.combine(date_obj, day_start)
    end_limit = datetime.combine(date_obj, day_end)
    block = timedelta(minutes=duration_minutes)
    step = timedelta(minutes=step_minutes)

    while cursor + block <= end_limit:
        slot_start = cursor
        slot_end = cursor + block
        # Check overlap against all occupied intervals
        conflict = False
        for o_start, o_end in occupied:
            if slot_start < o_end and o_start < slot_end:
                conflict = True
                break
        if not conflict:
            slots.append(slot_start.strftime('%H:%M'))
        cursor += step
    return slots
