import os

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

_ON_VERCEL = bool(os.environ.get('VERCEL'))


def _run(task, **kwargs):
    if _ON_VERCEL:
        task(**kwargs)
    else:
        task.delay(**kwargs)


@receiver(post_save, sender=User)
def create_notification_preference(sender, instance, created, **kwargs):
    """Auto-create prefs for every new user."""
    if created:
        from .models import NotificationPreference
        NotificationPreference.objects.get_or_create(user=instance)


@receiver(post_save, sender='gamification.UserGamification')
def check_league_overtake(sender, instance, **kwargs):
    """
    Fire league overtake notification when XP is updated.
    Checks if this user just passed the person directly above them.
    """
    from .tasks import notify_league_overtake

    UserGamification = sender
    above = (
        UserGamification.objects
        .filter(total_xp__gt=instance.total_xp)
        .order_by('total_xp')
        .first()
    )
    if not above:
        return

    # Only fire if the gap is very small — just overtook them
    if instance.total_xp - above.total_xp <= 50:
        _run(
            notify_league_overtake,
            overtaker_id=instance.user_id,
            overtaken_id=above.user_id,
        )