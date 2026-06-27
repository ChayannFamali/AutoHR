"""Тесты Этапа 3.7: чат MVP."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Candidate, Company, Job
from messaging.models import Conversation, Message

User = get_user_model()


class MessagingTests(TestCase):

    def setUp(self):
        self.hr = User.objects.create_user(
            username='hr_msg', password='pw', user_type='hr',
        )
        self.cand_user = User.objects.create_user(
            username='cand_msg', password='pw', user_type='candidate',
        )
        self.candidate = Candidate.objects.create(
            user=self.cand_user, first_name='И', last_name='И',
            email='c@msg.com',
        )
        self.company = Company.objects.create(name='Acme')
        self.job = Job.objects.create(
            title='Dev', company=self.company, description='d',
            requirements='r', experience_level='middle', location='M',
            created_by=self.hr,
        )

    def test_get_or_create_between(self):
        """Метод создаёт переписку между двумя пользователями."""
        conv, created = Conversation.get_or_create_between(self.hr, self.cand_user)
        self.assertTrue(created)
        self.assertEqual(conv.participants.count(), 2)

        conv2, created2 = Conversation.get_or_create_between(self.hr, self.cand_user)
        self.assertFalse(created2)
        self.assertEqual(conv.id, conv2.id)

    def test_get_or_create_with_job(self):
        """Переписка по конкретной вакансии — отдельная."""
        conv1, _ = Conversation.get_or_create_between(
            self.hr, self.cand_user, job=self.job,
        )
        conv2, _ = Conversation.get_or_create_between(self.hr, self.cand_user)
        self.assertNotEqual(conv1.id, conv2.id)

    def test_conversation_list_anonymous_redirected(self):
        response = self.client.get(reverse('messaging:conversation_list'))
        self.assertEqual(response.status_code, 302)

    def test_conversation_list_renders(self):
        Conversation.get_or_create_between(self.hr, self.cand_user)
        self.client.login(username='hr_msg', password='pw')
        response = self.client.get(reverse('messaging:conversation_list'))
        self.assertEqual(response.status_code, 200)

    def test_start_conversation_creates(self):
        self.client.login(username='hr_msg', password='pw')
        response = self.client.get(
            reverse('messaging:start_conversation',
                    kwargs={'user_id': self.cand_user.id}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_start_conversation_with_self_blocked(self):
        self.client.login(username='hr_msg', password='pw')
        response = self.client.get(
            reverse('messaging:start_conversation',
                    kwargs={'user_id': self.hr.id}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_conversation_detail_marks_read(self):
        conv, _ = Conversation.get_or_create_between(self.hr, self.cand_user)
        Message.objects.create(
            conversation=conv, sender=self.cand_user, body='hi',
        )
        self.client.login(username='hr_msg', password='pw')
        response = self.client.get(
            reverse('messaging:conversation_detail',
                    kwargs={'conversation_id': conv.id}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.filter(read_at__isnull=True).count(), 0)

    def test_send_message_htmx(self):
        conv, _ = Conversation.get_or_create_between(self.hr, self.cand_user)
        self.client.login(username='hr_msg', password='pw')
        response = self.client.post(
            reverse('messaging:send_message',
                    kwargs={'conversation_id': conv.id}),
            {'body': 'Привет'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.filter(conversation=conv).count(), 1)
        self.assertContains(response, 'Привет')

    def test_send_message_empty_body(self):
        conv, _ = Conversation.get_or_create_between(self.hr, self.cand_user)
        self.client.login(username='hr_msg', password='pw')
        response = self.client.post(
            reverse('messaging:send_message',
                    kwargs={'conversation_id': conv.id}),
            {'body': ''},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Message.objects.filter(conversation=conv).count(), 0)

    def test_poll_messages(self):
        conv, _ = Conversation.get_or_create_between(self.hr, self.cand_user)
        msg = Message.objects.create(
            conversation=conv, sender=self.cand_user, body='Тест',
        )
        self.client.login(username='hr_msg', password='pw')
        response = self.client.get(
            reverse('messaging:poll_messages',
                    kwargs={'conversation_id': conv.id}),
            {'since': '0'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тест')

        response = self.client.get(
            reverse('messaging:poll_messages',
                    kwargs={'conversation_id': conv.id}),
            {'since': str(msg.id)},
        )
        self.assertNotContains(response, 'Тест')

    def test_other_user_cannot_view(self):
        """Сторонний пользователь не видит чужую переписку → 404."""
        conv, _ = Conversation.get_or_create_between(self.hr, self.cand_user)
        outsider = User.objects.create_user(
            username='outsider', password='pw', user_type='candidate',
        )
        self.client.login(username='outsider', password='pw')
        response = self.client.get(
            reverse('messaging:conversation_detail',
                    kwargs={'conversation_id': conv.id}),
        )
        self.assertEqual(response.status_code, 404)

    def test_unread_count(self):
        conv, _ = Conversation.get_or_create_between(self.hr, self.cand_user)
        Message.objects.create(
            conversation=conv, sender=self.cand_user, body='1',
        )
        Message.objects.create(
            conversation=conv, sender=self.cand_user, body='2',
        )
        self.assertEqual(conv.unread_count_for(self.hr), 2)
        self.assertEqual(conv.unread_count_for(self.cand_user), 0)

    def test_mark_read(self):
        msg = Message.objects.create(
            conversation=Conversation.objects.first()
            or Conversation.objects.create(),
            sender=self.cand_user, body='x',
        )
        self.assertIsNone(msg.read_at)
        msg.mark_read()
        self.assertIsNotNone(msg.read_at)
