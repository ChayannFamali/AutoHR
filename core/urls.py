from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.JobListView.as_view(), name='job_list'),
    path('jobs/', views.JobListView.as_view(), name='job_list'),
    path('jobs/htmx/', views.job_list_htmx, name='job_list_htmx'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('jobs/<int:job_id>/apply/', views.apply_for_job, name='apply_job'),
    path('jobs/<int:job_id>/toggle-save/', views.toggle_save_job, name='toggle_save_job'),
    path('companies/', views.company_list, name='company_list'),
    path('companies/<slug:slug>/', views.company_detail, name='company_detail'),
    path('companies/<slug:slug>/review/', views.add_company_review, name='add_company_review'),
    path('favorites/', views.favorites_list, name='favorites_list'),
    path('favorites/save-search/', views.save_current_search, name='save_search'),
    path('favorites/saved-search/<int:search_id>/run/', views.run_saved_search, name='run_saved_search'),
    path('favorites/saved-search/<int:search_id>/delete/', views.delete_saved_search, name='delete_saved_search'),
    path('applications/', views.ApplicationListView.as_view(), name='application_list'),
    path('applications/export/', views.export_applications_excel, name='export_applications'),
    path('jobs/create/', views.create_job, name='create_job'),
    path('jobs/my/', views.job_list_hr, name='job_list_hr'),
    path('applications/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
    path('applications/<int:application_id>/update-status-htmx/', views.update_application_status_htmx, name='update_application_status_htmx'),
    path('applications/<int:application_id>/schedule/', views.schedule_interview_for_application, name='schedule_interview_quick'),
    path('applications/<int:application_id>/detail/', views.application_detail, name='application_detail'),
    path('applications/<int:application_id>/add-note/', views.add_note_to_application, name='add_note_to_application'),
    path('jobs/<int:pk>/edit/', views.JobEditView.as_view(), name='edit_job'),
    path('jobs/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    # HTMX-эндпоинты (Этап 4.5)
    path('jobs/<int:job_id>/delete-htmx/', views.delete_job_htmx, name='delete_job_htmx'),
    path('applications/<int:application_id>/detail-htmx/', views.application_detail_htmx, name='application_detail_htmx'),
    path('applications/<int:application_id>/schedule-htmx/', views.schedule_interview_htmx, name='schedule_interview_htmx'),
    path('applications/<int:application_id>/add-note-htmx/', views.add_note_htmx, name='add_note_htmx'),
    path('interviews/<int:interview_id>/update-status-htmx/', views.update_interview_status_htmx, name='update_interview_status_htmx'),
    path('interviews/<int:interview_id>/reschedule-htmx/', views.reschedule_interview_htmx, name='reschedule_interview_htmx'),
    path('interviews/<int:interview_id>/feedback-htmx/', views.save_interview_feedback_htmx, name='save_interview_feedback_htmx'),
]
