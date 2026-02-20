from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from config.views import app_shell, dashboard, login_page, signup_page, books_page, books_reader_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', app_shell, name='landing'),
    path('login/', login_page, name='login-page'),
    path('signup/', signup_page, name='signup-page'),
    path('dashboard/', dashboard, name='dashboard'),
    path('books/', books_page, name='books-page'),
    path('books/<int:book_id>/read/', books_reader_page, name='books-reader'),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/', include('apps.books.urls')),
    path('api/reading/', include('apps.reading.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
