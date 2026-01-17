import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from core.models import Profile


class Command(BaseCommand):
    help = '🌟 Creates a default superuser \'admin\' with a Profile. Ignores if already exists.'

    def handle(self, *args, **kwargs):
        self.stdout.write('🔹 Starting creation of admin user and profile...')

        try:
            adminUser = User(
                username='admin',
                email='django.admin@example.com',
                first_name='Django',
                last_name='Admin',
                is_staff=True,
                is_active=True,
                is_superuser=True,
            )
            adminUser.set_password('admin')
            adminUser.save()
            self.stdout.write(self.style.SUCCESS('✅ Superuser \'admin\' created successfully.'))

            Profile.objects.create(
                user=adminUser,
                jobTitle=random.choice(Profile.JobTitle.values),
                department='Engineering'
            )
            self.stdout.write(self.style.SUCCESS('✅ Profile for \'admin\' created successfully.'))

        except IntegrityError:
            self.stdout.write(self.style.WARNING('⚠️ Admin user already exists. Skipping creation.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Unexpected error: {e}'))

        self.stdout.write(self.style.SUCCESS('🎉 Admin user setup complete.'))
