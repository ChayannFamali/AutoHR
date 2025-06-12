from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.JobListView.as_view(), name='job_list'),
    path('jobs/', views.JobListView.as_view(), name='job_list'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('jobs/<int:job_id>/apply/', views.apply_for_job, name='apply_job'),
    path('applications/', views.ApplicationListView.as_view(), name='application_list'),
]
