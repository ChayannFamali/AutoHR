import os

from django.core.validators import FileExtensionValidator
from django.db import models

from core.models import Application, Candidate


def resume_upload_path(instance, filename):
    return f'resumes/{instance.candidate.id}/{filename}'

class Resume(models.Model):
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
        ('auto', 'Автоопределение'),
    ]
    
    STATUS_CHOICES = [
        ('uploaded', 'Загружено'),
        ('processing', 'Обрабатывается'),
        ('processed', 'Обработано'),
        ('error', 'Ошибка'),
    ]
    
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, verbose_name="Кандидат")
    application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Заявка")
    
    # Файл резюме
    file = models.FileField(
        upload_to=resume_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx'])],
        verbose_name="Файл резюме"
    )
    original_filename = models.CharField(max_length=255, verbose_name="Оригинальное имя файла")
    file_size = models.PositiveIntegerField(verbose_name="Размер файла (байты)")
    
    # Извлеченная информация
    extracted_text = models.TextField(blank=True, verbose_name="Извлеченный текст")
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='auto', verbose_name="Язык")
    
    # Структурированная информация
    skills = models.JSONField(default=list, verbose_name="Навыки")
    experience_years = models.PositiveIntegerField(null=True, blank=True, verbose_name="Опыт (лет)")
    education = models.JSONField(default=list, verbose_name="Образование")
    work_experience = models.JSONField(default=list, verbose_name="Опыт работы")
    
    # AI анализ
    text_embedding = models.JSONField(null=True, blank=True, verbose_name="Text Embedding")
    skills_embedding = models.JSONField(null=True, blank=True, verbose_name="Skills Embedding")
    
    # Метаданные
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded', verbose_name="Статус")
    processing_error = models.TextField(blank=True, verbose_name="Ошибка обработки")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Резюме"
        verbose_name_plural = "Резюме"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Резюме {self.candidate.full_name} - {self.original_filename}"
    
    def delete(self, *args, **kwargs):
        # Удаляем файл при удалении записи
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)
    
    @property
    def file_extension(self):
        return os.path.splitext(self.original_filename)[1].lower()
    
    @property
    def is_pdf(self):
        return self.file_extension == '.pdf'
    
    @property
    def is_docx(self):
        return self.file_extension == '.docx'

class ResumeAnalysis(models.Model):
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, verbose_name="Резюме")
    
    # Анализ контента
    key_skills = models.JSONField(default=list, verbose_name="Ключевые навыки")
    experience_summary = models.TextField(blank=True, verbose_name="Краткое описание опыта")
    education_level = models.CharField(max_length=100, blank=True, verbose_name="Уровень образования")
    
    # Качественные метрики
    completeness_score = models.FloatField(default=0.0, verbose_name="Полнота резюме")
    relevance_keywords = models.JSONField(default=list, verbose_name="Релевантные ключевые слова")
    
    # Временные метки
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Анализ резюме"
        verbose_name_plural = "Анализы резюме"
    
    def __str__(self):
        return f"Анализ резюме {self.resume.candidate.full_name}"
