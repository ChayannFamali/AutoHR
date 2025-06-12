from django.contrib import admin

from .models import (Notification, NotificationPreference,
                     NotificationTemplate, NotificationType)


@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['notification_type', 'user', 'candidate', 'channel', 'status', 'created_at']
    list_filter = ['status', 'channel']
    search_fields = ['subject', 'user__username']

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['notification_type', 'language', 'channel', 'is_active']
    list_filter = ['language', 'channel', 'is_active']

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_enabled', 'sms_enabled', 'in_app_enabled']
    search_fields = ['user__username']
