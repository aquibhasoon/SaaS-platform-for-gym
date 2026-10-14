from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    list_display = (
        "member",
        "check_in",
        "scanned_by",
    )

    list_filter = (
        "check_in",
    )

    search_fields = (
        "member__member_id",
        "member__first_name",
        "member__last_name",
        "member__phone",
    )

    readonly_fields = (
        "created_at",
    )