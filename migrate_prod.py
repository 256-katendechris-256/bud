import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / '.env', override=True)

from django.conf import settings

settings.configure(
    BASE_DIR=BASE_DIR,
    INSTALLED_APPS=[
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'rest_framework',
        'corsheaders',
        'notifications',
        'apps.accounts',
        'apps.books',
        'apps.reading',
        'apps.clubs',
        'apps.discussions',
        'apps.gamification',
    ],
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['SUPABASE_DB_NAME'],
            'USER': os.environ['SUPABASE_DB_USER'],
            'PASSWORD': os.environ['SUPABASE_DB_PASSWORD'],
            'HOST': os.environ['SUPABASE_DB_HOST'],
            'PORT': os.environ['SUPABASE_DB_PORT'],
            'OPTIONS': {'sslmode': 'require'},
        }
    },
    AUTH_USER_MODEL='accounts.User',
    DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
)

import django
django.setup()

from django.core.management import call_command
call_command('migrate', verbosity=2)
