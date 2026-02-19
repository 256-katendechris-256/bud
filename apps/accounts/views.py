from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer

User = get_user_model()

class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "User registered successfully. Please verify your email."},
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def verify_email(self, request):
        from .services import EmailVerificationService
        
        token = request.data.get('token') or request.data.get('code')
        
        if not token:
            return Response(
                {"error": "Token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success, message, user = EmailVerificationService.verify_email(token)
        
        if success:
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": message,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": UserSerializer(user).data,
                    "redirect": "/dashboard/",
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": message},
                status=status.HTTP_400_BAD_REQUEST
            )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def logout(self, request):
        return Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_200_OK
        )


class UserProfileViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def profile(self, request):
        if not request.user.email_verified or not request.user.is_active:
            return Response(
                {"detail": "User is not approved"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class GoogleClientIdView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"client_id": settings.GOOGLE_CLIENT_ID})


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        credential = request.data.get('credential')
        if not credential:
            return Response(
                {"error": "Google credential is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            idinfo = google_id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
        except ValueError:
            return Response(
                {"error": "Invalid Google token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = idinfo.get('email')
        if not email:
            return Response(
                {"error": "Google account has no email"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'email_verified': True,
                'is_active': True,
            }
        )

        if created:
            user.set_unusable_password()
            user.save()
        elif not user.email_verified:
            user.email_verified = True
            user.save(update_fields=['email_verified'])

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }, status=status.HTTP_200_OK)
