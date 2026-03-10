import json
import logging
from django.http  import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf  import settings
from qstash       import Receiver

logger = logging.getLogger(__name__)


def _verify_qstash(request) -> bool:
    """Verify the request genuinely came from QStash."""
    receiver = Receiver(
        current_signing_key = settings.QSTASH_CURRENT_SIGNING_KEY,
        next_signing_key    = settings.QSTASH_NEXT_SIGNING_KEY,
    )
    try:
        receiver.verify(
            signature = request.headers.get('Upstash-Signature', ''),
            body      = request.body.decode(),
            url       = request.build_absolute_uri(),
        )
        return True
    except Exception as e:
        logger.warning(f'QStash signature verification failed: {e}')
        return False


@csrf_exempt
@require_POST
def cron_check_streaks(request):
    if not _verify_qstash(request):
        return JsonResponse({'error': 'unauthorized'}, status=401)
    try:
        from .tasks import check_streaks
        check_streaks()
        return JsonResponse({'status': 'streak check complete'})
    except Exception as e:
        logger.error(f'cron_check_streaks failed: {e}')
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def cron_midnight_sos(request):
    if not _verify_qstash(request):
        return JsonResponse({'error': 'unauthorized'}, status=401)
    try:
        from .tasks import midnight_sos
        midnight_sos()
        return JsonResponse({'status': 'midnight SOS complete'})
    except Exception as e:
        logger.error(f'cron_midnight_sos failed: {e}')
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def cron_daily_reminders(request):
    if not _verify_qstash(request):
        return JsonResponse({'error': 'unauthorized'}, status=401)
    try:
        from .tasks import send_daily_reminders
        send_daily_reminders()
        return JsonResponse({'status': 'daily reminders sent'})
    except Exception as e:
        logger.error(f'cron_daily_reminders failed: {e}')
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def cron_weekly_digest(request):
    if not _verify_qstash(request):
        return JsonResponse({'error': 'unauthorized'}, status=401)
    try:
        from .tasks import weekly_digest
        weekly_digest()
        return JsonResponse({'status': 'weekly digest sent'})
    except Exception as e:
        logger.error(f'cron_weekly_digest failed: {e}')
        return JsonResponse({'error': str(e)}, status=500)