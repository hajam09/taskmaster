from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '💣 Completely deletes ALL data from the Django database (including auth, sessions, admin logs).'

    def handle(self, *args, **kwargs):
        self.stdout.write('\n💣 Nuking database using Django flush...\n')
        call_command('flush', interactive=False)
        self.stdout.write('🔥 Database fully reset.\n')
