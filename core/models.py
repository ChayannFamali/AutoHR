from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class Company(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название компании")
    slug = models.SlugField(
        max_length=220, unique=True, blank=True,
        verbose_name="URL-идентификатор",
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    website = models.URLField(blank=True, verbose_name="Веб-сайт")
    logo = models.ImageField(
        upload_to='company_logos/', blank=True, null=True,
        verbose_name="Логотип",
    )
    industry = models.CharField(
        max_length=100, blank=True, verbose_name="Отрасль",
    )
    employee_count = models.CharField(
        max_length=50, blank=True, verbose_name="Размер компании",
        help_text="Например: 1-50, 50-200, 200-1000, 1000+",
    )
    founded_year = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Год основания",
    )
    address = models.CharField(
        max_length=300, blank=True, verbose_name="Адрес",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or 'company'
            slug = base
            i = 1
            while Company.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        avg = self.reviews.aggregate(avg=models.Avg('rating'))['avg']
        return round(avg, 1) if avg else None

    @property
    def reviews_count(self):
        return self.reviews.count()

    @property
    def active_jobs_count(self):
        return self.job_set.filter(status='active').count()


class CompanyReview(models.Model):
    """Отзыв кандидата/HR о компании."""

    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Компания",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='company_reviews',
        verbose_name="Автор",
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оценка",
    )
    title = models.CharField(
        max_length=200, blank=True, verbose_name="Заголовок отзыва",
    )
    text = models.TextField(verbose_name="Текст отзыва")
    pros = models.TextField(blank=True, verbose_name="Плюсы")
    cons = models.TextField(blank=True, verbose_name="Минусы")
    is_anonymous = models.BooleanField(
        default=False, verbose_name="Анонимный отзыв",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Отзыв о компании"
        verbose_name_plural = "Отзывы о компаниях"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', '-created_at']),
        ]

    def __str__(self):
        author = 'Аноним' if self.is_anonymous or not self.author else (
            self.author.get_full_name() or self.author.username
        )
        return f"{author} → {self.company.name} ({self.rating}/5)"

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

    EMPLOYMENT_CHOICES = [
        ('full_time', 'Полная занятость'),
        ('part_time', 'Частичная занятость'),
        ('internship', 'Стажировка'),
        ('project', 'Проектная работа'),
        ('remote', 'Удалённо'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название вакансии")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Компания")
    description = models.TextField(verbose_name="Описание вакансии")
    requirements = models.TextField(verbose_name="Требования")
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, verbose_name="Уровень опыта")
    employment_type = models.CharField(
        max_length=20, choices=EMPLOYMENT_CHOICES,
        default='full_time', verbose_name="Тип занятости",
    )
    salary_min = models.PositiveIntegerField(null=True, blank=True, verbose_name="Зарплата от")
    salary_max = models.PositiveIntegerField(null=True, blank=True, verbose_name="Зарплата до")
    location = models.CharField(max_length=200, verbose_name="Локация")
    remote_work = models.BooleanField(default=False, verbose_name="Удаленная работа")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Статус")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Создано пользователем")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0, verbose_name="Количество просмотров")
    # Поля для AI анализа
    requirements_embedding = models.JSONField(null=True, blank=True, verbose_name="Embedding требований")
    skills_required = models.JSONField(
        default=list, blank=True,
        verbose_name="Ключевые навыки (теги)",
        help_text="Список строк, например: ['Python', 'Django']",
    )

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.company.name}"


class Candidate(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name="Пользователь"
    )
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
    notes = models.TextField(blank=True, null=True, verbose_name="Заметки HR")
    ai_score = models.FloatField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="AI оценка"
    )
    ai_feedback = models.TextField(blank=True, verbose_name="AI отзыв")
    applied_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        unique_together = ['candidate', 'job']
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.candidate.full_name} -> {self.job.title}"


