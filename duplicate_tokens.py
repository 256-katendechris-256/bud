# Run this once: py migrate_prod.py (after adding this logic)
# Or run as a standalone script after setting up Django

import os, sys, django
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / '.env')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.base'

from django.conf import settings
settings.DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.postgresql',
        'NAME'    : os.environ['SUPABASE_DB_NAME'],
        'USER'    : os.environ['SUPABASE_DB_USER'],
        'PASSWORD': os.environ['SUPABASE_DB_PASSWORD'],
        'HOST'    : os.environ['SUPABASE_DB_HOST'],
        'PORT'    : os.environ['SUPABASE_DB_PORT'],
        'OPTIONS' : {'sslmode': 'require'},
    }
}
django.setup()

from notifications.models import FCMToken

# Show current state
print(f"Total FCM tokens: {FCMToken.objects.count()}")
for token in FCMToken.objects.select_related('user'):
    print(f"  User: {token.user.username} | Token: {token.token[:30]}...")

# Delete duplicates — keep only the latest token per user
from django.db.models import Max

print("\nRemoving duplicates...")
users_with_tokens = FCMToken.objects.values('user').distinct()
removed = 0
for entry in users_with_tokens:
    tokens = FCMToken.objects.filter(user_id=entry['user']).order_by('-id')
    if tokens.count() > 1:
        # Keep the first (newest), delete the rest
        to_delete = tokens[1:]
        count = to_delete.count()
        FCMToken.objects.filter(id__in=[t.id for t in to_delete]).delete()
        removed += count
        print(f"  Removed {count} duplicate(s) for user {entry['user']}")

print(f"\nDone. Removed {removed} duplicate tokens.")
print(f"Remaining tokens: {FCMToken.objects.count()}")