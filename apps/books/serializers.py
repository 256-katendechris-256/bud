from rest_framework import serializers

from .models import Book, Genre


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'name', 'slug')


class BookListSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    file = serializers.SerializerMethodField()
    added_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Book
        fields = (
            'id', 'title', 'author', 'cover_url', 'total_pages',
            'description', 'publisher', 'published_date', 'language',
            'google_books_id', 'genres', 'file', 'added_by',
        )

    def get_file(self, obj):
        """Return file URL if it exists, otherwise None"""
        if obj.file:
            return obj.file.url
        return None


class BookDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    file = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = (
            'id', 'title', 'author', 'isbn_10', 'isbn_13',
            'total_pages', 'cover_url', 'description', 'publisher',
            'published_date', 'language', 'google_books_id',
            'genres', 'added_by', 'created_at', 'updated_at', 'file',
        )
        read_only_fields = ('added_by', 'created_at', 'updated_at')

    def get_file(self, obj):
        """Return file URL if it exists, otherwise None"""
        if obj.file:
            return obj.file.url
        return None


class BookFileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class GoogleBookResultSerializer(serializers.Serializer):
    google_books_id = serializers.CharField()
    title = serializers.CharField()
    author = serializers.CharField()
    isbn_10 = serializers.CharField(allow_null=True)
    isbn_13 = serializers.CharField(allow_null=True)
    total_pages = serializers.IntegerField()
    cover_url = serializers.CharField(allow_blank=True)
    description = serializers.CharField(allow_blank=True)
    publisher = serializers.CharField(allow_blank=True)
    published_date = serializers.CharField(allow_blank=True)
    language = serializers.CharField()
    categories = serializers.ListField(child=serializers.CharField(), required=False)
