from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import RegisterViewSet, LoginView, LogoutViewSet, UserProfileViewSet, GoogleAuthView, GoogleClientIdView

router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='register')
router.register(r'logout', LogoutViewSet, basename='logout')
router.register(r'profile', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('google/', GoogleAuthView.as_view(), name='google-auth'),
    path('google-client-id/', GoogleClientIdView.as_view(), name='google-client-id'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] + router.urls
