from django.urls import path
from . import views

app_name = "workouts"

urlpatterns = [
    path("", views.workout_list, name="list"),
    path(
        "plan/<int:plan_id>/",
        views.plan_detail,
        name="plan_detail",
    ),
]
