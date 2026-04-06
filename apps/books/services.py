import logging
import urllib.parse
import requests

from django.core.cache import cache
from django.db.models import Q

from .models import Book, Genre

logger = logging.getLogger(__name__)


class GoogleBooksAPIError(Exception):
    """Raised when the Google Books API call fails."""


class OpenLibraryService:

    BASE_URL = "https://openlibrary.org/search.json"
    BASE_WORK_URL = "https://openlibrary.org/works"

    @staticmethod
    def _safe_cache_get(key, default=None):
        try:
            return cache.get(key, default)
        except Exception as exc:
            logger.warning("Cache read failed for key %s: %s", key, exc)
            return default

    @staticmethod
    def _safe_cache_set(key, value, timeout=None):
        try:
            cache.set(key, value, timeout=timeout)
        except Exception as exc:
            logger.warning("Cache write failed for key %s: %s", key, exc)

    @staticmethod
    def search(query, max_results=10):
        cache_key = f"ol_search:{query.lower()}:{max_results}"
        cached = OpenLibraryService._safe_cache_get(cache_key)
        if cached:
            return cached

        params = {'q': query, 'limit': max_results}
        url = f"{OpenLibraryService.BASE_URL}?{urllib.parse.urlencode(params)}"

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            return []

        items = data.get('docs', [])
        results = [OpenLibraryService._normalize(item) for item in items]

        # Cache the full result list for 30 min
        OpenLibraryService._safe_cache_set(cache_key, results, timeout=60 * 30)

        # Also cache each book individually by work_id so add_from_google
        # can reuse the rich search data (author, cover, pages) instead of
        # re-fetching from the works endpoint which lacks those fields.
        for book_data in results:
            work_id = book_data.get('google_books_id')
            if work_id:
                OpenLibraryService._safe_cache_set(
                    f"ol_work:{work_id}", book_data, timeout=60 * 60
                )

        return results

    @staticmethod
    def _normalize(book):
        cover_url = ""
        if book.get("cover_i"):
            cover_url = f"https://covers.openlibrary.org/b/id/{book['cover_i']}-M.jpg"

        isbn_list = book.get("isbn", [])
        isbn_10 = isbn_list[0] if isbn_list else None

        # Strip full path — /works/OL45883W → OL45883W
        work_id = book.get('key', '').split('/')[-1]

        return {
            'google_books_id': work_id,
            'title': book.get('title', 'Unknown Title'),
            'author': ', '.join(book.get('author_name', ['Unknown Author'])),
            'isbn_10': isbn_10,
            'isbn_13': None,
            'total_pages': book.get('number_of_pages_median', 0) or 0,
            'cover_url': cover_url,
            'description': '',
            'publisher': ', '.join(book.get('publisher', [])[:1]),
            'published_date': book.get('first_publish_year', ''),
            'language': 'en',
            'categories': book.get('subject', [])[:3],
        }

    @staticmethod
    def fetch_by_id(work_id):
        """
        Fallback fetch when work is not in cache.
        Hits /works/OL45883W.json — note this endpoint lacks author & cover_i,
        so we also call the author and editions endpoints to fill the gaps.
        """
        work_id = work_id.split('/')[-1]
        url = f"{OpenLibraryService.BASE_WORK_URL}/{work_id}.json"

        try:
            response = requests.get(url, timeout=4)
            response.raise_for_status()
            work_data = response.json()
        except requests.RequestException:
            return None

        normalized = OpenLibraryService._normalize_work(work_data, work_id)

        # Attempt to fetch author name from the authors sub-endpoint
        author_keys = [
            a.get('author', {}).get('key', '')
            for a in work_data.get('authors', [])
            if isinstance(a.get('author'), dict)
        ]
        if author_keys:
            try:
                author_url = f"https://openlibrary.org{author_keys[0]}.json"
                author_resp = requests.get(author_url, timeout=3)
                author_resp.raise_for_status()
                normalized['author'] = author_resp.json().get('name', 'Unknown Author')
            except requests.RequestException:
                pass

        # Attempt to fetch cover + page count from editions endpoint
        if not normalized['cover_url'] or not normalized['total_pages']:
            try:
                editions_url = f"{OpenLibraryService.BASE_WORK_URL}/{work_id}/editions.json?limit=5"
                ed_resp = requests.get(editions_url, timeout=3)
                ed_resp.raise_for_status()
                editions = ed_resp.json().get('entries', [])
                for ed in editions:
                    covers = ed.get('covers', [])
                    if covers and covers[0] > 0 and not normalized['cover_url']:
                        normalized['cover_url'] = (
                            f"https://covers.openlibrary.org/b/id/{covers[0]}-M.jpg"
                        )
                    if not normalized['total_pages'] and ed.get('number_of_pages'):
                        normalized['total_pages'] = ed['number_of_pages']
                    if normalized['cover_url'] and normalized['total_pages']:
                        break
            except requests.RequestException:
                pass

        return normalized

    @staticmethod
    def _normalize_work(work_data, work_id):
        description = work_data.get("description", "")
        if isinstance(description, dict):
            description = description.get("value", "")

        return {
            "google_books_id": work_id,
            "title": work_data.get("title", "Unknown Title"),
            "author": "Unknown Author",  # filled in by fetch_by_id if possible
            "isbn_10": None,
            "isbn_13": None,
            "total_pages": 0,
            "cover_url": "",  # filled in by fetch_by_id if possible
            "description": description,
            "publisher": "",
            "published_date": "",
            "language": "en",
            "categories": work_data.get("subjects", [])[:5],
        }


class BookCatalogService:

    @staticmethod
    def add_from_google(google_books_id, user=None, prefetched_data=None):
        work_id = google_books_id.split('/')[-1]

        existing = Book.objects.filter(google_books_id=work_id).first()
        if existing:
            return existing, False

        # Priority: frontend prefetched data → Redis cache → Open Library API
        # prefetched_data comes from the search result the user already saw,
        # so it always has full fields (pages, cover, author) — no extra API call needed.
        data = (
            prefetched_data
            or OpenLibraryService._safe_cache_get(f"ol_work:{work_id}")
            or OpenLibraryService.fetch_by_id(work_id)
        )

        if not data:
            return None, False

        book = Book.objects.create(
            title=data['title'],
            author=data['author'],
            isbn_10=data.get('isbn_10') or None,
            isbn_13=data.get('isbn_13') or None,
            total_pages=data.get('total_pages') or 0,
            cover_url=data.get('cover_url', ''),
            description=data.get('description', ''),
            publisher=data.get('publisher', ''),
            published_date=data.get('published_date', ''),
            language=data.get('language', 'en'),
            google_books_id=work_id,
            added_by=user,
        )

        for cat in data.get('categories', []):
            if cat and cat.strip():
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