from django.contrib import admin

from .models import (Interview, InterviewAvailability, InterviewTimeSlot,
                     InterviewType)


@admin.register(InterviewType)
class InterviewTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_minutes', 'is_active']

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'interviewer', 'scheduled_at', 'status', 'format']
    list_filter = ['status', 'format']
    search_fields = ['candidate__first_name', 'interviewer__username']

@admin.register(InterviewAvailability)
class InterviewAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['interviewer', 'weekday', 'start_time', 'end_time', 'is_active']
    list_filter = ['weekday', 'is_active']

@admin.register(InterviewTimeSlot)
class InterviewTimeSlotAdmin(admin.ModelAdmin):
    list_display = ['interviewer', 'date', 'start_time', 'end_time', 'is_booked']
    list_filter = ['is_booked', 'date']
