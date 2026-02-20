from rest_framework import serializers

from apps.books.serializers import BookListSerializer

from .models import UserBook, ReadingSession


class UserBookSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    progress_percent = serializers.SerializerMethodField()

    class Meta:
        model = UserBook
        fields = (
            'id', 'book', 'status', 'current_page',
            'started_at', 'finished_at', 'progress_percent',
            'created_at', 'updated_at',
        )

    def get_progress_percent(self, obj):
        if obj.book.total_pages and obj.book.total_pages > 0:
            return round((obj.current_page / obj.book.total_pages) * 100, 1)
        return 0


class ReadingSessionSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)

    class Meta:
        model = ReadingSession
        fields = (
            'id', 'book', 'book_title', 'start_page', 'end_page',
            'pages_read', 'duration_minutes', 'xp_earned', 'created_at',
        )


class LogSessionSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    start_page = serializers.IntegerField(min_value=0)
    end_page = serializers.IntegerField(min_value=0)
    duration_minutes = serializers.IntegerField(min_value=0)

    def validate(self, data):
        if data['end_page'] < data['start_page']:
            raise serializers.ValidationError("end_page must be >= start_page")
        return data


class ReadingStatsSerializer(serializers.Serializer):
    total_xp = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    books_finished = serializers.IntegerField()
    total_time_hours = serializers.FloatField()
