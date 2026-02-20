from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Book(models.Model):
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=500)
    isbn_10 = models.CharField(max_length=10, null=True, blank=True, unique=True)
    isbn_13 = models.CharField(max_length=13, null=True, blank=True, unique=True)
    total_pages = models.PositiveIntegerField(default=0)
    cover_url = models.URLField(max_length=500, blank=True, default='')
    description = models.TextField(blank=True, default='')
    publisher = models.CharField(max_length=300, blank=True, default='')
    published_date = models.CharField(max_length=20, blank=True, default='')
    language = models.CharField(max_length=10, default='en')
    google_books_id = models.CharField(max_length=40, null=True, blank=True, unique=True)
    file = models.FileField(
        upload_to='books/pdfs/', blank=True, null=True,
        validators=[FileExtensionValidator(['pdf'])],
    )
    genres = models.ManyToManyField(Genre, blank=True, related_name='books')
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_books',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.author}"
