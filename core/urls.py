from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.JobListView.as_view(), name='job_list'),
    path('jobs/', views.JobListView.as_view(), name='job_list'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('jobs/<int:job_id>/apply/', views.apply_for_job, name='apply_job'),
    path('applications/', views.ApplicationListView.as_view(), name='application_list'),
    path('applications/export/', views.export_applications_excel, name='export_applications'),
    path('jobs/create/', views.create_job, name='create_job'),
    path('jobs/my/', views.job_list_hr, name='job_list_hr'),
    path('applications/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
    path('applications/<int:application_id>/schedule/', views.schedule_interview_for_application, name='schedule_interview_quick'),
    path('applications/<int:application_id>/detail/', views.application_detail, name='application_detail'),
    path('applications/<int:application_id>/add-note/', views.add_note_to_application, name='add_note_to_application'),
    path('jobs/<int:pk>/edit/', views.JobEditView.as_view(), name='edit_job'),
]
