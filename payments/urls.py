from django.urls import path

from . import views


app_name = "payments"


urlpatterns = [

    path(
        "",
        views.payment_list,
        name="list"
    ),

    path(
        "membership/<int:membership_id>/add/",
        views.payment_create,
        name="create"
    ),

    path(
        "<int:payment_id>/",
        views.payment_detail,
        name="detail"
    ),

]