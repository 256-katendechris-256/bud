from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Window, F
from django.db.models.functions import RowNumber

from .models import UserGamification, Badge
from .serializers import LeaderboardEntrySerializer, UserGamificationSerializer, BadgeSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leaderboard(request):
    """
    Get the leaderboard ranked by total XP.
    
    Query params:
    - limit: Number of entries to return (default 20, max 100)
    - period: 'all', 'week', 'month' (default 'all')
    """
    limit = min(int(request.query_params.get('limit', 20)), 100)
    
    # Get all gamification records ordered by XP
    queryset = UserGamification.objects.select_related('user').filter(
        total_xp__gt=0  # Only include users with XP
    ).order_by('-total_xp', '-current_streak', 'user__date_joined')[:limit]
    
    # Add rank to each entry
    entries = list(queryset)
    for i, entry in enumerate(entries, start=1):
        entry.rank = i
    
    serializer = LeaderboardEntrySerializer(
        entries, 
        many=True, 
        context={'request': request}
    )
    
    # Get current user's rank if not in top results
    user_rank = None
    user_entry = None
    current_user_in_list = any(e.user_id == request.user.id for e in entries)
    
    if not current_user_in_list:
        try:
            user_gamification = UserGamification.objects.get(user=request.user)
            # Count users with more XP
            rank = UserGamification.objects.filter(
                total_xp__gt=user_gamification.total_xp
            ).count() + 1
            user_gamification.rank = rank
            user_entry = LeaderboardEntrySerializer(
                user_gamification, 
                context={'request': request}
            ).data
            user_rank = rank
        except UserGamification.DoesNotExist:
            user_rank = None
    
    return Response({
        'leaderboard': serializer.data,
        'total_participants': UserGamification.objects.filter(total_xp__gt=0).count(),
        'current_user_rank': user_rank,
        'current_user_entry': user_entry,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_rank(request):
    """Get the current user's rank and nearby competitors."""
    try:
        user_gamification = UserGamification.objects.get(user=request.user)
    except UserGamification.DoesNotExist:
        return Response({
            'rank': None,
            'total_xp': 0,
            'message': 'Start reading to join the leaderboard!'
        })
    
    # Calculate rank
    rank = UserGamification.objects.filter(
        total_xp__gt=user_gamification.total_xp
    ).count() + 1
    
    total_participants = UserGamification.objects.filter(total_xp__gt=0).count()
    
    # Get users just above and below
    above = UserGamification.objects.select_related('user').filter(
        total_xp__gt=user_gamification.total_xp
    ).order_by('total_xp')[:3]
    
    below = UserGamification.objects.select_related('user').filter(
        total_xp__lt=user_gamification.total_xp
    ).order_by('-total_xp')[:3]
    
    # Add ranks
    above_list = list(above)
    for i, entry in enumerate(above_list):
        entry.rank = rank - len(above_list) + i
    
    below_list = list(below)
    for i, entry in enumerate(below_list):
        entry.rank = rank + i + 1
    
    user_gamification.rank = rank
    
    return Response({
        'rank': rank,
        'total_participants': total_participants,
        'percentile': round((1 - (rank / total_participants)) * 100, 1) if total_participants > 0 else 0,
        'user': UserGamificationSerializer(user_gamification).data,
        'above': LeaderboardEntrySerializer(above_list, many=True, context={'request': request}).data,
        'below': LeaderboardEntrySerializer(below_list, many=True, context={'request': request}).data,
        'xp_to_next_rank': above_list[0].total_xp - user_gamification.total_xp if above_list else 0,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_badges(request):
    """Get the current user's earned badges."""
    badges = Badge.objects.filter(user=request.user).order_by('-earned_at')
    serializer = BadgeSerializer(badges, many=True)
    
    # Get all possible badges
    all_badges = [choice[0] for choice in Badge.BADGE_CHOICES]
    earned = [b.badge_type for b in badges]
    
    return Response({
        'earned': serializer.data,
        'total_earned': len(earned),
        'total_available': len(all_badges),
        'locked': [b for b in all_badges if b not in earned],
    })
