from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='finance_dashboard'),
    path('requests/', views.payment_requests_list, name='finance_requests'),
    path('requests/<int:request_id>/', views.payment_request_detail, name='finance_request_detail'),
    path('payments/', views.payments_list, name='finance_payments'),
]
