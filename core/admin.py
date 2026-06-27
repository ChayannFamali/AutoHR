from django.contrib import admin

from .models import (Application, Candidate, Company, CompanyReview, Education,
                     Job, SavedJob, SavedSearch, Skill, WorkExperience)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'industry', 'employee_count', 'created_at']
    list_filter = ['industry']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CompanyReview)
class CompanyReviewAdmin(admin.ModelAdmin):
    list_display = ['company', 'rating', 'author', 'is_anonymous', 'created_at']
    list_filter = ['rating', 'is_anonymous', 'created_at']
    search_fields = ['company__name', 'text', 'title']
    raw_id_fields = ['author', 'company']
    readonly_fields = ['created_at', 'updated_at']


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


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'job__title']
    raw_id_fields = ['user', 'job']


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at', 'last_used_at']
    list_filter = ['created_at']
    search_fields = ['name', 'user__username']
    raw_id_fields = ['user']


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'position', 'company', 'start_date', 'is_current']
    list_filter = ['is_current']
    search_fields = ['company', 'position', 'candidate__first_name']
    raw_id_fields = ['candidate']


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'institution', 'degree', 'end_year']
    list_filter = ['degree']
    search_fields = ['institution', 'field_of_study', 'candidate__first_name']
    raw_id_fields = ['candidate']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'name', 'level', 'years_of_experience']
    list_filter = ['level']
    search_fields = ['name', 'candidate__first_name']
    raw_id_fields = ['candidate']
