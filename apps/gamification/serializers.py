from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserGamification, Badge

User = get_user_model()


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    """Serializer for leaderboard entries."""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    display_name = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()
    is_current_user = serializers.SerializerMethodField()

    class Meta:
        model = UserGamification
        fields = [
            'user_id',
            'username',
            'first_name',
            'display_name',
            'total_xp',
            'current_streak',
            'books_finished',
            'total_pages_read',
            'rank',
            'is_current_user',
        ]

    def get_display_name(self, obj):
        if obj.user.first_name:
            return obj.user.first_name
        if obj.user.username:
            return obj.user.username
        return obj.user.email.split('@')[0] if obj.user.email else 'Reader'

    def get_rank(self, obj):
        return getattr(obj, 'rank', None)

    def get_is_current_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user_id == request.user.id
        return False


class UserGamificationSerializer(serializers.ModelSerializer):
    """Full gamification profile serializer."""
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = UserGamification
        fields = [
            'total_xp',
            'current_streak',
            'longest_streak',
            'books_finished',
            'total_pages_read',
            'total_time_hours',
            'last_read_date',
            'display_name',
        ]

    def get_display_name(self, obj):
        if obj.user.first_name:
            return obj.user.first_name
        if obj.user.username:
            return obj.user.username
        return obj.user.email.split('@')[0] if obj.user.email else 'Reader'


class BadgeSerializer(serializers.ModelSerializer):
    """Serializer for user badges."""
    badge_label = serializers.SerializerMethodField()

    class Meta:
        model = Badge
        fields = ['badge_type', 'badge_label', 'earned_at']

    def get_badge_label(self, obj):
        return dict(Badge.BADGE_CHOICES).get(obj.badge_type, obj.badge_type)
