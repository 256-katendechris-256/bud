from django.urls import path
from . import views

urlpatterns = [
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('my-rank/', views.my_rank, name='my-rank'),
    path('badges/', views.my_badges, name='my-badges'),
]
