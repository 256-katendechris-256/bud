from rest_framework.routers import DefaultRouter

from .views import ReadingViewSet, NoteViewSet

router = DefaultRouter()
router.register(r'progress', ReadingViewSet, basename='reading')
router.register(r'notes', NoteViewSet, basename='notes')

urlpatterns = router.urls
