from django.conf import settings
from django.db import models
from django.utils import timezone


class UserGamification(models.Model):
    user            = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gamification',
    )
    total_xp        = models.PositiveIntegerField(default=0)
    current_streak  = models.PositiveIntegerField(default=0)
    longest_streak  = models.PositiveIntegerField(default=0)
    books_finished  = models.PositiveIntegerField(default=0)
    total_pages_read= models.PositiveIntegerField(default=0)
    total_time_hours= models.FloatField(default=0.0)
    last_read_date  = models.DateField(null=True, blank=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} — {self.total_xp} XP — {self.current_streak} day streak"

    def record_session(self, pages_read: int, duration_minutes: int, xp_earned: int):
        """
        Called every time a ReadingSession is saved.
        Updates streak, XP, pages, and time in one place.
        """
        today = timezone.now().date()

        # Streak logic
        if self.last_read_date is None:
            self.current_streak = 1
        elif self.last_read_date == today:
            pass  # already read today — streak unchanged
        elif self.last_read_date == today - timezone.timedelta(days=1):
            self.current_streak += 1  # consecutive day
        else:
            self.current_streak = 1   # broke the streak, reset

        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

        self.last_read_date   = today
        self.total_xp        += xp_earned
        self.total_pages_read += pages_read
        self.total_time_hours += round(duration_minutes / 60, 2)
        self.save()


class Badge(models.Model):
    BADGE_CHOICES = [
        ('first_book',    'First Book Finished'),
        ('streak_7',      '7-Day Streak'),
        ('streak_30',     '30-Day Streak'),
        ('pages_100',     '100 Pages Read'),
        ('pages_1000',    '1,000 Pages Read'),
        ('xp_500',        '500 XP Earned'),
        ('xp_5000',       '5,000 XP Earned'),
        ('night_owl',     'Night Owl — read after 10PM'),
        ('early_bird',    'Early Bird — read before 7AM'),
        ('speed_reader',  'Speed Reader — 50 pages in one session'),
    ]

    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='badges',
    )
    badge_type = models.CharField(max_length=30, choices=BADGE_CHOICES)
    earned_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge_type')
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.user.username} — {self.badge_type}"