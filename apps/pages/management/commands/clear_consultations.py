from django.core.management.base import BaseCommand
from apps.pages.models import Consultation


class Command(BaseCommand):
    help = "Delete all Consultation entries (use with caution)"

    def handle(self, *args, **options):
        count = Consultation.objects.count()
        Consultation.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} consultations."))
