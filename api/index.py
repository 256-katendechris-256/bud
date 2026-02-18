import os
import sys
from pathlib import Path

# Ensure project root is on the path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Run collectstatic on cold start (Vercel serverless)
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()

# Collect static files into STATIC_ROOT on first load
_static_root = BASE_DIR / "staticfiles"
if not _static_root.exists():
    try:
        call_command("collectstatic", "--noinput", verbosity=0)
    except Exception:
        pass
