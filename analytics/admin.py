from django.contrib import admin

from .models import AnalyticsSnapshot, PopularSkill


@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_applications', 'total_resumes', 'total_interviews', 'avg_ai_score')
    list_filter = ('date',)
    search_fields = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at',)


@admin.register(PopularSkill)
class PopularSkillAdmin(admin.ModelAdmin):
    list_display = ('skill_name', 'frequency', 'period_start', 'period_end', 'created_at')
    list_filter = ('period_start', 'period_end')
    search_fields = ('skill_name',)
    date_hierarchy = 'period_start'
    readonly_fields = ('created_at',)