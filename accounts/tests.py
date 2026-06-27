from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import (Candidate, Education, Skill, WorkExperience)

User = get_user_model()


class LoginSmokeTests(TestCase):
    """Smoke: страница логина доступна, без 404 на статике."""

    def test_login_page_returns_200(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Вход в систему')

    def test_login_page_does_not_reference_missing_image(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertNotContains(response, "autoHR.png")


class RegistrationSmokeTests(TestCase):
    """Smoke: страница регистрации кандидата доступна и принимает форму."""

    def test_register_candidate_page_returns_200(self):
        url = reverse('accounts:register_candidate')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_register_choice_page_returns_200(self):
        url = reverse('accounts:register_choice')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "autoHR.png")


class AuthRequiredTests(TestCase):
    """Smoke: ключевые защищённые страницы требуют авторизации."""

    def test_application_list_redirects_anonymous(self):
        response = self.client.get(reverse('core:application_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_resume_list_redirects_anonymous(self):
        response = self.client.get(reverse('resume:resume_list'))
        self.assertEqual(response.status_code, 302)

    def test_job_detail_accessible_anonymous(self):
        response = self.client.get(reverse('core:job_list'))
        self.assertEqual(response.status_code, 200)


class RoleBasedAccessTests(TestCase):
    """Smoke: проверка прав на экспорт — только HR."""

    def setUp(self):
        self.hr_user = User.objects.create_user(
            username='hr_user', password='hr_pass_123',
            user_type='hr', email='hr@example.com'
        )
        self.candidate_user = User.objects.create_user(
            username='candidate_user', password='cand_pass_123',
            user_type='candidate', email='candidate@example.com',
            first_name='Cand', last_name='User'
        )
        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            first_name='Cand', last_name='User',
            email='candidate@example.com'
        )

    def test_export_applications_redirects_anonymous(self):
        response = self.client.get(reverse('core:export_applications'))
        self.assertEqual(response.status_code, 302)

    def test_export_applications_forbidden_for_candidate(self):
        self.client.login(username='candidate_user', password='cand_pass_123')
        response = self.client.get(reverse('core:export_applications'))
        self.assertIn(response.status_code, (302, 403))

    def test_export_applications_ok_for_hr(self):
        self.client.login(username='hr_user', password='hr_pass_123')
        response = self.client.get(reverse('core:export_applications'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'spreadsheetml',
            response['Content-Type'],
            'Ожидается XLSX-файл'
        )

    def test_export_resumes_excel_requires_hr(self):
        url = reverse('resume:export_resumes_excel')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username='candidate_user', password='cand_pass_123')
        response = self.client.get(url)
        self.assertIn(response.status_code, (302, 403))

        self.client.login(username='hr_user', password='hr_pass_123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class CandidateProfileTests(TestCase):
    """Тесты Этапа 3.2: расширенный профиль кандидата."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='cand32', password='pw1234567', user_type='candidate',
            email='c32@example.com',
        )
        self.candidate = Candidate.objects.create(
            user=self.user, first_name='Иван', last_name='Иванов',
            email='c32@example.com', phone='+7999', location='Москва',
        )

    def test_profile_view_renders_tabs(self):
        self.client.login(username='cand32', password='pw1234567')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Обзор')
        self.assertContains(response, 'Опыт')
        self.assertContains(response, 'Образование')
        self.assertContains(response, 'Навыки')

    def test_profile_view_anonymous_redirected(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)

    def test_add_work_experience(self):
        self.client.login(username='cand32', password='pw1234567')
        response = self.client.post(
            reverse('accounts:add_work_experience'),
            {
                'company': 'Acme',
                'position': 'Senior Dev',
                'start_date': '2020-01-01',
                'end_date': '2023-12-31',
                'is_current': '',
                'description': 'Coding',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(WorkExperience.objects.filter(candidate=self.candidate).count(), 1)

    def test_add_work_experience_current_no_end_date(self):
        self.client.login(username='cand32', password='pw1234567')
        response = self.client.post(
            reverse('accounts:add_work_experience'),
            {
                'company': 'Acme',
                'position': 'Senior Dev',
                'start_date': '2023-01-01',
                'is_current': 'on',
                'description': '',
            },
        )
        self.assertEqual(response.status_code, 302)
        we = WorkExperience.objects.get(candidate=self.candidate)
        self.assertTrue(we.is_current)
        self.assertIsNone(we.end_date)

    def test_add_work_experience_invalid_dates(self):
        self.client.login(username='cand32', password='pw1234567')
        response = self.client.post(
            reverse('accounts:add_work_experience'),
            {
                'company': 'X',
                'position': 'Y',
                'start_date': '2023-01-01',
                'end_date': '2020-01-01',
                'is_current': '',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(WorkExperience.objects.count(), 0)

    def test_edit_work_experience(self):
        we = WorkExperience.objects.create(
            candidate=self.candidate, company='Old', position='Old',
            start_date=date(2020, 1, 1), end_date=date(2021, 1, 1),
        )
        self.client.login(username='cand32', password='pw1234567')
        response = self.client.post(
            reverse('accounts:edit_work_experience', kwargs={'we_id': we.id}),
            {
                'company': 'New', 'position': 'New',
                'start_date': '2020-01-01', 'end_date': '2021-12-31',
                'is_current': '',
            },
        )
        self.assertEqual(response.status_code, 302)
        we.refresh_from_db()
        self.assertEqual(we.company, 'New')

    def test_delete_work_experience(self):
        we = WorkExperience.objects.create(
            candidate=self.candidate, company='X', position='Y',
            start_date=date(2020, 1, 1), end_date=date(2021, 1, 1),
        )
        self.client.login(username='cand32', password='pw1234567')
        response = self.client.post(
            reverse('accounts:delete_work_experience', kwargs={'we_id': we.id}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(WorkExperience.objects.filter(id=we.id).exists())

    def test_work_experience_only_own(self):
        other_user = User.objects.create_user(
            username='other32', password='pw', user_type='candidate',
        )
        other_cand = Candidate.objects.create(
            user=other_user, first_name='A', last_name='B',
            email='a@b.c',
        )
        we = WorkExperience.objects.create(
            candidate=other_cand, company='X', position='Y',
            start_date=date(2020, 1, 1), end_date=date(2021, 1, 1),
        )
        self.client.login(username='cand32', password='pw1234567')
        response = self.client.post(
            reverse('accounts:edit_work_experience', kwargs={'we_id': we.id}),
            {'company': 'HACK', 'position': 'X', 'start_date': '2020-01-01',
             'end_date': '2021-01-01', 'is_current': ''},
        )
        self.assertEqual(response.status_code, 404)

    def test_add_education(self):
        self.client.login(username='cand32', password='pw1234567')
        response = self.client.post(
            reverse('accounts:add_education'),
            {
                'institution': 'МГУ',
                'degree': 'master',
                'field_of_study': 'Computer Science',
                'start_year': 2015,
                'end_year': 2020,
                'description': '',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Education.objects.filter(candidate=self.candidate).count(), 1)

    def test_add_education_invalid_years(self):
        self.client.login(username='cand32', password='pw1234567')
        response = self.client.post(
            reverse('accounts:add_education'),
            {
                'institution': 'X',
                'degree': 'bachelor',
                'start_year': 2020,
                'end_year': 2015,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Education.objects.count(), 0)

    def test_delete_education(self):
        ed = Education.objects.create(
            candidate=self.candidate, institution='X', degree='bachelor',
            start_year=2010, end_year=2015,
        )
        self.client.login(username='cand32', password='pw1234567')
        response = self.client.post(
            reverse('accounts:delete_education', kwargs={'ed_id': ed.id}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Education.objects.filter(id=ed.id).exists())

    def test_add_skill(self):
        self.client.login(username='cand32', password='pw1234567')
        response = self.client.post(
            reverse('accounts:add_skill'),
            {'name': 'Python', 'level': 'expert', 'years_of_experience': 5},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Skill.objects.filter(candidate=self.candidate).count(), 1)

    def test_add_skill_unique(self):
        Skill.objects.create(candidate=self.candidate, name='Python', level='expert')
        self.client.login(username='cand32', password='pw1234567')
        response = self.client.post(
            reverse('accounts:add_skill'),
            {'name': 'Python', 'level': 'beginner', 'years_of_experience': 1},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Skill.objects.filter(candidate=self.candidate).count(), 1)

    def test_delete_skill(self):
        sk = Skill.objects.create(candidate=self.candidate, name='X')
        self.client.login(username='cand32', password='pw1234567')
        response = self.client.post(
            reverse('accounts:delete_skill', kwargs={'skill_id': sk.id}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Skill.objects.filter(id=sk.id).exists())

    def test_skill_level_color(self):
        sk = Skill.objects.create(candidate=self.candidate, name='X', level='expert')
        self.assertEqual(sk.level_color, 'success')
        sk.level = 'intermediate'
        self.assertEqual(sk.level_color, 'warning')
        sk.level = 'beginner'
        self.assertEqual(sk.level_color, 'info')

    def test_add_experience_requires_candidate(self):
        no_cand_user = User.objects.create_user(
            username='no_cand', password='pw', user_type='candidate',
        )
        self.client.login(username='no_cand', password='pw')
        response = self.client.get(reverse('accounts:add_work_experience'))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('accounts:add_education'))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('accounts:add_skill'))
        self.assertEqual(response.status_code, 302)
