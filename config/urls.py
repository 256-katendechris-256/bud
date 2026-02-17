from django.contrib import admin
from django.urls import path, include
from config.views import app_shell, dashboard, login_page, signup_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', app_shell, name='landing'),
    path('login/', login_page, name='login-page'),
    path('signup/', signup_page, name='signup-page'),
    path('dashboard/', dashboard, name='dashboard'),
    path('api/auth/', include('apps.accounts.urls')),
]
