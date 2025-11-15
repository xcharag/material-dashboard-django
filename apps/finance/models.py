from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone


class PaymentRequest(models.Model):
    consultation = models.OneToOneField(
        'pages.Consultation', on_delete=models.CASCADE, related_name='payment_request'
    )
    expected_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='BOB')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['currency']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"PR#{self.id} for consultation {self.consultation_id}"

    @property
    def amount_paid(self) -> Decimal:
        agg = self.payments.aggregate(total=models.Sum('amount'))
        return agg['total'] or Decimal('0.00')

    @property
    def balance(self) -> Decimal:
        if self.expected_amount is None:
            return Decimal('0.00')
        return (self.expected_amount or Decimal('0.00')) - self.amount_paid

    @property
    def status(self) -> str:
        if self.expected_amount is None or self.expected_amount == Decimal('0.00'):
            return 'pending'
        paid = self.amount_paid
        if paid <= Decimal('0.00'):
            return 'pending'
        if paid >= (self.expected_amount or Decimal('0.00')):
            return 'paid'
        return 'partial'


class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'Efectivo'),
        ('card', 'Tarjeta'),
        ('qr', 'QR'),
    ]

    request = models.ForeignKey(PaymentRequest, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='BOB')
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    reference = models.CharField(max_length=100, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    paid_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['paid_at']),
            models.Index(fields=['method']),
        ]

    def __str__(self):
        return f"Payment {self.amount} {self.currency} via {self.method}"
