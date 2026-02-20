from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from apps.books.models import Book

from .models import UserBook, ReadingSession


class ReadingService:

    @staticmethod
    def calculate_xp(pages_read, duration_minutes):
        base_xp = pages_read * 2
        if duration_minutes >= 60:
            return int(base_xp * 2)
        elif duration_minutes >= 30:
            return int(base_xp * 1.5)
        return base_xp

    @staticmethod
    def start_reading(user, book_id):
        book = Book.objects.get(id=book_id)
        user_book, created = UserBook.objects.get_or_create(
            user=user,
            book=book,
            defaults={'status': 'READING', 'started_at': timezone.now()},
        )
        if not created and user_book.status != 'READING':
            user_book.status = 'READING'
            if not user_book.started_at:
                user_book.started_at = timezone.now()
            user_book.finished_at = None
            user_book.save(update_fields=['status', 'started_at', 'finished_at', 'updated_at'])
        return user_book

    @staticmethod
    def log_session(user, book_id, start_page, end_page, duration_minutes):
        book = Book.objects.get(id=book_id)
        user_book, _ = UserBook.objects.get_or_create(
            user=user,
            book=book,
            defaults={'status': 'READING', 'started_at': timezone.now()},
        )

        pages_read = max(0, end_page - start_page)
        xp_earned = ReadingService.calculate_xp(pages_read, duration_minutes)

        session = ReadingSession.objects.create(
            user=user,
            book=book,
            user_book=user_book,
            start_page=start_page,
            end_page=end_page,
            pages_read=pages_read,
            duration_minutes=duration_minutes,
            xp_earned=xp_earned,
        )

        # Update current page
        user_book.current_page = end_page
        if user_book.status != 'READING':
            user_book.status = 'READING'
            if not user_book.started_at:
                user_book.started_at = timezone.now()

        # Auto-finish if reached total pages
        if book.total_pages > 0 and end_page >= book.total_pages:
            user_book.status = 'FINISHED'
            user_book.finished_at = timezone.now()

        user_book.save()
        return session

    @staticmethod
    def get_reading_stats(user):
        total_xp = ReadingSession.objects.filter(user=user).aggregate(
            total=Sum('xp_earned')
        )['total'] or 0

        books_finished = UserBook.objects.filter(user=user, status='FINISHED').count()

        total_minutes = ReadingSession.objects.filter(user=user).aggregate(
            total=Sum('duration_minutes')
        )['total'] or 0

        current_streak = ReadingService._calculate_streak(user)

        return {
            'total_xp': total_xp,
            'current_streak': current_streak,
            'books_finished': books_finished,
            'total_time_hours': round(total_minutes / 60, 1),
        }

    @staticmethod
    def get_currently_reading(user):
        return UserBook.objects.filter(
            user=user,
            status='READING',
        ).select_related('book')

    @staticmethod
    def _calculate_streak(user):
        today = timezone.now().date()
        streak = 0
        day = today
        while True:
            has_session = ReadingSession.objects.filter(
                user=user,
                created_at__date=day,
            ).exists()
            if not has_session:
                break
            streak += 1
            day -= timedelta(days=1)
        return streak
