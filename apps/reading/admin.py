from django.contrib import admin

from .models import UserBook, ReadingSession


@admin.register(UserBook)
class UserBookAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'status', 'current_page', 'started_at', 'finished_at')
    list_filter = ('status', 'started_at')
    search_fields = ('user__username', 'user__email', 'book__title')
    raw_id_fields = ('user', 'book')


@admin.register(ReadingSession)
class ReadingSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'pages_read', 'duration_minutes', 'xp_earned', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'book__title')
    raw_id_fields = ('user', 'book', 'user_book')
