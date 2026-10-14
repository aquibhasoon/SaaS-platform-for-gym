from django.urls import path

from . import views

app_name = "attendance"


urlpatterns = [
    path("", views.attendance_list, name="list"),
    path("scanner/", views.scanner, name="scanner"),
    path("qr/<str:member_id>/", views.member_qr, name="member_qr"),
]
