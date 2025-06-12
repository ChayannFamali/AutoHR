from django.contrib import admin

from .models import AIModel, AnalysisTask, JobCandidateMatch


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_type', 'version', 'is_active']
    list_filter = ['model_type', 'is_active']

@admin.register(AnalysisTask)
class AnalysisTaskAdmin(admin.ModelAdmin):
    list_display = ['task_type', 'status', 'created_at', 'processing_time']
    list_filter = ['task_type', 'status']

@admin.register(JobCandidateMatch)
class JobCandidateMatchAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'job', 'overall_score', 'recommendation', 'created_at']
    list_filter = ['recommendation']
    search_fields = ['candidate__first_name', 'job__title']