class SavedJob(models.Model):
    """Вакансия, добавленная пользователем в избранное."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_jobs',
        verbose_name="Пользователь",
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='saved_by',
        verbose_name="Вакансия",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Добавлено")

    class Meta:
        verbose_name = "Избранная вакансия"
        verbose_name_plural = "Избранные вакансии"
        unique_together = ['user', 'job']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.job.title}"


class SavedSearch(models.Model):
    """Сохранённый поисковый запрос с параметрами фильтрации."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_searches',
        verbose_name="Пользователь",
    )
    name = models.CharField(max_length=200, verbose_name="Название поиска")
    params = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Параметры (search, experience_level, remote_work, ...)",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    last_used_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Последнее использование"
    )

    class Meta:
        verbose_name = "Сохранённый поиск"
        verbose_name_plural = "Сохранённые поиски"
        ordering = ['-last_used_at', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class WorkExperience(models.Model):
    """Место работы кандидата (Этап 3.2)."""

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='work_experiences',
        verbose_name="Кандидат",
    )
    company = models.CharField(max_length=200, verbose_name="Компания")
    position = models.CharField(max_length=200, verbose_name="Должность")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(
        null=True, blank=True, verbose_name="Дата окончания",
        help_text="Оставьте пустым, если работаете здесь сейчас",
    )
    is_current = models.BooleanField(
        default=False, verbose_name="Текущее место работы",
    )
    description = models.TextField(
        blank=True, verbose_name="Обязанности и достижения",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Опыт работы"
        verbose_name_plural = "Опыт работы"
        ordering = ['-is_current', '-start_date']
        indexes = [
            models.Index(fields=['candidate', '-start_date']),
        ]

    def __str__(self):
        end = 'настоящее время' if self.is_current else (
            self.end_date.strftime('%m.%Y') if self.end_date else '—'
        )
        return f"{self.position} @ {self.company} ({end})"


class Education(models.Model):
    """Образование кандидата (Этап 3.2)."""

    DEGREE_CHOICES = [
        ('secondary', 'Среднее'),
        ('vocational', 'Среднее профессиональное'),
        ('bachelor', 'Бакалавр'),
        ('master', 'Магистр'),
        ('phd', 'Кандидат/Доктор наук'),
        ('courses', 'Курсы'),
        ('certification', 'Сертификация'),
    ]

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='educations',
        verbose_name="Кандидат",
    )
    institution = models.CharField(
        max_length=300, verbose_name="Учебное заведение",
    )
    degree = models.CharField(
        max_length=30, choices=DEGREE_CHOICES,
        default='bachelor', verbose_name="Степень",
    )
    field_of_study = models.CharField(
        max_length=200, blank=True, verbose_name="Специальность",
    )
    start_year = models.PositiveIntegerField(verbose_name="Год начала")
    end_year = models.PositiveIntegerField(verbose_name="Год окончания")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Образование"
        verbose_name_plural = "Образование"
        ordering = ['-end_year']
        indexes = [
            models.Index(fields=['candidate', '-end_year']),
        ]

    def __str__(self):
        return f"{self.institution} ({self.start_year}–{self.end_year})"


class Skill(models.Model):
    """Навык кандидата с уровнем владения (Этап 3.2)."""

    LEVEL_CHOICES = [
        ('beginner', 'Начальный'),
        ('intermediate', 'Средний'),
        ('expert', 'Продвинутый'),
    ]

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='skills',
        verbose_name="Кандидат",
    )
    name = models.CharField(max_length=100, verbose_name="Навык")
    level = models.CharField(
        max_length=20, choices=LEVEL_CHOICES,
        default='intermediate', verbose_name="Уровень",
    )
    years_of_experience = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Опыт (лет)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"
        ordering = ['name']
        unique_together = ['candidate', 'name']
        indexes = [
            models.Index(fields=['candidate', 'name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"

    @property
    def level_color(self):
        return {
            'beginner': 'info',
            'intermediate': 'warning',
            'expert': 'success',
        }.get(self.level, 'secondary')
