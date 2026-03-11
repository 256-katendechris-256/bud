from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class FCMToken(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_tokens')
    token      = models.CharField(max_length=500, unique=True)
    last_seen  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} — {self.token[:20]}..."


class NotificationPreference(models.Model):
    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_prefs')
    streak_alerts    = models.BooleanField(default=True)
    league_alerts    = models.BooleanField(default=True)
    goal_reminders   = models.BooleanField(default=True)
    reminder_time    = models.TimeField(default='07:00')
    last_reminder_date = models.DateField(null=True, blank=True)
    timezone         = models.CharField(max_length=50, default='Africa/Kampala')

    def __str__(self):
        return f"{self.user.username} prefs"


class NotificationLog(models.Model):
    TYPE_CHOICES = [
        ('streak',      'Streak'),
        ('league',      'League'),
        ('goal',        'Goal'),
        ('achievement', 'Achievement'),
        ('bookclub',    'Book Club'),
    ]
    URGENCY_CHOICES = [
        ('low',    'Low'),
        ('medium', 'Medium'),
        ('high',   'High'),
    ]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    urgency    = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='low')
    title      = models.CharField(max_length=255)
    body       = models.TextField()
    data       = models.JSONField(default=dict, blank=True)
    sent_at    = models.DateTimeField(auto_now_add=True)
    opened     = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.user.username} — {self.notif_type} — {self.title}"