import urllib.request
import urllib.parse
import json

from django.conf import settings
from django.db.models import Q

from .models import Book, Genre


class GoogleBooksAPIError(Exception):
    """Raised when the Google Books API call fails."""


class GoogleBooksService:

    BASE_URL = 'https://www.googleapis.com/books/v1/volumes'

    @staticmethod
    def search(query, max_results=10):
        params = {
            'q': query,
            'maxResults': max_results,
            'printType': 'books',
        }
        api_key = getattr(settings, 'GOOGLE_BOOKS_API_KEY', '').strip()
        if api_key:
            params['key'] = api_key

        url = f"{GoogleBooksService.BASE_URL}?{urllib.parse.urlencode(params)}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Bud/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
        except Exception as exc:
            raise GoogleBooksAPIError(
                'Google Books is temporarily unavailable. '
                'Check your internet connection or try again later.'
            ) from exc

        items = data.get('items', [])
        return [GoogleBooksService._normalize(item) for item in items]

    @staticmethod
    def fetch_by_id(google_books_id):
        url = f"{GoogleBooksService.BASE_URL}/{google_books_id}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Bud/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
        except Exception:
            return None

        return GoogleBooksService._normalize(data)

    @staticmethod
    def _normalize(volume_data):
        info = volume_data.get('volumeInfo', {})
        identifiers = {i['type']: i['identifier'] for i in info.get('industryIdentifiers', [])}

        # Prefer HTTPS thumbnail, bump to medium size
        cover = ''
        image_links = info.get('imageLinks', {})
        if image_links:
            cover = image_links.get('thumbnail', image_links.get('smallThumbnail', ''))
            cover = cover.replace('http://', 'https://')
            cover = cover.replace('&edge=curl', '')

        return {
            'google_books_id': volume_data.get('id', ''),
            'title': info.get('title', 'Unknown Title'),
            'author': ', '.join(info.get('authors', ['Unknown Author'])),
            'isbn_10': identifiers.get('ISBN_10'),
            'isbn_13': identifiers.get('ISBN_13'),
            'total_pages': info.get('pageCount', 0) or 0,
            'cover_url': cover,
            'description': info.get('description', ''),
            'publisher': info.get('publisher', ''),
            'published_date': info.get('publishedDate', ''),
            'language': info.get('language', 'en'),
            'categories': info.get('categories', []),
        }


class BookCatalogService:

    @staticmethod
    def add_from_google(google_books_id, user=None):
        existing = Book.objects.filter(google_books_id=google_books_id).first()
        if existing:
            return existing, False

        data = GoogleBooksService.fetch_by_id(google_books_id)
        if not data:
            return None, False

        book = Book.objects.create(
            title=data['title'],
            author=data['author'],
            isbn_10=data['isbn_10'] or None,
            isbn_13=data['isbn_13'] or None,
            total_pages=data['total_pages'],
            cover_url=data['cover_url'],
            description=data['description'],
            publisher=data['publisher'],
            published_date=data['published_date'],
            language=data['language'],
            google_books_id=data['google_books_id'],
            added_by=user,
        )

        # Save Google Books categories as Genre objects
        for cat in data.get('categories', []):
            genre, _ = Genre.objects.get_or_create(name=cat.strip())
            book.genres.add(genre)

        return book, True

    @staticmethod
    def search_catalog(query):
        if not query:
            return Book.objects.all()
        return Book.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        )
