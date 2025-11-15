from django.db import migrations
from decimal import Decimal, ROUND_HALF_UP


def backfill_expected_amount(apps, schema_editor):
    PaymentRequest = apps.get_model('finance', 'PaymentRequest')
    # Consultation is related via OneToOne on PaymentRequest.consultation
    for pr in PaymentRequest.objects.select_related('consultation').all():
        if pr.expected_amount is None and getattr(pr, 'consultation', None):
            duration = getattr(pr.consultation, 'duration', 0) or 0
            blocks = (Decimal(duration) / Decimal(30)) if duration else Decimal(0)
            suggested = (Decimal('250.00') * blocks).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            pr.expected_amount = suggested
            if not pr.currency:
                pr.currency = 'BOB'
            pr.save(update_fields=['expected_amount', 'currency'])


class Migration(migrations.Migration):
    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(backfill_expected_amount, migrations.RunPython.noop),
    ]
