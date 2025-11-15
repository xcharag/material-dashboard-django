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
    path('end-session/<int:consultation_id>/', views.end_session, name='end_session'),
    path('profile/', views.profile, name='profile'),
    path('api/available-slots/', views.available_slots_api, name='available_slots_api'),
    path('mis-pacientes/', views.my_patients, name='my_patients'),
    path('mis-pacientes/<int:patient_id>/', views.patient_history, name='patient_history'),
    path('config/consultorios/', views.config_consultorios, name='config_consultorios'),
    path('config/consultorios/calendario/', views.consultorios_calendar, name='consultorios_calendar'),
    path('consult/delete/<int:consultation_id>/', views.consultation_delete_api, name='consultation_delete_api'),
    path('consult/cancel/<int:consultation_id>/', views.consultation_cancel_api, name='consultation_cancel_api'),
    path('patient/<int:patient_id>/color/', views.patient_color_update_api, name='patient_color_update_api'),
    path('consult/list/', views.consult_table, name='consult_table'),
    path('api/calendar/events/', views.calendar_events_api, name='calendar_events_api'),
    path('consult/update-time/<int:consultation_id>/', views.consultation_time_update_api, name='consultation_time_update_api'),
    # AI Report & Chat
    path('report/sessions/', views.report_sessions, name='report_sessions'),
    path('report/sessions/chat/', views.report_sessions_chat, name='report_sessions_chat'),
    # History manager
    path('patients/<int:patient_id>/history-manager/', views.patient_history_manager, name='patient_history_manager'),
]
