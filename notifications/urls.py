from django.urls import path
from . import views, cron_views

urlpatterns = [
    # ── Flutter API endpoints ──────────────────────────────────────
    path('register-token/',   views.register_token,    name='register-token'),
    path('unregister-token/', views.unregister_token,  name='unregister-token'),
    path('',                  views.notification_list, name='notification-list'),
    path('unread-count/',     views.unread_count,      name='unread-count'),
    path('<int:pk>/read/',    views.mark_read,          name='mark-read'),
    path('mark-all-read/',    views.mark_all_read,      name='mark-all-read'),
    path('preferences/',      views.preferences,        name='notification-preferences'),

    # ── QStash cron endpoints ──────────────────────────────────────
    path('cron/check-streaks/',    cron_views.cron_check_streaks,    name='cron-check-streaks'),
    path('cron/midnight-sos/',     cron_views.cron_midnight_sos,     name='cron-midnight-sos'),
    path('cron/daily-reminders/',  cron_views.cron_daily_reminders,  name='cron-daily-reminders'),
    path('cron/weekly-digest/',    cron_views.cron_weekly_digest,    name='cron-weekly-digest'),

    path('<int:pk>/delete/', views.delete_notification,     name='notification-delete'),
    path('delete-all/',  views.delete_all_notifications, name='notification-delete-all'),
]