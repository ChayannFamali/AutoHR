from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название компании")
    description = models.TextField(blank=True, verbose_name="Описание")
    website = models.URLField(blank=True, verbose_name="Веб-сайт")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"
    
    def __str__(self):
        return self.name

class Job(models.Model):
    EXPERIENCE_CHOICES = [
        ('junior', 'Junior (0-2 года)'),
        ('middle', 'Middle (2-5 лет)'),
        ('senior', 'Senior (5+ лет)'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Активная'),
        ('paused', 'Приостановлена'),
        ('closed', 'Закрыта'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Название вакансии")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Компания")
    description = models.TextField(verbose_name="Описание вакансии")
    requirements = models.TextField(verbose_name="Требования")
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, verbose_name="Уровень опыта")
    salary_min = models.PositiveIntegerField(null=True, blank=True, verbose_name="Зарплата от")
    salary_max = models.PositiveIntegerField(null=True, blank=True, verbose_name="Зарплата до")
    location = models.CharField(max_length=200, verbose_name="Локация")
    remote_work = models.BooleanField(default=False, verbose_name="Удаленная работа")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Статус")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Создано пользователем")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Поля для AI анализа
    requirements_embedding = models.JSONField(null=True, blank=True, verbose_name="Embedding требований")
    
    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.company.name}"

class Candidate(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn")
    location = models.CharField(max_length=200, blank=True, verbose_name="Местоположение")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Кандидат"
        verbose_name_plural = "Кандидаты"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('processing', 'Обрабатывается'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
        ('interviewed', 'Прошел собеседование'),
    ]
    
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, verbose_name="Кандидат")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name="Вакансия")
    cover_letter = models.TextField(blank=True, verbose_name="Сопроводительное письмо")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    ai_score = models.FloatField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="AI оценка"
    )
    ai_feedback = models.TextField(blank=True, verbose_name="AI отзыв")
    hr_notes = models.TextField(blank=True, verbose_name="Заметки HR")
    applied_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        unique_together = ['candidate', 'job']
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.candidate.full_name} -> {self.job.title}"
