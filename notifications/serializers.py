from rest_framework import serializers
from .models import FCMToken, NotificationPreference, NotificationLog


class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FCMToken
        fields = ['token']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = NotificationPreference
        fields = [
            'streak_alerts',
            'league_alerts',
            'goal_reminders',
            'reminder_time',
        ]


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = NotificationLog
        fields = [
            'id',
            'notif_type',
            'urgency',
            'title',
            'body',
            'data',
            'sent_at',
            'opened',
            'streak_alerts',
            'league_alerts',
            'goal_reminders',
            'reminder_time',
            'timezone'
        ]