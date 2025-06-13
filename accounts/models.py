from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USER_TYPES = [
        ('hr', 'HR специалист'),
        ('candidate', 'Кандидат'),
        ('admin', 'Администратор'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='candidate')
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    company = models.CharField(max_length=200, blank=True, verbose_name="Компания")
    position = models.CharField(max_length=200, blank=True, verbose_name="Должность")
    is_verified = models.BooleanField(default=False, verbose_name="Подтвержден")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
    
    def is_hr(self):
        return self.user_type == 'hr'
    
    def is_candidate(self):
        return self.user_type == 'candidate'
    
    def is_admin_user(self):
        return self.user_type == 'admin' or self.is_superuser

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, verbose_name="О себе")
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn")
    github_url = models.URLField(blank=True, verbose_name="GitHub")
    website = models.URLField(blank=True, verbose_name="Веб-сайт")
    location = models.CharField(max_length=200, blank=True, verbose_name="Местоположение")
    skills = models.JSONField(default=list, blank=True, verbose_name="Навыки")
    experience_years = models.PositiveIntegerField(null=True, blank=True, verbose_name="Опыт (лет)")
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
    
    def __str__(self):
        return f"Профиль {self.user.get_full_name()}"
