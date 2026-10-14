from django.urls import path
from . import views

app_name = "member_portal"

urlpatterns = [
    path("login/", views.member_login, name="login"),
    path("register/", views.member_register, name="register"),
    path("", views.member_dashboard, name="dashboard"),
    path("logout/", views.member_logout, name="logout"),
]