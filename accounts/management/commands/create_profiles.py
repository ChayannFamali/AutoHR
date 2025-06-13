from django.core.management.base import BaseCommand

from accounts.models import User, UserProfile


class Command(BaseCommand):
    help = 'Create profiles for existing users'
    
    def handle(self, *args, **options):
        users_without_profile = User.objects.filter(profile__isnull=True)
        created_count = 0
        
        for user in users_without_profile:
            UserProfile.objects.create(user=user)
            created_count += 1
            
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} profiles')
        )
