import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from core.models import Application, Candidate


class InterviewType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    duration_minutes = models.PositiveIntegerField(default=60, verbose_name="Длительность (мин)")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    class Meta:
        verbose_name = "Тип собеседования"
        verbose_name_plural = "Типы собеседований"
    
    def __str__(self):
        return self.name

class Interview(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Запланировано'),
        ('confirmed', 'Подтверждено'),
        ('in_progress', 'В процессе'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
        ('no_show', 'Не явился'),
    ]
    
    FORMAT_CHOICES = [
        ('online', 'Онлайн'),
        ('offline', 'Офлайн'),
        ('phone', 'Телефон'),
    ]
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, verbose_name="Заявка")
    interview_type = models.ForeignKey(InterviewType, on_delete=models.CASCADE, verbose_name="Тип собеседования")
    
    interviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Интервьюер")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, verbose_name="Кандидат")
    
    scheduled_at = models.DateTimeField(verbose_name="Запланировано на")
    duration_minutes = models.PositiveIntegerField(default=60, verbose_name="Длительность (мин)")
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, verbose_name="Формат")
    location = models.CharField(max_length=200, blank=True, verbose_name="Место/Ссылка")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="Статус")
    notes = models.TextField(blank=True, verbose_name="Заметки")
    preparation_notes = models.TextField(blank=True, verbose_name="Заметки для подготовки")
    
    feedback = models.TextField(blank=True, verbose_name="Обратная связь")
    rating = models.PositiveIntegerField(
        null=True, 
        blank=True,
        choices=[(i, str(i)) for i in range(1, 6)],
        verbose_name="Оценка (1-5)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Собеседование"
        verbose_name_plural = "Собеседования"
        ordering = ['scheduled_at']
    
    def __str__(self):
        return f"{self.candidate.full_name} - {self.scheduled_at.strftime('%d.%m.%Y %H:%M')}"
    
    def clean(self):
        if self.scheduled_at and self.scheduled_at < timezone.now():
            raise ValidationError("Нельзя запланировать собеседование в прошлом")
    
    @property
    def end_time(self):
        return self.scheduled_at + datetime.timedelta(minutes=self.duration_minutes)

class InterviewAvailability(models.Model):
    WEEKDAY_CHOICES = [
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    ]
    
    interviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Интервьюер")
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, verbose_name="День недели")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    
    class Meta:
        verbose_name = "Доступность для собеседований"
        verbose_name_plural = "Доступности для собеседований"
        unique_together = ['interviewer', 'weekday', 'start_time', 'end_time']
    
    def __str__(self):
        return f"{self.interviewer.get_full_name()} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Время начала должно быть раньше времени окончания")

class InterviewTimeSlot(models.Model):
    interviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Интервьюер")
    date = models.DateField(verbose_name="Дата")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    is_booked = models.BooleanField(default=False, verbose_name="Забронировано")
    interview = models.OneToOneField(Interview, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Собеседование")
    
    class Meta:
        verbose_name = "Временной слот"
        verbose_name_plural = "Временные слоты"
        unique_together = ['interviewer', 'date', 'start_time']
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.interviewer.get_full_name()} - {self.date} {self.start_time}-{self.end_time}"
