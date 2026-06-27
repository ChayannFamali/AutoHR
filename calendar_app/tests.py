from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from calendar_app.models import Interview, InterviewType
from core.models import Application, Candidate, Company, Job

User = get_user_model()


class InterviewListSmokeTests(TestCase):
    """Регрессионный тест бага Этапа 1.9: один URL → один обработчик."""

    def setUp(self):
        self.hr = User.objects.create_user(
            username='hr', password='pw1234567', user_type='hr'
        )

    def test_interview_list_url_resolves_to_class(self):
        """URL calendar_app:interview_list должен резолвиться."""
        url = reverse('calendar_app:interview_list')
        self.assertTrue(url)

    def test_interview_list_requires_login(self):
        url = reverse('calendar_app:interview_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_interview_list_hr_accessible(self):
        self.client.login(username='hr', password='pw1234567')
        url = reverse('calendar_app:interview_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class SendReminderViewTests(TestCase):
    """Регрессионный тест Этапа 1.2: send_interview_reminder view делегирует в сервис."""

    def setUp(self):
        self.hr = User.objects.create_user(
            username='hr', password='pw1234567', user_type='hr',
            email='hr@example.com'
        )
        self.candidate_user = User.objects.create_user(
            username='cand', password='pw1234567', user_type='candidate',
            email='cand@example.com'
        )
        self.candidate = Candidate.objects.create(
            user=self.candidate_user, first_name='Иван', last_name='Иванов',
            email='cand@example.com'
        )
        company = Company.objects.create(name='Acme')
        self.job = Job.objects.create(
            title='Dev', company=company, description='', requirements='',
            experience_level='middle', location='Moscow',
            created_by=self.hr,
        )
        self.application = Application.objects.create(
            candidate=self.candidate, job=self.job
        )
        self.interview_type = InterviewType.objects.create(
            name='Standard', duration_minutes=60
        )
        self.interview = Interview.objects.create(
            application=self.application,
            candidate=self.candidate,
            interviewer=self.hr,
            interview_type=self.interview_type,
            scheduled_at=timezone.now() + timedelta(days=1),
            format='online',
            status='scheduled',
        )

    def test_send_reminder_view_hr(self):
        import json
        self.client.login(username='hr', password='pw1234567')
        url = reverse('calendar_app:send_reminder', kwargs={'interview_id': self.interview.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get('success'))