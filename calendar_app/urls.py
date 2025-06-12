from django.urls import path

from . import views

app_name = 'calendar_app'

urlpatterns = [
    path('interviews/', views.InterviewListView.as_view(), name='interview_list'),
    path('interviews/<int:pk>/', views.interview_detail, name='interview_detail'),
    path('calendar/', views.interview_calendar, name='interview_calendar'),
]
