import os


_settings_module = os.getenv("DJANGO_SETTINGS_MODULE", "")
_django_env = os.getenv("DJANGO_ENV", "").lower()

if _settings_module.endswith(".production") or _django_env == "production":
    from .production import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403
