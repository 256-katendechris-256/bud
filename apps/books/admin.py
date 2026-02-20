from django.contrib import admin

from .models import Book, Genre


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'total_pages', 'language', 'created_at')
    list_filter = ('genres', 'language', 'created_at')
    search_fields = ('title', 'author', 'isbn_10', 'isbn_13')
    filter_horizontal = ('genres',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
