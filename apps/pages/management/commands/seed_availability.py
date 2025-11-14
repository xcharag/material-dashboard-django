from django.core.management.base import BaseCommand
from datetime import time
from apps.pages.models import Professional, WeeklyAvailability

DEFAULTS = {
    0: (time(9, 0), time(17, 0)),  # Monday
    1: (time(9, 0), time(17, 0)),  # Tuesday
    2: (time(9, 0), time(17, 0)),  # Wednesday
    3: (time(9, 0), time(17, 0)),  # Thursday
    4: (time(9, 0), time(17, 0)),  # Friday
    5: (time(9, 0), time(12, 0)),  # Saturday
    6: None,                      # Sunday closed
}

class Command(BaseCommand):
    help = "Seed default weekly availability for all professionals if missing"

    def handle(self, *args, **options):
        created = 0
        for prof in Professional.objects.all():
            for wd in range(7):
                if not WeeklyAvailability.objects.filter(professional=prof, weekday=wd).exists():
                    data = DEFAULTS.get(wd)
                    if data is None:
                        WeeklyAvailability.objects.create(
                            professional=prof,
                            weekday=wd,
                            is_closed=True
                        )
                    else:
                        WeeklyAvailability.objects.create(
                            professional=prof,
                            weekday=wd,
                            start_time=data[0],
                            end_time=data[1],
                            is_closed=False
                        )
                    created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} availability entries."))
