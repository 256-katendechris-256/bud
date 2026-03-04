# apps/books/urls.py
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, GenreViewSet

router = DefaultRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'genres', GenreViewSet, basename='genre')

print("REGISTERED URLS:", [str(u.pattern) for u in router.urls])

urlpatterns = router.urls