from django.urls import path

from . import views

app_name = 'resume'

urlpatterns = [
    path('upload/', views.upload_resume, name='upload_resume'),
    path('upload/<int:application_id>/', views.upload_resume, name='upload_resume_for_application'),
    path('list/', views.resume_list, name='resume_list'),
    path('<int:pk>/', views.resume_detail, name='resume_detail'),
]
