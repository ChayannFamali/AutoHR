from django.urls import path

from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('api/applications-chart/', views.applications_chart_data, name='applications_chart'),
    path('api/ai-scores/', views.ai_scores_distribution, name='ai_scores'),
    path('api/popular-skills/', views.popular_skills_data, name='popular_skills'),
    path('api/application-status/', views.application_status_data, name='application_status'),
    path('api/interview-completion/', views.interview_completion_rate, name='interview_completion'),
    path('api/top-jobs/', views.top_jobs_by_applications, name='top_jobs'),
    path('api/resume-processing/', views.resume_processing_stats, name='resume_processing'),
    path('api/recruitment-funnel/', views.recruitment_funnel, name='recruitment_funnel'),
    path('api/conversion-rates/', views.conversion_rates, name='conversion_rates'),
    path('api/time-to-hire/', views.time_to_hire, name='time_to_hire'),
    path('api/top-employers/', views.top_employers, name='top_employers'),
]