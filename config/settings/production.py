import environ
from pathlib import Path

from .base import *

env = environ.Env()

# Read .env file if it exists (won't exist on Vercel — use env vars there)
_env_file = BASE_DIR / '.env'
if _env_file.is_file():
    environ.Env.read_env(_env_file)

DEBUG = False

SECRET_KEY = env('SECRET_KEY', default=SECRET_KEY)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['.vercel.app', 'localhost', '127.0.0.1'])

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

# Database
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
                'OPTIONS': {'sslmode': 'require'},
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': Path('/tmp') / 'bud.sqlite3',
            }
        }

# Cache
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

# S3/Supabase Storage
AWS_ACCESS_KEY_ID        = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY    = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME  = env('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME       = env('AWS_S3_REGION_NAME', default='eu-west-1')
AWS_S3_ENDPOINT_URL      = env('AWS_S3_ENDPOINT_URL')
AWS_DEFAULT_ACL          = 'public-read'
AWS_S3_FILE_OVERWRITE    = False
AWS_QUERYSTRING_AUTH     = False
AWS_S3_SIGNATURE_VERSION = 's3v4'

# ✅ Force Supabase public URL format instead of S3 signed URLs
AWS_S3_CUSTOM_DOMAIN = f"{env('AWS_S3_ENDPOINT_URL').replace('https://', '').replace('/storage/v1/s3', '')}/storage/v1/object/public/{env('AWS_STORAGE_BUCKET_NAME')}"

# ✅ Single STORAGES definition — no duplicate
STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
    },
'staticfiles': {
    'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
},
}

MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Email
EMAIL_BACKEND     = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST        = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT        = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS     = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL     = env.bool('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER   = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_TIMEOUT     = env.int('EMAIL_TIMEOUT', default=30)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER or 'noreply@budapp.com')
FRONTEND_URL      = env('FRONTEND_URL', default='https://bud-ruby.vercel.app')

# Google OAuth
GOOGLE_CLIENT_ID = env('GOOGLE_CLIENT_ID', default='')