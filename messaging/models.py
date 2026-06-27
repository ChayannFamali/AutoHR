"""Модели чата MVP (Этап 3.7).

Conversation — переписка между двумя пользователями (HR ↔ кандидат),
опционально привязанная к вакансии.
Message — отдельное сообщение в рамках Conversation.
"""
from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """Переписка между двумя участниками (опц. — по вакансии)."""

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        verbose_name="Участники",
    )
    related_job = models.ForeignKey(
        'core.Job',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='conversations',
        verbose_name="Вакансия (опц.)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Переписка"
        verbose_name_plural = "Переписки"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
        ]

    def __str__(self):
        names = ', '.join(
            u.get_full_name() or u.username
            for u in self.participants.all()
        )
        return f"#{self.id} ({names})"

    @property
    def last_message(self):
        return self.messages.order_by('-created_at').first()

    def unread_count_for(self, user):
        return self.messages.filter(read_at__isnull=True).exclude(sender=user).count()

    @classmethod
    def get_or_create_between(cls, user1, user2, job=None):
        """Найти или создать переписку между двумя пользователями.

        - Если job передан → ищем переписку по этой вакансии.
        - Если job не передан → ищем «общую» переписку (без привязки к вакансии).
        """
        qs = cls.objects.filter(participants=user1).filter(participants=user2)
        if job is not None:
            qs = qs.filter(related_job=job)
        else:
            qs = qs.filter(related_job__isnull=True)
        existing = qs.first()
        if existing:
            return existing, False
        conv = cls.objects.create(related_job=job)
        conv.participants.add(user1, user2)
        return conv, True


class Message(models.Model):
    """Сообщение в переписке (Этап 3.7)."""

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Переписка",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name="Отправитель",
    )
    body = models.TextField(verbose_name="Текст сообщения")
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Прочитано",
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f"{self.sender.username}: {self.body[:50]}"

    def mark_read(self):
        if not self.read_at:
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])
