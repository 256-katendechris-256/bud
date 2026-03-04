import os
import sys
import django
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / '.env')

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.base"

import django
from django.conf import settings

settings.DATABASES = {
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

django.setup()

from django.core.management import execute_from_command_line
execute_from_command_line(["manage.py", "migrate"])
