"""
Management command to generate a secure SECRET_KEY
"""
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = 'Generate a new SECRET_KEY for production use'

    def handle(self, *args, **options):
        secret_key = get_random_secret_key()
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('Generated new SECRET_KEY:'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(f'\n{secret_key}\n')
        self.stdout.write(self.style.WARNING('\n⚠️  IMPORTANT: Copy this key to your .env file'))
        self.stdout.write(self.style.WARNING('Add this line to your .env file:'))
        self.stdout.write(f'\nSECRET_KEY={secret_key}\n')
        self.stdout.write(self.style.WARNING('Keep this key secret and never commit it to version control!'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
