import environ
from pathlib import Path

from .base import *

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

DEBUG = False

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['.vercel.app', 'localhost', '127.0.0.1'])

# Avoid hard dependency on database-backed session tables in serverless runtime.
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}
WHITENOISE_MANIFEST_STRICT = False

_database_url = env('DATABASE_URL', default='')
if _database_url:
    DATABASES = {
        'default': env.db_url('DATABASE_URL'),
    }
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS'].setdefault('sslmode', env('DB_SSLMODE', default='require'))
else:
    _db_name = env('SUPABASE_DB_NAME', default='')
    _db_user = env('SUPABASE_DB_USER', default='')
    _db_password = env('SUPABASE_DB_PASSWORD', default='')
    _db_host = env('SUPABASE_DB_HOST', default='')
    _db_port = env('SUPABASE_DB_PORT', default='')

    if all([_db_name, _db_user, _db_password, _db_host, _db_port]):
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': _db_name,
                'USER': _db_user,
                'PASSWORD': _db_password,
                'HOST': _db_host,
                'PORT': _db_port,
                'OPTIONS': {
                    'sslmode': env('DB_SSLMODE', default='require'),
                },
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': Path('/tmp') / 'bud.sqlite3',
            }
        }

# Cache - Upstash Redis
_redis_url = env('REDIS_URL', default='')
if _redis_url:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _redis_url,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'bud-prod-cache-fallback',
        }
    }
