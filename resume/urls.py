from django.urls import path

from . import views

app_name = 'resume'

urlpatterns = [
    path('upload/', views.upload_resume, name='upload_resume'),
    path('upload/<int:application_id>/', views.upload_resume, name='upload_resume_for_application'),
    path('list/', views.resume_list, name='resume_list'),
    path('<int:pk>/', views.resume_detail, name='resume_detail'),
    path('export/excel/', views.export_resumes_excel, name='export_resumes_excel'),
    path('export/csv/', views.export_resumes_csv, name='export_resumes_csv'),
    path('export/pdf/', views.export_resumes_pdf, name='export_resumes_pdf'),
    path('<int:resume_id>/reprocess/', views.reprocess_resume, name='reprocess_resume'),
]
