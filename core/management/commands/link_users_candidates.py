from django.core.management.base import BaseCommand

from accounts.models import User
from core.models import Candidate


class Command(BaseCommand):
    help = 'Связывает пользователей с кандидатами по email'

    def handle(self, *args, **options):
        self.stdout.write("Начинаем связывание пользователей и кандидатов...")
        
        candidates_without_user = Candidate.objects.filter(user__isnull=True)
        linked_count = 0
        
        for candidate in candidates_without_user:
            try:
                user = User.objects.get(email=candidate.email, user_type='candidate')
                candidate.user = user
                candidate.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Связали: {user.username} ({user.email}) -> {candidate.full_name}'
                    )
                )
                linked_count += 1
                
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Не найден пользователь для кандидата: {candidate.full_name} ({candidate.email})'
                    )
                )
            except User.MultipleObjectsReturned:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️ Найдено несколько пользователей для email: {candidate.email}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Готово! Связано записей: {linked_count}')
        )
