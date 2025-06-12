from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import Application, Candidate, Job
from resume.models import Resume


class AIModel(models.Model):
    MODEL_TYPES = [
        ('embedding', 'Embedding Model'),
        ('classification', 'Classification Model'),
        ('scoring', 'Scoring Model'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Название модели")
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES, verbose_name="Тип модели")
    version = models.CharField(max_length=20, verbose_name="Версия")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    config = models.JSONField(default=dict, verbose_name="Конфигурация")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "AI Модель"
        verbose_name_plural = "AI Модели"
    
    def __str__(self):
        return f"{self.name} v{self.version}"

class AnalysisTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('running', 'Выполняется'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
    ]
    
    TASK_TYPES = [
        ('resume_analysis', 'Анализ резюме'),
        ('job_matching', 'Сопоставление с вакансией'),
        ('bulk_analysis', 'Массовый анализ'),
    ]
    
    task_type = models.CharField(max_length=30, choices=TASK_TYPES, verbose_name="Тип задачи")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Резюме")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Вакансия")
    application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Заявка")
    
    # Результаты
    result_data = models.JSONField(default=dict, verbose_name="Данные результата")
    error_message = models.TextField(blank=True, verbose_name="Сообщение об ошибке")
    processing_time = models.FloatField(null=True, blank=True, verbose_name="Время обработки (сек)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Задача анализа"
        verbose_name_plural = "Задачи анализа"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_task_type_display()} - {self.status}"

class JobCandidateMatch(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name="Вакансия")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, verbose_name="Кандидат")
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, verbose_name="Резюме")
    
    # Оценки соответствия
    overall_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="Общая оценка"
    )
    skills_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="Оценка навыков"
    )
    experience_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="Оценка опыта"
    )
    
    # Детальный анализ
    matched_skills = models.JSONField(default=list, verbose_name="Совпадающие навыки")
    missing_skills = models.JSONField(default=list, verbose_name="Недостающие навыки")
    experience_analysis = models.JSONField(default=dict, verbose_name="Анализ опыта")
    
    # AI рекомендации
    recommendation = models.CharField(
        max_length=20,
        choices=[
            ('strong_match', 'Сильное соответствие'),
            ('good_match', 'Хорошее соответствие'),
            ('partial_match', 'Частичное соответствие'),
            ('weak_match', 'Слабое соответствие'),
        ],
        verbose_name="Рекомендация"
    )
    reasoning = models.TextField(verbose_name="Обоснование")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Соответствие кандидата вакансии"
        verbose_name_plural = "Соответствия кандидатов вакансиям"
        unique_together = ['job', 'candidate', 'resume']
        ordering = ['-overall_score']
    
    def __str__(self):
        return f"{self.candidate.full_name} -> {self.job.title} ({self.overall_score:.2f})"
