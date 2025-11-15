from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from .models import PaymentRequest, Payment
from .forms import PaymentCreateForm


def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Sección disponible solo para administradores.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@staff_required
def dashboard(request):
    # KPIs
    reqs = PaymentRequest.objects.select_related('consultation')
    counts = {
        'pending': sum(1 for r in reqs if r.status == 'pending'),
        'partial': sum(1 for r in reqs if r.status == 'partial'),
        'paid': sum(1 for r in reqs if r.status == 'paid'),
    }
    # Last 30 days payments
    since = timezone.now() - timezone.timedelta(days=30)
    last_payments = Payment.objects.filter(paid_at__gte=since)
    total_30d = last_payments.aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'pages/finance/dashboard.html', {
        'segment': 'finance_dashboard',
        'counts': counts,
        'total_30d': total_30d,
    })


@login_required
@staff_required
def payment_requests_list(request):
    status_filter = request.GET.get('status')
    reqs = list(PaymentRequest.objects.select_related('consultation__patient', 'consultation__professional'))
    if status_filter in {'pending', 'partial', 'paid'}:
        reqs = [r for r in reqs if r.status == status_filter]
    return render(request, 'pages/finance/payment_requests_list.html', {
        'segment': 'finance_requests',
        'requests': reqs,
        'status_filter': status_filter,
    })


@login_required
@staff_required
def payment_request_detail(request, request_id):
    pr = get_object_or_404(PaymentRequest.objects.select_related('consultation__patient', 'consultation__professional'), id=request_id)
    if request.method == 'POST':
        form = PaymentCreateForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.request = pr
            payment.created_by = request.user
            payment.currency = pr.currency
            payment.save()
            messages.success(request, 'Pago registrado correctamente.')
            return redirect('finance_request_detail', request_id=pr.id)
        else:
            messages.error(request, 'Verifica los datos del pago.')
    else:
        form = PaymentCreateForm()

    return render(request, 'pages/finance/payment_request_detail.html', {
        'segment': 'finance_requests',
        'pr': pr,
        'form': form,
    })


@login_required
@staff_required
def payments_list(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    qs = Payment.objects.select_related('request__consultation__patient').order_by('-paid_at')
    try:
        if start:
            qs = qs.filter(paid_at__date__gte=datetime.strptime(start, '%Y-%m-%d').date())
        if end:
            qs = qs.filter(paid_at__date__lte=datetime.strptime(end, '%Y-%m-%d').date())
    except Exception:
        messages.warning(request, 'Rango de fechas inválido.')

    total = qs.aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'pages/finance/payments_list.html', {
        'segment': 'finance_payments',
        'payments': qs,
        'total': total,
        'start': start or '',
        'end': end or '',
    })
