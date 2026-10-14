from django.urls import path

from . import views

app_name = "memberships"


urlpatterns = [
    path("", views.membership_list, name="list"),
    path("add/", views.membership_create, name="create"),
    path("<int:membership_id>/", views.membership_detail, name="detail"),
    path("<int:membership_id>/renew/", views.membership_renew, name="renew"),
   
]
