from django.urls import path

from . import views

app_name = 'calendar_app'

urlpatterns = [
    path('interviews/', views.InterviewListView.as_view(), name='interview_list'),
    path('interviews/<int:pk>/', views.interview_detail, name='interview_detail'),
    path('interviews/schedule/', views.schedule_interview, name='schedule_interview'),
    path('calendar/', views.interview_calendar, name='interview_calendar'),
    path('interviews/<int:interview_id>/update-status/', views.update_interview_status, name='update_interview_status'),
    path('interviews/<int:interview_id>/reschedule/', views.reschedule_interview, name='reschedule_interview'),
    path('interviews/<int:interview_id>/add-notes/', views.add_interview_notes, name='add_interview_notes'),
    path('interviews/<int:interview_id>/feedback/', views.save_interview_feedback, name='save_feedback'),
    path('interviews/<int:interview_id>/send-reminder/', views.send_interview_reminder, name='send_reminder'),
]

