"""
WSGI config for maikai_pos project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maikai_pos.settings')

application = get_wsgi_application()
