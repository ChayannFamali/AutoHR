from datetime import timedelta

# Create your models here.
from django.db import models
from django.db.models import Avg, Count
from django.utils import timezone


class AnalyticsSnapshot(models.Model):
    """Снимок аналитических данных на определенную дату"""
    date = models.DateField(default=timezone.now)
    total_applications = models.IntegerField(default=0)
    total_resumes = models.IntegerField(default=0)
    total_interviews = models.IntegerField(default=0)
    avg_ai_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['date']
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics for {self.date}"

class PopularSkill(models.Model):
    """Популярные навыки за период"""
    skill_name = models.CharField(max_length=100)
    frequency = models.IntegerField(default=0)
    period_start = models.DateField()
    period_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-frequency']
