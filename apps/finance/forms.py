from django import forms
from .models import Payment


class PaymentCreateForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'method', 'reference', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
