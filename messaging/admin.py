from django.contrib import admin

from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'related_job', 'created_at', 'updated_at']
    raw_id_fields = ['related_job']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'created_at', 'read_at']
    list_filter = ['created_at', 'read_at']
    search_fields = ['body', 'sender__username']
    raw_id_fields = ['conversation', 'sender']
