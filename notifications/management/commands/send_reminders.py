from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from calendar_app.models import Interview
from notifications.services import NotificationService


class Command(BaseCommand):
    help = 'Send interview reminders'
    
    def handle(self, *args, **options):
        # Находим собеседования на завтра
        tomorrow = timezone.now() + timedelta(days=1)
        tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        interviews = Interview.objects.filter(
            scheduled_at__range=[tomorrow_start, tomorrow_end],
            status='confirmed'
        )
        
        sent_count = 0
        for interview in interviews:
            # Проверяем, не отправляли ли уже напоминание
            from notifications.models import Notification
            existing_reminder = Notification.objects.filter(
                candidate=interview.candidate,
                notification_type__code='interview_reminder',
                content_type__model='interview',
                object_id=interview.id
            ).exists()
            
            if not existing_reminder:
                if NotificationService.send_interview_reminder(interview):
                    sent_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {sent_count} interview reminders')
        )
