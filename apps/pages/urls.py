from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('accounts/username-recovery/', views.username_recovery, name='username_recovery'),
    path('accounts/password-reset/', auth_views.PasswordResetView.as_view(
        template_name='pages/password_reset.html',
        email_template_name='pages/password_reset_email.html',
        subject_template_name='pages/password_reset_subject.txt'
    ), name='password_reset'),
    path('accounts/password-reset-done/', auth_views.PasswordResetDoneView.as_view(
        template_name='pages/password_reset_done.html'
    ), name='password_reset_done'),
    path('accounts/password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='pages/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('accounts/password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='pages/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('patients/', views.patients, name='patients'),
    path('patients/<int:patient_id>/edit/', views.edit_patient, name='edit_patient'),
    path('patients/<int:patient_id>/delete/', views.delete_patient, name='delete_patient'),
    path('professionals/', views.professionals, name='professionals'),
    path('consult/', views.consult, name='consult'),
    path('start-session/<int:consultation_id>/', views.start_session, name='start_session'),
]
