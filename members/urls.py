from django.urls import path

from . import views

app_name = "members"


urlpatterns = [
    path("", views.member_list, name="list"),
    path("add/", views.member_create, name="create"),
    path("<str:member_id>/", views.member_detail, name="detail"),
]
