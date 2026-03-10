from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@shared_task
def check_streaks():
    """
    Runs at 9PM — warns users who haven't read today
    and still have an active streak to protect.
    """
    from .models import NotificationPreference, NotificationLog
    from .services import send_push
    from apps.reading.models import ReadingSession

    today = timezone.now().date()

    prefs = NotificationPreference.objects.filter(
        streak_alerts=True
    ).select_related('user')

    for pref in prefs:
        user = pref.user

        # ReadingSession uses created_at — filter by date portion
        already_read = ReadingSession.objects.filter(
            user=user,
            created_at__date=today,
        ).exists()
        if already_read:
            continue

        # Skip if streak is 0 — nothing to lose
        gamification = getattr(user, 'gamification', None)
        streak = getattr(gamification, 'current_streak', 0) if gamification else 0
        if streak == 0:
            continue

        title = "Your streak is at risk 🔥"
        body  = f"You have a {streak}-day streak — don't lose it! Open your book now."

        send_push(user, title, body, data={'type': 'streak', 'urgency': 'medium'})

        NotificationLog.objects.create(
            user       = user,
            notif_type = 'streak',
            urgency    = 'medium',
            title      = title,
            body       = body,
        )


@shared_task
def midnight_sos():
    """
    Runs at 11:30PM — final urgent warning for users
    who still haven't read and have a streak > 0.
    """
    from .models import NotificationPreference, NotificationLog
    from .services import send_push
    from apps.reading.models import ReadingSession

    today = timezone.now().date()

    prefs = NotificationPreference.objects.filter(
        streak_alerts=True
    ).select_related('user')

    for pref in prefs:
        user = pref.user

        already_read = ReadingSession.objects.filter(
            user=user,
            created_at__date=today,
        ).exists()
        if already_read:
            continue

        gamification = getattr(user, 'gamification', None)
        streak = getattr(gamification, 'current_streak', 0) if gamification else 0
        if streak == 0:
            continue

        title = "Last chance! 🚨"
        body  = f"30 minutes left! Read just 1 page to save your {streak}-day streak."

        send_push(user, title, body, data={'type': 'streak', 'urgency': 'high'})

        NotificationLog.objects.create(
            user       = user,
            notif_type = 'streak',
            urgency    = 'high',
            title      = title,
            body       = body,
        )


@shared_task
def send_daily_reminders():
    """
    Runs every hour — sends reminder only to users
    whose reminder_time matches the current hour.
    """
    from .models import NotificationPreference, NotificationLog
    from .services import send_push

    current_hour = timezone.now().astimezone(
        timezone.get_current_timezone()
    ).hour

    prefs = NotificationPreference.objects.filter(
        goal_reminders=True,
        reminder_time__hour=current_hour,
    ).select_related('user')

    for pref in prefs:
        user = pref.user

        title = "Time to read 📖"
        body  = "Your daily reading reminder — even 10 minutes counts."

        send_push(user, title, body, data={'type': 'goal', 'urgency': 'low'})

        NotificationLog.objects.create(
            user       = user,
            notif_type = 'goal',
            urgency    = 'low',
            title      = title,
            body       = body,
        )


@shared_task
def weekly_digest():
    """
    Runs every Sunday at 6PM — sends each user
    a summary of their week.
    """
    from .models import NotificationPreference, NotificationLog
    from .services import send_push
    from apps.reading.models import ReadingSession

    prefs = NotificationPreference.objects.filter(
        goal_reminders=True
    ).select_related('user')

    week_ago = timezone.now().date() - timedelta(days=7)

    for pref in prefs:
        user = pref.user

        sessions = ReadingSession.objects.filter(
            user=user,
            created_at__date__gte=week_ago,
        )

        total_pages  = sum(s.pages_read for s in sessions)
        # count distinct days using created_at date
        days_read    = sessions.dates('created_at', 'day').count()
        gamification = getattr(user, 'gamification', None)
        streak       = getattr(gamification, 'current_streak', 0) if gamification else 0
        xp           = getattr(gamification, 'total_xp', 0) if gamification else 0

        if total_pages == 0:
            title = "Start your reading week 📚"
            body  = "You didn't read this week. A fresh week starts now — open a book!"
        else:
            title = "Your week in books 📊"
            body  = (
                f"{days_read} days read · {total_pages} pages · "
                f"{streak} day streak · {xp} XP earned"
            )

        send_push(user, title, body, data={'type': 'goal', 'urgency': 'low'})

        NotificationLog.objects.create(
            user       = user,
            notif_type = 'goal',
            urgency    = 'low',
            title      = title,
            body       = body,
        )


@shared_task
def notify_league_overtake(overtaker_id: int, overtaken_id: int):
    """
    Called from a signal when a user surpasses another in XP.
    Notifies the overtaken user so they feel the competition.
    """
    from .models import NotificationPreference, NotificationLog
    from .services import send_push

    try:
        overtaker = User.objects.get(id=overtaker_id)
        overtaken = User.objects.get(id=overtaken_id)
    except User.DoesNotExist:
        return

    pref = NotificationPreference.objects.filter(
        user=overtaken, league_alerts=True
    ).first()
    if not pref:
        return

    title = "You've been overtaken! ⚔️"
    body  = f"{overtaker.username} just passed you in the league. Fight back!"

    send_push(overtaken, title, body, data={'type': 'league', 'urgency': 'medium'})

    NotificationLog.objects.create(
        user       = overtaken,
        notif_type = 'league',
        urgency    = 'medium',
        title      = title,
        body       = body,
    )

@shared_task
def notify_achievement(user_id: int, badge_type: str):
    from .models import NotificationLog
    from .services import send_push

    BADGE_LABELS = {
        'first_book'   : ('First book finished! 📚', 'You completed your first book. Keep going!'),
        'streak_7'     : ('7-Day Streak! 🔥',         'A whole week of reading. You\'re on fire!'),
        'streak_30'    : ('30-Day Streak! 🏆',         'A month straight. Legendary dedication.'),
        'pages_100'    : ('100 Pages Read! 📖',        'You\'ve read 100 pages. Just the beginning.'),
        'pages_1000'   : ('1,000 Pages Read! 🎉',      'Four digits. You\'re a real reader now.'),
        'xp_500'       : ('500 XP Earned! ⭐',         'Halfway to 1,000. Keep earning!'),
        'xp_5000'      : ('5,000 XP Earned! 👑',       'Elite reader status unlocked.'),
        'speed_reader' : ('Speed Reader! ⚡',           '50 pages in one session. Impressive.'),
    }

    title, body = BADGE_LABELS.get(badge_type, ('Badge Unlocked! 🏅', 'You earned a new badge.'))

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    send_push(user, title, body, data={'type': 'achievement', 'badge': badge_type})

    NotificationLog.objects.create(
        user       = user,
        notif_type = 'achievement',
        urgency    = 'low',
        title      = title,
        body       = body,
        data       = {'badge_type': badge_type},
    )