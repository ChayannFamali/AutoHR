from django.contrib import admin

from .models import Resume, ResumeAnalysis


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'original_filename', 'status', 'language', 'uploaded_at']
    list_filter = ['status', 'language']
    search_fields = ['candidate__first_name', 'candidate__last_name']

@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = ['resume', 'completeness_score', 'analyzed_at']
    search_fields = ['resume__candidate__first_name', 'resume__candidate__last_name']
