from django.contrib import admin

from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):

    list_display = (
        "member_id",
        "full_name",
        "phone",
        "gender",
        "status",
        "join_date",
    )

    list_filter = (
        "status",
        "gender",
        "join_date",
    )

    search_fields = (
        "member_id",
        "first_name",
        "last_name",
        "phone",
        "email",
    )

    readonly_fields = (
        "member_id",
        "qr_token",
        "join_date",
        "created_at",
        "updated_at",
    )