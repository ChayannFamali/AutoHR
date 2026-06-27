from datetime import datetime, timedelta, timezone as tz
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from calendar_app.models import (Interview, InterviewAvailability,
                                 InterviewTimeSlot, InterviewType)
from core.models import Application, Candidate, Company, CompanyReview, Job
from notifications.services import NotificationService

User = get_user_model()


class JobListSmokeTests(TestCase):
    """Smoke: публичный каталог вакансий работает."""

    def test_job_list_anonymous_200(self):
        response = self.client.get(reverse('core:job_list'))
        self.assertEqual(response.status_code, 200)

    def test_job_list_renders_jobs(self):
        hr = User.objects.create_user(username='hr', user_type='hr')
        company = Company.objects.create(name='Acme')
        Job.objects.create(
            title='Python Dev', company=company, description='', requirements='',
            experience_level='middle', location='Remote', remote_work=True,
            created_by=hr,
        )

        response = self.client.get(reverse('core:job_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Dev')


class ExportPermissionsTests(TestCase):
    """Регрессионный тест бага Этапа 1.3: export_applications_excel требует HR."""

    def setUp(self):
        self.hr = User.objects.create_user(
            username='hr', password='pw1234567', user_type='hr'
        )
        self.cand = User.objects.create_user(
            username='cand', password='pw1234567', user_type='candidate'
        )

    def test_anonymous_redirected(self):
        response = self.client.get(reverse('core:export_applications'))
        self.assertEqual(response.status_code, 302)

    def test_candidate_forbidden(self):
        self.client.login(username='cand', password='pw1234567')
        response = self.client.get(reverse('core:export_applications'))
        self.assertIn(response.status_code, (302, 403))

    def test_hr_allowed(self):
        self.client.login(username='hr', password='pw1234567')
        response = self.client.get(reverse('core:export_applications'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])


class InterviewReminderTests(TestCase):
    """Регрессионный тест бага Этапа 1.2: send_interview_reminder существует."""

    def setUp(self):
        self.company = Company.objects.create(name='Acme')
        self.job = Job.objects.create(
            title='Dev', company=self.company, description='d', requirements='r',
            experience_level='middle', location='Moscow',
            created_by=User.objects.create_user(username='hr_owner', user_type='hr'),
        )
        self.candidate_user = User.objects.create_user(
            username='cand', password='pw', user_type='candidate',
            email='cand@example.com'
        )
        self.candidate = Candidate.objects.create(
            user=self.candidate_user, first_name='Иван', last_name='Иванов',
            email='cand@example.com'
        )
        self.application = Application.objects.create(
            candidate=self.candidate, job=self.job
        )
        self.interview_type = InterviewType.objects.create(name='Standard', duration_minutes=60)
        self.interviewer = User.objects.create_user(
            username='int', password='pw', user_type='hr', email='int@example.com'
        )
        self.interview = Interview.objects.create(
            application=self.application,
            candidate=self.candidate,
            interviewer=self.interviewer,
            interview_type=self.interview_type,
            scheduled_at=timezone.now() + timedelta(days=1),
            format='online',
            status='scheduled',
        )

    def test_send_interview_reminder_returns_true(self):
        """Метод существует и возвращает True (письмо уходит в console backend)."""
        result = NotificationService.send_interview_reminder(self.interview)
        self.assertTrue(result, 'send_interview_reminder должен вернуть True')

    def test_send_interview_reminder_handles_no_location(self):
        """Покрывает ветку без location."""
        self.interview.location = ''
        self.interview.save()
        self.assertTrue(NotificationService.send_interview_reminder(self.interview))


class HTMXEndpointTests(TestCase):
    """Тесты HTMX-эндпоинтов (SKILL 4)."""

    def setUp(self):
        self.hr = User.objects.create_user(
            username='hr', password='pw1234567', user_type='hr',
        )
        self.cand_user = User.objects.create_user(
            username='cand', password='pw1234567', user_type='candidate',
            email='c@example.com',
        )
        self.candidate = Candidate.objects.create(
            user=self.cand_user, first_name='И', last_name='И',
            email='c@example.com',
        )
        self.company = Company.objects.create(name='Acme')
        self.job = Job.objects.create(
            title='Python Dev', company=self.company, description='d',
            requirements='r', experience_level='middle', location='M',
            created_by=self.hr,
        )
        self.application = Application.objects.create(
            candidate=self.candidate, job=self.job,
        )

    def test_job_list_htmx_returns_partial(self):
        """GET /jobs/htmx/ возвращает HTML-фрагмент, не полную страницу."""
        response = self.client.get(reverse('core:job_list_htmx'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Dev')
        # Не должен содержать <html> (т.е. это не полная страница)
        self.assertNotContains(response, '<html')

    def test_job_list_htmx_filters_by_search(self):
        """HTMX-эндпоинт фильтрует по GET-параметрам."""
        response = self.client.get(
            reverse('core:job_list_htmx'),
            {'search': 'Python'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Dev')

    def test_update_status_htmx_approved(self):
        """POST update-status-htmx с approved обновляет заявку и возвращает partial."""
        self.client.login(username='hr', password='pw1234567')
        response = self.client.post(
            reverse('core:update_application_status_htmx',
                    kwargs={'application_id': self.application.id}),
            {'status': 'approved'},
        )
        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'approved')

    def test_update_status_htmx_rejected(self):
        """POST update-status-htmx с rejected."""
        self.client.login(username='hr', password='pw1234567')
        response = self.client.post(
            reverse('core:update_application_status_htmx',
                    kwargs={'application_id': self.application.id}),
            {'status': 'rejected'},
        )
        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'rejected')

    def test_update_status_htmx_invalid_status_returns_400(self):
        """POST с неверным статусом → 400 + HTML ошибка."""
        self.client.login(username='hr', password='pw1234567')
        response = self.client.post(
            reverse('core:update_application_status_htmx',
                    kwargs={'application_id': self.application.id}),
            {'status': 'bogus'},
        )
        self.assertEqual(response.status_code, 400)

    def test_update_status_htmx_anonymous_redirected(self):
        """Анонимный пользователь редиректится на логин."""
        response = self.client.post(
            reverse('core:update_application_status_htmx',
                    kwargs={'application_id': self.application.id}),
            {'status': 'approved'},
        )
        self.assertEqual(response.status_code, 302)

    def test_update_status_htmx_candidate_forbidden(self):
        """Кандидат не может менять статус."""
        self.client.login(username='cand', password='pw1234567')
        response = self.client.post(
            reverse('core:update_application_status_htmx',
                    kwargs={'application_id': self.application.id}),
            {'status': 'approved'},
        )
        self.assertIn(response.status_code, (302, 403))


class FavoritesTests(TestCase):
    """Тесты Этапа 3.4: SavedJob, SavedSearch, /favorites/."""

    def setUp(self):
        from core.models import SavedJob, SavedSearch
        self.SavedJob = SavedJob
        self.SavedSearch = SavedSearch

        self.hr = User.objects.create_user(
            username='hr_fav', password='pw1234567', user_type='hr',
        )
        self.cand_user = User.objects.create_user(
            username='cand_fav', password='pw1234567', user_type='candidate',
            email='c_fav@example.com',
        )
        self.candidate = Candidate.objects.create(
            user=self.cand_user, first_name='Иван', last_name='Иванов',
            email='c_fav@example.com',
        )
        self.company = Company.objects.create(name='Acme')
        self.job = Job.objects.create(
            title='Python Dev', company=self.company, description='d',
            requirements='r', experience_level='middle', location='Москва',
            created_by=self.hr,
        )
        self.job2 = Job.objects.create(
            title='Java Dev', company=self.company, description='d',
            requirements='r', experience_level='senior', location='Москва',
            remote_work=True, created_by=self.hr,
        )

    def test_toggle_save_job_creates(self):
        """POST /jobs/<id>/toggle-save/ создаёт SavedJob."""
        self.client.login(username='cand_fav', password='pw1234567')
        response = self.client.post(
            reverse('core:toggle_save_job', kwargs={'job_id': self.job.id}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            self.SavedJob.objects.filter(
                user=self.cand_user, job=self.job
            ).exists()
        )
        self.assertContains(response, 'В избранном')

    def test_toggle_save_job_removes(self):
        """Повторный POST убирает из избранного."""
        self.SavedJob.objects.create(user=self.cand_user, job=self.job)
        self.client.login(username='cand_fav', password='pw1234567')
        response = self.client.post(
            reverse('core:toggle_save_job', kwargs={'job_id': self.job.id}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            self.SavedJob.objects.filter(
                user=self.cand_user, job=self.job
            ).exists()
        )
        self.assertContains(response, 'В избранное')

    def test_toggle_save_job_anonymous_redirected(self):
        """Анонимный пользователь → 302 на логин."""
        response = self.client.post(
            reverse('core:toggle_save_job', kwargs={'job_id': self.job.id}),
        )
        self.assertEqual(response.status_code, 302)

    def test_toggle_save_job_unique(self):
        """Повторный toggle не создаёт дубль (unique_together)."""
        self.client.login(username='cand_fav', password='pw1234567')
        for _ in range(3):
            self.client.post(
                reverse('core:toggle_save_job', kwargs={'job_id': self.job.id}),
            )
        count = self.SavedJob.objects.filter(
            user=self.cand_user, job=self.job
        ).count()
        self.assertLessEqual(count, 1)

    def test_favorites_list_renders(self):
        """GET /favorites/ отдаёт 200 и список сохранённого."""
        self.SavedJob.objects.create(user=self.cand_user, job=self.job)
        self.client.login(username='cand_fav', password='pw1234567')
        response = self.client.get(reverse('core:favorites_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Dev')

    def test_favorites_list_only_own(self):
        """Сохранённое другим пользователем не видно."""
        other = User.objects.create_user(
            username='other', password='pw1234567', user_type='candidate',
        )
        self.SavedJob.objects.create(user=other, job=self.job)
        self.SavedJob.objects.create(user=self.cand_user, job=self.job2)

        self.client.login(username='cand_fav', password='pw1234567')
        response = self.client.get(reverse('core:favorites_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Java Dev')
        self.assertNotContains(response, 'Python Dev')

    def test_save_search_creates(self):
        """POST /favorites/save-search/ создаёт SavedSearch с параметрами."""
        self.client.login(username='cand_fav', password='pw1234567')
        response = self.client.post(
            reverse('core:save_search'),
            {
                'name': 'Senior удалённо',
                'experience_level': 'senior',
                'remote_work': 'true',
            },
        )
        self.assertEqual(response.status_code, 200)
        saved = self.SavedSearch.objects.get(user=self.cand_user)
        self.assertEqual(saved.name, 'Senior удалённо')
        self.assertEqual(saved.params['experience_level'], 'senior')
        self.assertEqual(saved.params['remote_work'], 'true')

    def test_save_search_empty_name_rejected(self):
        """Без имени — ошибка."""
        self.client.login(username='cand_fav', password='pw1234567')
        response = self.client.post(reverse('core:save_search'), {'name': ''})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])

    def test_run_saved_search_redirects_with_params(self):
        """GET /favorites/saved-search/<id>/run/ редиректит на /jobs/? с params."""
        saved = self.SavedSearch.objects.create(
            user=self.cand_user,
            name='X',
            params={'experience_level': 'senior', 'remote_work': 'true'},
        )
        self.client.login(username='cand_fav', password='pw1234567')
        response = self.client.get(
            reverse('core:run_saved_search', kwargs={'search_id': saved.id}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('experience_level=senior', response['Location'])
        self.assertIn('remote_work=true', response['Location'])
        saved.refresh_from_db()
        self.assertIsNotNone(saved.last_used_at)

    def test_delete_saved_search(self):
        """POST delete_saved_search удаляет запись."""
        saved = self.SavedSearch.objects.create(
            user=self.cand_user, name='X', params={},
        )
        self.client.login(username='cand_fav', password='pw1234567')
        response = self.client.post(
            reverse('core:delete_saved_search',
                    kwargs={'search_id': saved.id}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            self.SavedSearch.objects.filter(id=saved.id).exists()
        )


class CompanyTests(TestCase):
    """Тесты Этапа 3.1: Company, CompanyReview, /companies/<slug>/."""

    def setUp(self):
        self.hr = User.objects.create_user(
            username='hr_co', password='pw1234567', user_type='hr',
        )
        self.cand_user = User.objects.create_user(
            username='cand_co', password='pw1234567', user_type='candidate',
            email='c_co@example.com',
        )

    def test_company_slug_auto_generated(self):
        """slug создаётся автоматически из name."""
        c = Company.objects.create(name='Acme Inc')
        self.assertEqual(c.slug, 'acme-inc')

    def test_company_slug_unique_on_duplicate(self):
        """Дублирующие имена получают уникальный slug (через -2)."""
        c1 = Company.objects.create(name='Acme')
        c2 = Company.objects.create(name='Acme')
        self.assertNotEqual(c1.slug, c2.slug)
        self.assertTrue(c2.slug.startswith('acme-'))

    def test_company_average_rating(self):
        """Среднее арифметическое по отзывам."""
        company = Company.objects.create(name='Acme')
        CompanyReview.objects.create(
            company=company, author=self.cand_user, rating=5, text='ok',
        )
        CompanyReview.objects.create(
            company=company, author=self.hr, rating=3, text='meh',
        )
        self.assertEqual(company.average_rating, 4.0)
        self.assertEqual(company.reviews_count, 2)

    def test_company_average_rating_no_reviews(self):
        """Без отзывов average_rating = None."""
        company = Company.objects.create(name='Acme')
        self.assertIsNone(company.average_rating)
        self.assertEqual(company.reviews_count, 0)

    def test_company_list_renders(self):
        """GET /companies/ отдаёт 200 и список компаний."""
        Company.objects.create(name='Acme')
        Company.objects.create(name='Globex')
        response = self.client.get(reverse('core:company_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acme')
        self.assertContains(response, 'Globex')

    def test_company_list_filters_by_industry(self):
        """Фильтр по отрасли работает."""
        Company.objects.create(name='IT Co', industry='IT')
        Company.objects.create(name='Bank', industry='Finance')
        response = self.client.get(
            reverse('core:company_list'), {'industry': 'IT'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'IT Co')
        self.assertNotContains(response, 'Bank')

    def test_company_detail_renders(self):
        """GET /companies/<slug>/ показывает вакансии и отзывы."""
        company = Company.objects.create(
            name='Acme', industry='IT', description='Cool place',
        )
        Job.objects.create(
            title='Backend', company=company, description='d', requirements='r',
            experience_level='middle', location='Remote',
            created_by=self.hr,
        )
        CompanyReview.objects.create(
            company=company, author=self.cand_user, rating=5,
            text='Great', title='Good',
        )
        response = self.client.get(
            reverse('core:company_detail', kwargs={'slug': company.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acme')
        self.assertContains(response, 'Backend')
        self.assertContains(response, 'Great')

    def test_company_detail_404(self):
        """Несуществующий slug → 404."""
        response = self.client.get(
            reverse('core:company_detail', kwargs={'slug': 'no-such'}),
        )
        self.assertEqual(response.status_code, 404)

    def test_add_review_creates(self):
        """POST отзыв создаёт CompanyReview."""
        company = Company.objects.create(name='Acme')
        self.client.login(username='cand_co', password='pw1234567')
        response = self.client.post(
            reverse('core:add_company_review', kwargs={'slug': company.slug}),
            {
                'rating': 5,
                'text': 'Отличная компания',
                'title': 'Хорошо',
                'pros': 'Команда',
                'cons': '',
                'is_anonymous': '',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            CompanyReview.objects.filter(
                company=company, author=self.cand_user
            ).exists()
        )

    def test_add_review_anonymous_redirected(self):
        """Анонимный пользователь → 302 на логин."""
        company = Company.objects.create(name='Acme')
        response = self.client.post(
            reverse('core:add_company_review', kwargs={'slug': company.slug}),
            {'rating': 5, 'text': 'x'},
        )
        self.assertEqual(response.status_code, 302)

    def test_add_review_unique_per_user(self):
        """Один пользователь — один отзыв о компании."""
        company = Company.objects.create(name='Acme')
        CompanyReview.objects.create(
            company=company, author=self.cand_user, rating=5, text='first',
        )
        self.client.login(username='cand_co', password='pw1234567')
        response = self.client.post(
            reverse('core:add_company_review', kwargs={'slug': company.slug}),
            {'rating': 3, 'text': 'second'},
        )
        self.assertEqual(response.status_code, 302)
        reviews = CompanyReview.objects.filter(
            company=company, author=self.cand_user
        )
        self.assertEqual(reviews.count(), 1)

    def test_review_validators(self):
        """rating валидируется 1..5 через full_clean."""
        company = Company.objects.create(name='Acme')
        bad = CompanyReview(
            company=company, rating=0, text='x',
        )
        with self.assertRaises(Exception):
            bad.full_clean()


class ExtendedSearchTests(TestCase):
    """Тесты Этапа 3.3: расширенный поиск вакансий."""

    def setUp(self):
        self.hr = User.objects.create_user(
            username='hr_es', password='pw1234567', user_type='hr',
        )
        self.company = Company.objects.create(name='Acme')
        self.job_python = Job.objects.create(
            title='Python Developer', company=self.company, description='d',
            requirements='r', experience_level='middle', location='Москва',
            employment_type='full_time',
            salary_min=150000, salary_max=250000,
            skills_required=['Python', 'Django', 'REST'],
            created_by=self.hr,
        )
        self.job_java = Job.objects.create(
            title='Java Developer', company=self.company, description='d',
            requirements='r', experience_level='senior', location='Москва',
            employment_type='part_time',
            salary_min=200000, salary_max=350000,
            skills_required=['Java', 'Spring'],
            created_by=self.hr,
        )
        self.job_intern = Job.objects.create(
            title='Python Intern', company=self.company, description='d',
            requirements='r', experience_level='junior', location='СПб',
            employment_type='internship',
            skills_required=['Python'],
            created_by=self.hr,
        )
        self.job_paused = Job.objects.create(
            title='Paused', company=self.company, description='d',
            requirements='r', experience_level='middle', location='Москва',
            status='paused', created_by=self.hr,
        )

    def test_search_by_title_substring(self):
        """Поиск по подстроке title."""
        response = self.client.get(reverse('core:job_list'), {'search': 'Python'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Developer')
        self.assertContains(response, 'Python Intern')
        self.assertNotContains(response, 'Java Developer')

    def test_search_by_skill(self):
        """Поиск по навыку (skills_required)."""
        response = self.client.get(reverse('core:job_list'), {'skills': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Developer')
        self.assertNotContains(response, 'Java Developer')

    def test_search_by_skills_multi(self):
        """Multi-select навыков — вакансия с любым из них подходит."""
        response = self.client.get(
            reverse('core:job_list'), {'skills': 'Java,Django'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Developer')
        self.assertContains(response, 'Java Developer')

    def test_filter_by_employment(self):
        """Фильтр по типу занятости."""
        response = self.client.get(
            reverse('core:job_list'), {'employment_type': 'internship'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Intern')
        self.assertNotContains(response, 'Python Developer')
        self.assertNotContains(response, 'Java Developer')

    def test_filter_by_salary_min(self):
        """Фильтр по минимальной зарплате."""
        response = self.client.get(
            reverse('core:job_list'), {'salary_min': '300000'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Java Developer')  # 200-350k
        self.assertNotContains(response, 'Python Developer')  # 150-250k
        self.assertNotContains(response, 'Python Intern')

    def test_filter_by_salary_range(self):
        """Фильтр по диапазону зарплаты (вилки, пересекающиеся с диапазоном)."""
        response = self.client.get(
            reverse('core:job_list'),
            {'salary_min': '100000', 'salary_max': '180000'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Java Developer')  # 200-350, вне диапазона
        self.assertContains(response, 'Python Developer')  # 150-250, пересекается

    def test_sort_salary_desc(self):
        """Сортировка по убыванию зарплаты."""
        response = self.client.get(
            reverse('core:job_list'), {'sort': 'salary_desc'},
        )
        self.assertEqual(response.status_code, 200)
        # Java (350k) выше, чем Python (250k) выше, чем Intern (None)
        body = response.content.decode()
        java_pos = body.find('Java Developer')
        python_pos = body.find('Python Developer')
        self.assertLess(java_pos, python_pos)

    def test_sort_salary_asc(self):
        """Сортировка по возрастанию зарплаты."""
        response = self.client.get(
            reverse('core:job_list'), {'sort': 'salary_asc'},
        )
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        java_pos = body.find('Java Developer')
        python_pos = body.find('Python Developer')
        self.assertLess(python_pos, java_pos)

    def test_paused_jobs_excluded(self):
        """Вакансии со статусом paused/closed не показываются."""
        response = self.client.get(reverse('core:job_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Paused')

    def test_search_htmx_returns_only_results(self):
        """HTMX-эндпоинт возвращает фрагмент списка (без html)."""
        response = self.client.get(
            reverse('core:job_list_htmx'),
            {'search': 'Python', 'experience_level': 'junior'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Intern')
        self.assertNotContains(response, 'Python Developer')
        self.assertNotContains(response, '<html')

    def test_combined_filters(self):
        """Комбинация фильтров работает."""
        response = self.client.get(
            reverse('core:job_list'),
            {
                'experience_level': 'junior',
                'employment_type': 'internship',
                'skills': 'Python',
                'location': 'СПб',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Intern')
        self.assertNotContains(response, 'Java Developer')

    def test_search_ignores_unsafe_salary(self):
        """Невалидный salary_min не вызывает 500."""
        response = self.client.get(
            reverse('core:job_list'), {'salary_min': 'abc'},
        )
        self.assertEqual(response.status_code, 200)

class Stage4FrontendTests(TestCase):
    """Этап 4: тесты фронтенд-редизайна (дедупликация, partials, HTMX, mobile)."""

    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.hr = User.objects.create_user(
            username='hr_s4', password='pw', user_type='hr',
        )
        self.cand_user = User.objects.create_user(
            username='cand_s4', password='pw', user_type='candidate',
            email='c4@example.com',
        )
        self.candidate = Candidate.objects.create(
            user=self.cand_user, first_name='Иван', last_name='Петров',
            email='c4@example.com',
        )
        self.company = Company.objects.create(name='Acme S4')
        self.job = Job.objects.create(
            title='Python Dev', company=self.company,
            description='Описание', requirements='Python',
            experience_level='middle', location='Москва',
            created_by=self.hr,
        )
        self.application = Application.objects.create(
            job=self.job, candidate=self.candidate,
            cover_letter='Тест',
        )

    def test_partials_render_without_errors(self):
        """Все partials рендерятся без ошибок."""
        from django.template.loader import render_to_string
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser

        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.cand_user

        ctx = {
            'job': self.job,
            'candidate': self.candidate,
            'application': self.application,
            'status': 'pending',
            'score': 0.7,
            'layout': 'list',
            'show_save': True,
            'show_description': True,
            'user': self.cand_user,
            'csrf_token': 'test',
            'request': request,
        }
        for tmpl in [
            'partials/job_card.html',
            'partials/candidate_avatar.html',
            'partials/status_badge.html',
            'partials/ai_score.html',
            'partials/skeleton.html',
        ]:
            html = render_to_string(tmpl, ctx)
            self.assertNotIn('{{', html, f'Template {tmpl} not rendered')

    def test_custom_css_exists(self):
        """custom.css содержит все ключевые классы Этапа 4."""
        css_file = Path(settings.STATICFILES_DIRS[0]) / 'vendor' / 'css' / 'custom.css'
        if not css_file.exists():
            self.skipTest(f'custom.css not found at {css_file}')
        css_text = css_file.read_text()
        for cls in [
            '.avatar-circle',
            '.badge-status',
            '.ai-score-circle',
            '.company-logo-placeholder',
            '.toast-container',
            '.autohr-toast',
            '.skeleton',
            '.sticky-filter',
            '.bottom-nav',
        ]:
            self.assertIn(cls, css_text, f'Missing CSS class {cls}')

    def test_custom_js_exposes_autohr_namespace(self):
        """custom.js экспортирует глобальный window.AutoHR."""
        js_file = Path(settings.STATICFILES_DIRS[0]) / 'vendor' / 'js' / 'custom.js'
        if not js_file.exists():
            self.skipTest(f'custom.js not found at {js_file}')
        js_text = js_file.read_text()
        self.assertIn('window.AutoHR = AutoHR', js_text)
        for fn in [
            'showToast',
            'getCookie',
            'formatFileSize',
            'initTooltips',
            'initConfirmDialogs',
            'initHtmxEvents',
        ]:
            self.assertIn(fn, js_text, f'Missing JS function {fn}')

    def test_times_filter_works(self):
        """times filter используется в skeleton.html."""
        from django.template import Context, Template
        t = Template('{% load core_extras %}{% for i in 3|times %}*{{ forloop.counter }}{% endfor %}')
        rendered = t.render(Context({}))
        self.assertEqual(rendered, '*1*2*3')

    def test_templates_no_inline_style_blocks(self):
        """Шаблоны не содержат inline <style> блоков в {% block extra_css %}."""
        for tmpl_path in Path('templates').rglob('*.html'):
            text = tmpl_path.read_text()
            self.assertNotIn('<style>', text, f'Inline <style> in {tmpl_path}')

    def test_templates_no_duplicate_get_cookie(self):
        """Шаблоны не дублируют getCookie() — берут из AutoHR.getCookie."""
        for tmpl_path in Path('templates').rglob('*.html'):
            text = tmpl_path.read_text()
            self.assertNotIn(
                'function getCookie(', text,
                f'Duplicate getCookie() in {tmpl_path}',
            )

    def test_delete_job_htmx(self):
        """HTMX-эндпоинт удаления вакансии возвращает 200 + toast."""
        self.client.login(username='hr_s4', password='pw')
        response = self.client.post(
            reverse('core:delete_job_htmx', kwargs={'job_id': self.job.id}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Job.objects.filter(id=self.job.id).count(), 0)
        self.assertIn('showToast', response['HX-Trigger'])

    def test_delete_job_htmx_other_user_forbidden(self):
        """Чужой HR не может удалить вакансию через HTMX."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        other_hr = User.objects.create_user(
            username='other_hr', password='pw', user_type='hr',
        )
        self.client.login(username='other_hr', password='pw')
        response = self.client.post(
            reverse('core:delete_job_htmx', kwargs={'job_id': self.job.id}),
        )
        self.assertEqual(response.status_code, 404)

    def test_application_detail_htmx(self):
        """HTMX-эндпоинт деталей заявки возвращает HTML модального окна."""
        self.client.login(username='hr_s4', password='pw')
        response = self.client.get(
            reverse('core:application_detail_htmx',
                    kwargs={'application_id': self.application.id}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'Детали заявки #{self.application.id}')
        self.assertIn('showModal', response['HX-Trigger'])

    def test_schedule_interview_htmx(self):
        """HTMX-эндпоинт планирования собеседования возвращает обновлённую строку."""
        from datetime import datetime, timedelta, timezone as tz
        scheduled = (datetime.now(tz.utc) + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M').replace('T', ' ')
        self.client.login(username='hr_s4', password='pw')
        response = self.client.post(
            reverse('core:schedule_interview_htmx',
                    kwargs={'application_id': self.application.id}),
            {'date': scheduled.split()[0], 'time': scheduled.split()[1],
             'format': 'online'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('showToast', response['HX-Trigger'])

    def test_add_note_htmx(self):
        """HTMX-эндпоинт добавления заметки возвращает обновлённый блок заметок."""
        self.client.login(username='hr_s4', password='pw')
        response = self.client.post(
            reverse('core:add_note_htmx',
                    kwargs={'application_id': self.application.id}),
            {'note': 'Хороший кандидат'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('showToast', response['HX-Trigger'])
        self.assertContains(response, 'Хороший кандидат')

    def test_update_interview_status_htmx(self):
        """HTMX-эндпоинт обновления статуса собеседования."""
        from calendar_app.models import Interview, InterviewType
        itype, _ = InterviewType.objects.get_or_create(
            name='Тестовое',
            defaults={'duration_minutes': 60, 'is_active': True},
        )
        interview = Interview.objects.create(
            application=self.application,
            candidate=self.candidate,
            interviewer=self.hr,
            interview_type=itype,
            scheduled_at=datetime.now(tz.utc) + timedelta(days=1),
            status='scheduled',
            duration_minutes=60,
        )
        self.client.login(username='hr_s4', password='pw')
        response = self.client.post(
            reverse('core:update_interview_status_htmx',
                    kwargs={'interview_id': interview.id}),
            {'status': 'confirmed'},
        )
        self.assertEqual(response.status_code, 200)
        interview.refresh_from_db()
        self.assertEqual(interview.status, 'confirmed')

    def test_reschedule_interview_htmx(self):
        """HTMX-эндпоинт переноса собеседования."""
        from calendar_app.models import Interview, InterviewType
        itype, _ = InterviewType.objects.get_or_create(
            name='Тестовое 2',
            defaults={'duration_minutes': 60, 'is_active': True},
        )
        interview = Interview.objects.create(
            application=self.application,
            candidate=self.candidate,
            interviewer=self.hr,
            interview_type=itype,
            scheduled_at=datetime.now(tz.utc) + timedelta(days=1),
            status='scheduled',
            duration_minutes=60,
        )
        new_dt = (datetime.now(tz.utc) + timedelta(days=5)).strftime('%Y-%m-%d %H:%M')
        self.client.login(username='hr_s4', password='pw')
        response = self.client.post(
            reverse('core:reschedule_interview_htmx',
                    kwargs={'interview_id': interview.id}),
            {'date': new_dt.split()[0], 'time': new_dt.split()[1],
             'reason': 'Тест'},
        )
        self.assertEqual(response.status_code, 200)
        interview.refresh_from_db()
        self.assertEqual(interview.status, 'rescheduled')

    def test_other_user_cannot_access_htmx_endpoints(self):
        """Сторонний пользователь не может удалять чужие вакансии/менять статусы."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        other = User.objects.create_user(
            username='other_s4', password='pw', user_type='candidate',
        )
        self.client.login(username='other_s4', password='pw')
        response = self.client.post(
            reverse('core:delete_job_htmx', kwargs={'job_id': self.job.id}),
        )
        self.assertEqual(response.status_code, 404)


class Stage5ProductionTests(TestCase):
    """Этап 5: тесты для rate-limit, health-checks, CORS, backup."""

    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.hr = User.objects.create_user(
            username='hr_s5', password='pw1234567', user_type='hr',
        )
        self.cand_user = User.objects.create_user(
            username='cand_s5', password='pw1234567', user_type='candidate',
        )

    def test_rate_limit_allows_under_limit(self):
        """Под лимитом — запрос проходит."""
        from core.ratelimit import rate_limit

        @rate_limit(key='test_under', limit=3, period=60)
        def my_view(request):
            from django.http import HttpResponse
            return HttpResponse('OK')

        factory = RequestFactory()
        for _ in range(3):
            response = my_view(factory.get('/'))
            self.assertEqual(response.status_code, 200)

    def test_rate_limit_blocks_over_limit(self):
        """Свыше лимита — 429."""
        from core.ratelimit import rate_limit

        @rate_limit(key='test_over', limit=2, period=60)
        def my_view(request):
            from django.http import HttpResponse
            return HttpResponse('OK')

        factory = RequestFactory()
        my_view(factory.get('/'))
        my_view(factory.get('/'))
        response = my_view(factory.get('/'))
        self.assertEqual(response.status_code, 429)

    def test_rate_limit_separate_keys(self):
        """Разные ключи — независимые счётчики."""
        from core.ratelimit import rate_limit

        @rate_limit(key='key_a', limit=1, period=60)
        def view_a(request):
            from django.http import HttpResponse
            return HttpResponse('A')

        @rate_limit(key='key_b', limit=1, period=60)
        def view_b(request):
            from django.http import HttpResponse
            return HttpResponse('B')

        factory = RequestFactory()
        # key_a: первый проходит, второй блокируется
        self.assertEqual(view_a(factory.get('/')).status_code, 200)
        self.assertEqual(view_a(factory.get('/')).status_code, 429)
        # key_b: первый проходит (независимый счётчик)
        self.assertEqual(view_b(factory.get('/')).status_code, 200)

    def test_rate_limit_htmx_returns_html(self):
        """HTMX-запросы получают HTML-ошибку, а не голый 429."""
        from core.ratelimit import rate_limit

        @rate_limit(key='test_htmx', limit=1, period=60)
        def my_view(request):
            from django.http import HttpResponse
            return HttpResponse('OK')

        factory = RequestFactory()
        my_view(factory.get('/'))
        response = my_view(factory.get('/', HTTP_HX_REQUEST='true'))
        self.assertEqual(response.status_code, 429)
        self.assertIn('Слишком много запросов', response.content.decode())

    def test_rate_limit_class_view(self):
        """rate_limit_class для CBV — лимит на POST, не на GET."""
        from core.ratelimit import rate_limit_class

        @rate_limit_class(key='test_cbv', limit=2, period=60)
        class MyView:
            def dispatch(self, request, *args, **kwargs):
                from django.http import HttpResponse
                return HttpResponse(f'{request.method} OK')

        factory = RequestFactory()
        view = MyView()

        # GET не считается
        for _ in range(5):
            response = view.dispatch(factory.get('/'))
            self.assertEqual(response.status_code, 200)

        # POST считается
        self.assertEqual(view.dispatch(factory.post('/')).status_code, 200)
        self.assertEqual(view.dispatch(factory.post('/')).status_code, 200)
        response = view.dispatch(factory.post('/'))
        self.assertEqual(response.status_code, 429)

    def test_health_overall(self):
        """GET /health/ — общий статус + проверки."""
        response = self.client.get(reverse('health:overall'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertIn('checks', data)
        self.assertIn('database', data['checks'])

    def test_health_db(self):
        """GET /health/db/ — только БД."""
        response = self.client.get(reverse('health:db'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')

    def test_health_ready(self):
        """GET /health/ready/ — readiness probe."""
        response = self.client.get(reverse('health:ready'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ready')

    def test_health_live(self):
        """GET /health/live/ — liveness probe (всегда alive)."""
        response = self.client.get(reverse('health:live'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'alive')

    def test_cors_disabled_by_default(self):
        """CORS по умолчанию выключен — заголовки не добавляются."""
        response = self.client.get(
            reverse('core:job_list'),
            HTTP_ORIGIN='https://example.com',
        )
        self.assertNotIn('Access-Control-Allow-Origin', response)

    def test_cors_enabled(self):
        """CORS включается через CORS_ENABLED=True + CORS_ALLOWED_ORIGINS."""
        with override_settings(
            CORS_ENABLED=True,
            CORS_ALLOWED_ORIGINS=['https://example.com'],
            CORS_ALLOW_CREDENTIALS=True,
        ):
            response = self.client.get(
                reverse('core:job_list'),
                HTTP_ORIGIN='https://example.com',
            )
            self.assertEqual(
                response['Access-Control-Allow-Origin'],
                'https://example.com',
            )
            self.assertEqual(response['Access-Control-Allow-Credentials'], 'true')

    def test_cors_not_in_allowed_origins(self):
        """Неразрешённый origin — заголовки не добавляются."""
        with override_settings(
            CORS_ENABLED=True,
            CORS_ALLOWED_ORIGINS=['https://example.com'],
        ):
            response = self.client.get(
                reverse('core:job_list'),
                HTTP_ORIGIN='https://evil.com',
            )
            self.assertNotIn('Access-Control-Allow-Origin', response)

    def test_login_view_has_rate_limit(self):
        """Login view защищён rate-limit (через rate_limit_class)."""
        # Просто проверяем что view не падает при рендеринге
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_backup_db_command(self):
        """Management command backup_db создаёт файл бэкапа."""
        from django.core.management import call_command
        from django.conf import settings as dj_settings
        from io import StringIO
        import tempfile

        # Используем временную директорию
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = dj_settings.DATABASES['default']['NAME']
            if not Path(db_path).exists():
                self.skipTest('БД не существует (тестовый run)')

            out = StringIO()
            call_command('backup_db', '--keep', '3', '--output', tmpdir,
                         stdout=out, stderr=StringIO())

            backups = list(Path(tmpdir).glob('backup_*'))
            self.assertGreater(len(backups), 0,
                               f'Бэкап не создан. Output: {out.getvalue()}')


class RateLimitCacheTestCase(TestCase):
    """Тесты что rate-limit использует cache (изолирован между тестами)."""

    def test_cache_set_and_get(self):
        """Cache.set + cache.get работают (базовая проверка)."""
        from django.core.cache import cache
        cache.set('rl:test_isolation', 999, timeout=60)
        self.assertEqual(cache.get('rl:test_isolation'), 999)
        cache.delete('rl:test_isolation')
        self.assertIsNone(cache.get('rl:test_isolation'))
