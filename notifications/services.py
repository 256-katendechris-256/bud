import json
import logging
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialise Firebase app once
if not firebase_admin._apps:
    if settings.FIREBASE_CREDENTIALS_JSON:
        raw = settings.FIREBASE_CREDENTIALS_JSON
        # Strip outer quotes if double-encoded
        if raw.startswith('"'):
            raw = json.loads(raw)
        cred_dict = json.loads(raw) if isinstance(raw, str) else raw
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

def send_push(user, title: str, body: str, data: dict = None):
    """
    Send a push notification to all FCM tokens registered for a user.
    Logs the notification and cleans up expired tokens automatically.
    """
    from .models import FCMToken, NotificationLog

    tokens = list(
        FCMToken.objects.filter(user=user).values_list('token', flat=True)
    )

    if not tokens:
        logger.info(f"No FCM tokens for user {user.username}, skipping push.")
        return

    data = {k: str(v) for k, v in (data or {}).items()}  # FCM requires string values

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data=data,
        tokens=tokens,
        android=messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                sound='default',
                click_action='FLUTTER_NOTIFICATION_CLICK',
            ),
        ),
    )

    try:
        response = messaging.send_each_for_multicast(message)
        logger.info(f"Sent to {response.success_count}/{len(tokens)} devices for {user.username}")

        # Remove tokens that are no longer valid
        if response.failure_count > 0:
            for idx, result in enumerate(response.responses):
                if not result.success:
                    FCMToken.objects.filter(token=tokens[idx]).delete()
                    logger.warning(f"Removed invalid token for {user.username}")

    except Exception as e:
        logger.error(f"FCM send failed for {user.username}: {e}")