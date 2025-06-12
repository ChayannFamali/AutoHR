from django.contrib import admin

from .models import Application, Candidate, Company, Job


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'website', 'created_at']
    search_fields = ['name']

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'experience_level', 'status', 'created_at']
    list_filter = ['status', 'experience_level', 'remote_work']
    search_fields = ['title', 'company__name']

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'location', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'job', 'status', 'ai_score', 'applied_at']
    list_filter = ['status']
    search_fields = ['candidate__first_name', 'candidate__last_name', 'job__title']
