from django.db.models import Q
from django.http import FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from .models import Book, Genre
from .serializers import (
    BookListSerializer,
    BookDetailSerializer,
    BookFileUploadSerializer,
    GenreSerializer,
    GoogleBookResultSerializer,
)
from .permissions import IsBudAdmin
from .services import OpenLibraryService, BookCatalogService, GoogleBooksAPIError


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.prefetch_related('genres').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return BookListSerializer
        return BookDetailSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update'):
            return [IsBudAdmin()]
        return [IsAuthenticated()]

    def _is_admin(self, user):
        return user.is_staff or getattr(user, 'role', '') in ('SUPER_ADMIN', 'CLUB_ADMIN')

    def destroy(self, request, *args, **kwargs):
        book = self.get_object()
        if not self._is_admin(request.user) and book.added_by != request.user:
            return Response(
                {'detail': 'Only the person who added this book can remove it.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.query_params.get('q', '').strip()
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(author__icontains=query))
        genre_ids = self.request.query_params.getlist('genre')
        if genre_ids:
            qs = qs.filter(genres__id__in=genre_ids).distinct()
        return qs

    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user)

    @action(detail=False, methods=['get'], url_path='search-google')
    def search_google(self, request):
        query = request.query_params.get('q', '').strip()
        if len(query) < 3:
            return Response(status=200)
        try:
            results = OpenLibraryService.search(query)
        except GoogleBooksAPIError as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        serializer = GoogleBookResultSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='upload-book',
            parser_classes=[MultiPartParser])
    def upload_book(self, request):
        """Create a new book entry directly from an uploaded PDF."""
        if not self._is_admin(request.user):
            count = Book.objects.filter(added_by=request.user).count()
            if count >= 5:
                return Response(
                    {'detail': 'You can add up to 5 books. Remove one of yours first.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        title  = request.data.get('title', '').strip()
        author = request.data.get('author', '').strip()
        file   = request.FILES.get('file')

        if not title:
            return Response({'detail': 'Title is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not author:
            return Response({'detail': 'Author is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not file:
            return Response({'detail': 'A PDF file is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not file.name.lower().endswith('.pdf'):
            return Response({'detail': 'Only PDF files are allowed.'}, status=status.HTTP_400_BAD_REQUEST)
        if file.size > 104857600:
            return Response({'detail': 'File size cannot exceed 100 MB.'}, status=status.HTTP_400_BAD_REQUEST)

        book = Book.objects.create(
            title=title,
            author=author,
            file=file,
            added_by=request.user,
        )
        return Response(BookDetailSerializer(book).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='upload-file',
            parser_classes=[MultiPartParser])
    def upload_file(self, request, pk=None):
        book = self.get_object()
        serializer = BookFileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book.file = serializer.validated_data['file']
        book.save(update_fields=['file'])
        return Response(
            BookDetailSerializer(book).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='add-from-google')
    def add_from_google(self, request):
        google_books_id = request.data.get('google_books_id', '').strip()
        if not google_books_id:
            return Response(
                {'detail': 'google_books_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build prefetched_data from whatever the frontend sends alongside the ID.
        # This avoids a Redis cache miss on a cold Vercel serverless instance —
        # the search result data travels with the request instead of relying on cache.
        prefetched_data = None
        if request.data.get('title'):
            prefetched_data = {
                'google_books_id': google_books_id,
                'title':        request.data.get('title', ''),
                'author':       request.data.get('author', ''),
                'total_pages':  request.data.get('total_pages', 0) or 0,
                'cover_url':    request.data.get('cover_url', ''),
                'description':  request.data.get('description', ''),
                'publisher':    request.data.get('publisher', ''),
                'published_date': request.data.get('published_date', ''),
                'isbn_10':      request.data.get('isbn_10', None),
                'isbn_13':      request.data.get('isbn_13', None),
                'language':     request.data.get('language', 'en'),
                'categories':   request.data.get('categories', []),
            }

        book, created = BookCatalogService.add_from_google(
            google_books_id,
            user=request.user,
            prefetched_data=prefetched_data,
        )

        if not book:
            return Response(
                {'detail': 'Could not fetch book from Open Library.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BookDetailSerializer(book)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get'], url_path='download-pdf')
    def download_pdf(self, request, pk=None):
        """Download PDF file for a book - authenticated users only."""
        book = self.get_object()

        if not book.file:
            return Response(
                {'detail': 'This book does not have a PDF file available.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            if not book.file.storage.exists(book.file.name):
                return Response(
                    {'detail': 'PDF file not found on server.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            file_handle = book.file.open('rb')
            response = FileResponse(file_handle, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{book.title}.pdf"'
            print(f'📥 [Books] PDF downloaded: {book.title} by user {request.user.email}')
            return response
        except Exception as e:
            print(f'❌ [Books] PDF download error: {e}')
            return Response(
                {'detail': f'Error downloading PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GenreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Genre.objects.filter(books__isnull=False).distinct()