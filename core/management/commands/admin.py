from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import IntegrityError


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
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
        except IntegrityError:
            pass
