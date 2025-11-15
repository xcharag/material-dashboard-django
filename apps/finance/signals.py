from decimal import Decimal, ROUND_HALF_UP
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.pages.models import Consultation
from .models import PaymentRequest


@receiver(post_save, sender=Consultation)
def create_payment_request_on_consultation(sender, instance: Consultation, created, **kwargs):
    # Price suggestion: 250 BOB per 30 minutes
    blocks = (Decimal(instance.duration) / Decimal(30)) if instance.duration else Decimal(0)
    suggested = (Decimal('250.00') * blocks).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    pr, pr_created = PaymentRequest.objects.get_or_create(
        consultation=instance,
        defaults={
            'expected_amount': suggested,
            'currency': 'BOB',
        }
    )
    # If it existed without expected amount, update once
    if not pr_created and (pr.expected_amount is None):
        pr.expected_amount = suggested
        if not pr.currency:
            pr.currency = 'BOB'
        pr.save(update_fields=['expected_amount', 'currency'])
