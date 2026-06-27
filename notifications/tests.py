from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from calendar_app.models import Interview, InterviewType
from core.models import Application, Candidate, Company, Job

User = get_user_model()


class SendRemindersCommandTests(TestCase):
    """Регрессионный тест бага Этапа 1.2: management-команда send_reminders не падает."""

    def setUp(self):
        self.company = Company.objects.create(name='Acme')
        self.job = Job.objects.create(
            title='Dev', company=self.company, description='', requirements='',
            experience_level='middle', location='Moscow',
            created_by=User.objects.create_user(username='hr', user_type='hr'),
        )
        self.candidate_user = User.objects.create_user(
            username='cand', password='pw', user_type='candidate',
            email='cand@example.com',
        )
        self.candidate = Candidate.objects.create(
            user=self.candidate_user, first_name='Иван', last_name='Иванов',
            email='cand@example.com',
        )
        self.application = Application.objects.create(
            candidate=self.candidate, job=self.job
        )
        self.interview_type = InterviewType.objects.create(
            name='Standard', duration_minutes=60
        )
        self.interviewer = User.objects.create_user(
            username='int', password='pw', user_type='hr'
        )

    def test_send_reminders_does_not_crash_on_empty(self):
        """Команда должна корректно работать без собеседований."""
        try:
            call_command('send_reminders')
        except AttributeError as e:
            self.fail(f'send_reminders упал с AttributeError: {e}')

    def test_send_reminders_with_confirmed_interview_tomorrow(self):
        tomorrow = timezone.now() + timedelta(days=1)
        Interview.objects.create(
            application=self.application,
            candidate=self.candidate,
            interviewer=self.interviewer,
            interview_type=self.interview_type,
            scheduled_at=tomorrow.replace(hour=10, minute=0, second=0, microsecond=0),
            format='online',
            status='confirmed',
        )

        try:
            call_command('send_reminders')
        except AttributeError as e:
            self.fail(
                f'send_reminders упал с AttributeError при наличии собеседования: {e}'
            )