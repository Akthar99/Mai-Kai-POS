"""
Management command to perform security audit
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Perform security audit on the Django project'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('MAI KAI POS - SECURITY AUDIT'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        issues = []
        warnings = []
        passed = []
        
        # Check DEBUG mode
        if settings.DEBUG:
            issues.append('❌ DEBUG is True - MUST be False in production')
        else:
            passed.append('✅ DEBUG is correctly set to False')
        
        # Check SECRET_KEY
        if settings.SECRET_KEY == 'django-insecure-change-this-in-production':
            issues.append('❌ SECRET_KEY is using default value - MUST be changed')
        else:
            passed.append('✅ SECRET_KEY appears to be customized')
        
        # Check ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
            issues.append('❌ ALLOWED_HOSTS is not properly configured')
        else:
            passed.append(f'✅ ALLOWED_HOSTS configured: {", ".join(settings.ALLOWED_HOSTS)}')
        
        # Check HTTPS settings
        if not settings.DEBUG:
            if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
                warnings.append('⚠️  SECURE_SSL_REDIRECT not enabled')
            else:
                passed.append('✅ SECURE_SSL_REDIRECT enabled')
            
            if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
                warnings.append('⚠️  SESSION_COOKIE_SECURE not enabled')
            else:
                passed.append('✅ SESSION_COOKIE_SECURE enabled')
            
            if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
                warnings.append('⚠️  CSRF_COOKIE_SECURE not enabled')
            else:
                passed.append('✅ CSRF_COOKIE_SECURE enabled')
        
        # Check HSTS
        if getattr(settings, 'SECURE_HSTS_SECONDS', 0) > 0:
            passed.append(f'✅ HSTS enabled ({settings.SECURE_HSTS_SECONDS} seconds)')
        else:
            warnings.append('⚠️  HSTS not enabled')
        
        # Check password validators
        validators = settings.AUTH_PASSWORD_VALIDATORS
        if len(validators) >= 4:
            passed.append(f'✅ Password validators configured ({len(validators)} validators)')
        else:
            warnings.append(f'⚠️  Only {len(validators)} password validators configured')
        
        # Check for .env file
        env_path = os.path.join(settings.BASE_DIR, '.env')
        if os.path.exists(env_path):
            passed.append('✅ .env file exists')
        else:
            issues.append('❌ .env file not found - create one from .env.example')
        
        # Check database
        db_engine = settings.DATABASES['default']['ENGINE']
        if 'sqlite3' in db_engine and not settings.DEBUG:
            warnings.append('⚠️  Using SQLite in production - consider PostgreSQL')
        elif 'sqlite3' not in db_engine:
            passed.append(f'✅ Using production database: {db_engine}')
        
        # Check static files
        if hasattr(settings, 'STATICFILES_STORAGE'):
            passed.append('✅ Static files storage configured')
        else:
            warnings.append('⚠️  STATICFILES_STORAGE not configured')
        
        # Check admin URL
        admin_url = getattr(settings, 'ADMIN_URL', 'admin/')
        if admin_url == 'admin/':
            warnings.append('⚠️  Admin URL is default "admin/" - consider changing for security')
        else:
            passed.append(f'✅ Custom admin URL configured')
        
        # Print results
        if passed:
            self.stdout.write(self.style.SUCCESS('\n✅ PASSED CHECKS:'))
            for item in passed:
                self.stdout.write(f'  {item}')
        
        if warnings:
            self.stdout.write(self.style.WARNING('\n⚠️  WARNINGS:'))
            for item in warnings:
                self.stdout.write(f'  {item}')
        
        if issues:
            self.stdout.write(self.style.ERROR('\n❌ CRITICAL ISSUES:'))
            for item in issues:
                self.stdout.write(f'  {item}')
        
        # Summary
        self.stdout.write('\n' + '='*70)
        total = len(passed) + len(warnings) + len(issues)
        self.stdout.write(f'\nSummary: {len(passed)}/{total} checks passed')
        
        if issues:
            self.stdout.write(self.style.ERROR(f'{len(issues)} critical issue(s) found - FIX BEFORE DEPLOYMENT'))
        elif warnings:
            self.stdout.write(self.style.WARNING(f'{len(warnings)} warning(s) - Review recommended'))
        else:
            self.stdout.write(self.style.SUCCESS('All security checks passed! ✅'))
        
        self.stdout.write('='*70 + '\n')
        
        # Return exit code
        if issues:
            exit(1)
