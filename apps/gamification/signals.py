from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.reading.models import ReadingSession


@receiver(post_save, sender=ReadingSession)
def update_gamification(sender, instance, created, **kwargs):
    if not created:
        return

    from .models import UserGamification, Badge
    from notifications.tasks import notify_league_overtake

    gamification, _ = UserGamification.objects.get_or_create(
        user=instance.user
    )

    old_xp = gamification.total_xp

    gamification.record_session(
        pages_read      = instance.pages_read,
        duration_minutes= instance.duration_minutes,
        xp_earned       = instance.xp_earned,
    )

    # Check badge unlocks
    _check_badges(instance.user, gamification)

    # Check league overtake
    from .models import UserGamification as UG
    above = (
        UG.objects
        .filter(total_xp__gt=old_xp, total_xp__lte=gamification.total_xp)
        .exclude(user=instance.user)
        .order_by('total_xp')
        .first()
    )
    if above:
        notify_league_overtake.delay(
            overtaker_id=instance.user.id,
            overtaken_id=above.user.id,
        )


def _check_badges(user, gamification):
    from .models import Badge
    from notifications.tasks import notify_achievement

    checks = [
        ('pages_100',   gamification.total_pages_read >= 100),
        ('pages_1000',  gamification.total_pages_read >= 1000),
        ('xp_500',      gamification.total_xp >= 500),
        ('xp_5000',     gamification.total_xp >= 5000),
        ('streak_7',    gamification.current_streak >= 7),
        ('streak_30',   gamification.current_streak >= 30),
        ('books_finished', gamification.books_finished >= 1),
    ]

    for badge_type, condition in checks:
        if condition:
            badge, created = Badge.objects.get_or_create(
                user=user, badge_type=badge_type
            )
            if created:
                notify_achievement.delay(
                    user_id   =user.id,
                    badge_type=badge_type,
                )