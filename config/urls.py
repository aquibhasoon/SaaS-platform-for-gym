from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("members/", include("members.urls")),
    path("attendance/", include("attendance.urls")),
    path("memberships/", include("memberships.urls")),
    path("payments/", include("payments.urls")),
    path("trainers/", include("trainers.urls")),
    path("workouts/", include("workouts.urls")),
    path(
        "progress/",
        include("progress.urls"),
    ),
    path(
        "reports/",
        include("reports.urls"),
    ),
    path(
        "settings/",
        include("gym_settings.urls"),
    ),
    path("member/", include("member_portal.urls")),
    path(
        "login/",
        include("accounts.urls"),
    ),
    path(
        "audit-logs/",
        include("audit_logs.urls"),
    ),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
