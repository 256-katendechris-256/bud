import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / '.env', override=True)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.base"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['SUPABASE_DB_NAME'],
        'USER': os.environ['SUPABASE_DB_USER'],
        'PASSWORD': os.environ['SUPABASE_DB_PASSWORD'],
        'HOST': os.environ['SUPABASE_DB_HOST'],
        'PORT': os.environ['SUPABASE_DB_PORT'],
        'OPTIONS': {'sslmode': 'require'},
    }
}

from django.conf import settings
settings.DATABASES = DATABASES

import django
from django import db
db.connections = db.ConnectionHandler(DATABASES)
django.setup()

from django.core.management import call_command
call_command('migrate', verbosity=1)
