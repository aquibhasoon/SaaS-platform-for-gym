from django.urls import path

from . import views


app_name = "progress"


urlpatterns = [

    path(
        "",
        views.progress_list,
        name="list",
    ),

    path(
        "add/",
        views.progress_create,
        name="create",
    ),

    path(
        "<int:record_id>/edit/",
        views.progress_edit,
        name="edit",
    ),

    path(
        "<int:record_id>/delete/",
        views.progress_delete,
        name="delete",
    ),

    path(
        "member/<int:member_id>/",
        views.member_progress,
        name="member_progress",
    ),
]