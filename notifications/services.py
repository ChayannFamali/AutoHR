import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Notification, NotificationTemplate, NotificationType

logger = logging.getLogger(__name__)

class NotificationService:
    
    @staticmethod
    def send_application_confirmation(application):
        """Уведомление кандидату о получении заявки"""
        try:
            # Простая отправка без создания записи в БД (пока нет типов уведомлений)
            send_mail(
                subject=f'Заявка на вакансию "{application.job.title}" получена',
                message=f'Здравствуйте, {application.candidate.full_name}!\n\n'
                       f'Ваша заявка на вакансию "{application.job.title}" в компании {application.job.company.name} получена и будет рассмотрена.\n\n'
                       f'Мы свяжемся с вами в ближайшее время.\n\n'
                       f'С уважением,\nКоманда AutoHR',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.candidate.email],
                fail_silently=True,
            )
            
            logger.info(f'Application confirmation sent to {application.candidate.email}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send application confirmation: {str(e)}')
            return False
    
    @staticmethod
    def send_interview_scheduled(interview):
        """Уведомление кандидату о назначенном собеседовании"""
        try:
            send_mail(
                subject=f'Собеседование назначено - {interview.application.job.title}',
                message=f'Здравствуйте, {interview.candidate.full_name}!\n\n'
                       f'Мы рады сообщить, что вас приглашают на собеседование по вакансии "{interview.application.job.title}".\n\n'
                       f'Детали собеседования:\n'
                       f'📅 Дата: {interview.scheduled_at.strftime("%d.%m.%Y")}\n'
                       f'⏰ Время: {interview.scheduled_at.strftime("%H:%M")}\n'
                       f'📍 Формат: {interview.get_format_display()}\n'
                       f'👤 Интервьюер: {interview.interviewer.get_full_name()}\n'
                       f'⏱️ Длительность: {interview.duration_minutes} минут\n'
                       + (f'📍 Место: {interview.location}\n' if interview.location else '') +
                       f'\nПожалуйста, подтвердите ваше участие.\n\n'
                       f'С уважением,\nКоманда AutoHR',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[interview.candidate.email],
                fail_silently=True,
            )
            
            logger.info(f'Interview notification sent to {interview.candidate.email}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send interview notification: {str(e)}')
            return False
    
    @staticmethod
    def send_hr_notification(title, message, user_email):
        """Уведомление HR специалисту"""
        try:
            send_mail(
                subject=f'AutoHR: {title}',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=True,
            )
            return True
        except Exception as e:
            logger.error(f'Failed to send HR notification: {str(e)}')
            return False

    @staticmethod
    def send_interview_reminder(interview):
        """Напоминание кандидату о предстоящем собеседовании"""
        try:
            send_mail(
                subject=f'Напоминание о собеседовании - {interview.scheduled_at.strftime("%d.%m.%Y в %H:%M")}',
                message=(
                    f'Здравствуйте, {interview.candidate.first_name}!\n\n'
                    f'Напоминаем вам о предстоящем собеседовании:\n\n'
                    f'📅 Дата: {interview.scheduled_at.strftime("%d.%m.%Y")}\n'
                    f'⏰ Время: {interview.scheduled_at.strftime("%H:%M")}\n'
                    f'💼 Вакансия: {interview.application.job.title}\n'
                    f'👤 Интервьюер: {interview.interviewer.get_full_name()}\n'
                    f'📍 Формат: {interview.get_format_display()}\n'
                    + (f'🔗 Место/Ссылка: {interview.location}\n' if interview.location else '') +
                    f'\nЖдём вас!\n\n'
                    f'С уважением,\nКоманда AutoHR'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[interview.candidate.email],
                fail_silently=True,
            )

            logger.info(f'Interview reminder sent to {interview.candidate.email}')
            return True

        except Exception as e:
            logger.error(f'Failed to send interview reminder: {str(e)}')
            return False
