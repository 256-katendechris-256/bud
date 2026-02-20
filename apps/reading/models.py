from django.conf import settings
from django.db import models


class UserBook(models.Model):
    STATUS_CHOICES = [
        ('WANT_TO_READ', 'Want to Read'),
        ('READING', 'Reading'),
        ('FINISHED', 'Finished'),
        ('DROPPED', 'Dropped'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_books',
    )
    book = models.ForeignKey(
        'books.Book',
        on_delete=models.CASCADE,
        related_name='user_books',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='WANT_TO_READ')
    current_page = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user} — {self.book.title} ({self.status})"


class ReadingSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reading_sessions',
    )
    book = models.ForeignKey(
        'books.Book',
        on_delete=models.CASCADE,
        related_name='reading_sessions',
    )
    user_book = models.ForeignKey(
        UserBook,
        on_delete=models.CASCADE,
        related_name='sessions',
    )
    start_page = models.PositiveIntegerField()
    end_page = models.PositiveIntegerField()
    pages_read = models.PositiveIntegerField()
    duration_minutes = models.PositiveIntegerField(default=0)
    xp_earned = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} read {self.pages_read}pg of {self.book.title}"
