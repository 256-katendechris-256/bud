from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import FCMToken, NotificationPreference, NotificationLog
from .serializers import (
    FCMTokenSerializer,
    NotificationPreferenceSerializer,
    NotificationLogSerializer,
)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_token(request):
    """Flutter calls this on every app open to keep the token fresh."""
    token = request.data.get('token')
    if not token:
        return Response({'error': 'token is required'}, status=400)

    FCMToken.objects.update_or_create(
        token=token,
        defaults={'user': request.user},
    )
    return Response({'status': 'token registered'})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unregister_token(request):
    """Called on logout so the device stops receiving pushes."""
    token = request.data.get('token')
    if token:
        FCMToken.objects.filter(user=request.user, token=token).delete()
    return Response({'status': 'token removed'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """Returns the 30 most recent notifications for the user."""
    logs = NotificationLog.objects.filter(
        user=request.user
    )[:30]
    serializer = NotificationLogSerializer(logs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_count(request):
    """Lightweight endpoint — Flutter polls this every 60s for the bell badge."""
    count = NotificationLog.objects.filter(
        user=request.user,
        opened=False,
    ).count()
    return Response({'unread': count})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_read(request, pk):
    """Mark a single notification as opened."""
    try:
        log = NotificationLog.objects.get(pk=pk, user=request.user)
    except NotificationLog.DoesNotExist:
        return Response({'error': 'not found'}, status=404)

    log.opened = True
    log.save(update_fields=['opened'])
    return Response({'status': 'marked read'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    """Clears the bell badge — marks every notification as opened."""
    NotificationLog.objects.filter(
        user=request.user,
        opened=False,
    ).update(opened=True)
    return Response({'status': 'all marked read'})


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def preferences(request):
    """Get or update notification preferences."""
    pref, _ = NotificationPreference.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        return Response(NotificationPreferenceSerializer(pref).data)

    serializer = NotificationPreferenceSerializer(
        pref, data=request.data, partial=True
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, pk):
    deleted, _ = NotificationLog.objects.filter(
        pk=pk, user=request.user
    ).delete()
    if deleted:
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response({'error': 'not found'}, status=404)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_all_notifications(request):
    NotificationLog.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)