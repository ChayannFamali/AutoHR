from django.urls import path

from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.conversation_list, name='conversation_list'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('start/<int:user_id>/<int:job_id>/', views.start_conversation, name='start_conversation_with_job'),
    path('<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('<int:conversation_id>/poll/', views.poll_messages, name='poll_messages'),
]
