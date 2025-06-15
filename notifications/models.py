from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from calendar_app.models import Interview
from core.models import Candidate


class NotificationType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    code = models.CharField(max_length=50, unique=True, verbose_name="Код")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    email_subject_template = models.CharField(max_length=200, blank=True, verbose_name="Шаблон темы email")
    email_body_template = models.TextField(blank=True, verbose_name="Шаблон тела email")
    sms_template = models.TextField(blank=True, verbose_name="Шаблон SMS")
    
    class Meta:
        verbose_name = "Тип уведомления"
        verbose_name_plural = "Типы уведомлений"
    
    def __str__(self):
        return self.name

class Notification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает отправки'),
        ('sent', 'Отправлено'),
        ('delivered', 'Доставлено'),
        ('failed', 'Ошибка'),
        ('cancelled', 'Отменено'),
    ]
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_app', 'В приложении'),
        ('push', 'Push уведомление'),
    ]
    
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE, verbose_name="Тип уведомления")
    
    # Получатели
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Пользователь")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Кандидат")
    email = models.EmailField(blank=True, verbose_name="Email получателя")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон получателя")
    
    # Связанный объект (полиморфная связь)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, verbose_name="Канал")
    subject = models.CharField(max_length=200, blank=True, verbose_name="Тема")
    message = models.TextField(verbose_name="Сообщение")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name="Запланировано на")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Отправлено в")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Доставлено в")
    
    # Ошибки и повторы
    error_message = models.TextField(blank=True, verbose_name="Сообщение об ошибке")
    retry_count = models.PositiveIntegerField(default=0, verbose_name="Количество повторов")
    max_retries = models.PositiveIntegerField(default=3, verbose_name="Максимум повторов")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-created_at']
    
    def __str__(self):
        recipient = self.user or self.candidate or self.email
        return f"{self.notification_type.name} -> {recipient}"

class NotificationTemplate(models.Model):
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
    ]
    
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE, verbose_name="Тип уведомления")
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='ru', verbose_name="Язык")
    channel = models.CharField(max_length=20, choices=Notification.CHANNEL_CHOICES, verbose_name="Канал")
    
    subject_template = models.CharField(max_length=200, blank=True, verbose_name="Шаблон темы")
    body_template = models.TextField(verbose_name="Шаблон сообщения")
    
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Шаблон уведомления"
        verbose_name_plural = "Шаблоны уведомлений"
        unique_together = ['notification_type', 'language', 'channel']
    
    def __str__(self):
        return f"{self.notification_type.name} - {self.get_language_display()} ({self.get_channel_display()})"

class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    
    # Предпочтения по каналам
    email_enabled = models.BooleanField(default=True, verbose_name="Email уведомления")
    sms_enabled = models.BooleanField(default=False, verbose_name="SMS уведомления")
    in_app_enabled = models.BooleanField(default=True, verbose_name="Уведомления в приложении")
    
    new_application_email = models.BooleanField(default=True, verbose_name="Новая заявка (Email)")
    interview_reminder_email = models.BooleanField(default=True, verbose_name="Напоминание о собеседовании (Email)")
    interview_reminder_sms = models.BooleanField(default=False, verbose_name="Напоминание о собеседовании (SMS)")
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Настройки уведомлений"
        verbose_name_plural = "Настройки уведомлений"
    
    def __str__(self):
        return f"Настройки уведомлений {self.user.get_full_name()}"
