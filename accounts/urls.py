from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


app_name = "accounts"


urlpatterns = [
    # ---------------------------------------------------------
    # STAFF AUTHENTICATION
    # ---------------------------------------------------------
    path(
        "",
        views.staff_login,
        name="login",
    ),

    path(
        "logout/",
        views.staff_logout,
        name="logout",
    ),

    # ---------------------------------------------------------
    # PASSWORD RESET
    # ---------------------------------------------------------
    path(
        "forgot-password/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url="/login/password-reset-sent/",
        ),
        name="password_reset",
    ),

    path(
        "password-reset-sent/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),

    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/login/password-reset-complete/",
        ),
        name="password_reset_confirm",
    ),

    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]