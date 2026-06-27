from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Application, Candidate, Company, Job

User = get_user_model()


class FunnelTests(TestCase):
    """Тесты Этапа 3.6: расширенная аналитика."""

    def setUp(self):
        self.hr = User.objects.create_user(
            username='hr_an', password='pw1234567', user_type='hr',
        )
        self.company = Company.objects.create(name='Acme')
        self.job = Job.objects.create(
            title='Backend', company=self.company, description='d',
            requirements='r', experience_level='middle', location='M',
            views_count=10, created_by=self.hr,
        )

    def _make_candidate(self, idx):
        u = User.objects.create_user(
            username=f'cand_{idx}', password='pw1234567',
            user_type='candidate', email=f'c_{idx}@example.com',
        )
        return Candidate.objects.create(
            user=u, first_name=f'C{idx}', last_name=f'L{idx}',
            email=f'c_{idx}@example.com',
        )

    def _create_app(self, candidate, status='pending', days_ago=0):
        applied = timezone.now() - timedelta(days=days_ago)
        app = Application.objects.create(
            candidate=candidate, job=self.job, status=status,
        )
        if status in ('approved', 'interviewed'):
            app.applied_at = applied
            app.processed_at = applied + timedelta(days=3)
            app.save()
        return app

    def test_recruitment_funnel_200(self):
        self._create_app(self._make_candidate(1), 'pending')
        self._create_app(self._make_candidate(2), 'approved')
        self._create_app(self._make_candidate(3), 'interviewed')
        response = self.client.get(reverse('analytics:recruitment_funnel'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['labels']), 5)
        self.assertEqual(len(data['data']), 5)
        self.assertEqual(data['data'][0], 10)
        self.assertEqual(data['data'][1], 3)
        self.assertEqual(data['data'][2], 1)
        self.assertEqual(data['data'][3], 1)

    def test_conversion_rates_zero_views(self):
        self.job.views_count = 0
        self.job.save(update_fields=['views_count'])
        self._create_app(self._make_candidate(1), 'approved')
        response = self.client.get(reverse('analytics:conversion_rates'))
        data = response.json()
        self.assertEqual(data['data'][0], 0.0)

    def test_conversion_rates(self):
        self.job.views_count = 100
        self.job.save(update_fields=['views_count'])
        # 10 откликов: 8 pending, 1 approved, 1 interviewed
        for i in range(8):
            self._create_app(self._make_candidate(i), 'pending')
        self._create_app(self._make_candidate(8), 'approved')
        self._create_app(self._make_candidate(9), 'interviewed')

        response = self.client.get(reverse('analytics:conversion_rates'))
        data = response.json()
        self.assertEqual(data['data'][0], 10.0)
        self.assertEqual(data['data'][1], 10.0)
        self.assertEqual(data['data'][2], 100.0)

    def test_time_to_hire_no_data(self):
        response = self.client.get(reverse('analytics:time_to_hire'))
        data = response.json()
        self.assertIsNone(data['avg_days'])
        self.assertEqual(data['sample_size'], 0)

    def test_time_to_hire_calculates(self):
        applied = timezone.now() - timedelta(days=10)
        candidate = self._make_candidate(1)
        app = Application.objects.create(
            candidate=candidate, job=self.job, status='approved',
        )
        app.applied_at = applied
        app.processed_at = applied + timedelta(days=3)
        app.save()

        response = self.client.get(reverse('analytics:time_to_hire'))
        data = response.json()
        self.assertEqual(data['avg_days'], 3.0)
        self.assertEqual(data['sample_size'], 1)

    def test_top_employers(self):
        for i in range(3):
            self._create_app(self._make_candidate(i), 'pending')

        response = self.client.get(reverse('analytics:top_employers'))
        data = response.json()
        self.assertEqual(data['labels'][0], 'Acme')
        self.assertEqual(data['jobs_data'][0], 1)
        self.assertEqual(data['apps_data'][0], 3)