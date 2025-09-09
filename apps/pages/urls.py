from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('patients/', views.patients, name='patients'),
    path('patients/<int:patient_id>/edit/', views.edit_patient, name='edit_patient'),
    path('patients/<int:patient_id>/delete/', views.delete_patient, name='delete_patient'),
    path('professionals/', views.professionals, name='professionals'),
    path('consult/', views.consult, name='consult'),
    path('start-session/<int:consultation_id>/', views.start_session, name='start_session'),
]
