from rest_framework.permissions import BasePermission


class IsBudAdmin(BasePermission):
    """
    Allows access to users with SUPER_ADMIN or CLUB_ADMIN role,
    or Django's is_staff flag.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.is_staff
            or getattr(request.user, 'role', '') in ('SUPER_ADMIN', 'CLUB_ADMIN')
        )
