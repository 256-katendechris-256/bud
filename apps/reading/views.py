from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserBook
from .serializers import (
    UserBookSerializer,
    LogSessionSerializer,
    ReadingSessionSerializer,
    ReadingStatsSerializer,
)
from .services import ReadingService


class ReadingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserBookSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserBook.objects.filter(
            user=self.request.user
        ).select_related('book')

    @action(detail=False, methods=['post'], url_path='start')
    def start(self, request):
        book_id = request.data.get('book_id')
        if not book_id:
            return Response(
                {'detail': 'book_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user_book = ReadingService.start_reading(request.user, book_id)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(UserBookSerializer(user_book).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='log-session')
    def log_session(self, request):
        serializer = LogSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        try:
            session = ReadingService.log_session(
                user=request.user,
                book_id=d['book_id'],
                start_page=d['start_page'],
                end_page=d['end_page'],
                duration_minutes=d['duration_minutes'],
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(ReadingSessionSerializer(session).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        data = ReadingService.get_reading_stats(request.user)
        serializer = ReadingStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='currently-reading')
    def currently_reading(self, request):
        qs = ReadingService.get_currently_reading(request.user)
        serializer = UserBookSerializer(qs, many=True)
        return Response(serializer.data)
