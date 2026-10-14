from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, TrainerPermission


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        (
            "Gym Information",
            {
                "fields": (
                    "role",
                    "phone",
                )
            }
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Gym Information",
            {
                "fields": (
                    "role",
                    "phone",
                )
            }
        ),
    )


@admin.register(TrainerPermission)
class TrainerPermissionAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "can_view_members",
        "can_view_attendance",
        "can_view_payments",
        "can_view_workouts",
        "can_view_reports",
    )

    list_filter = (
        "can_view_members",
        "can_view_attendance",
        "can_view_payments",
        "can_view_workouts",
        "can_view_reports",
    )