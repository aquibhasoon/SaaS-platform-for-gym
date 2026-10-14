from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "user",
        "action",
        "model_name",
        "object_id",
        "description",
        "ip_address",
    )

    list_filter = (
        "action",
        "model_name",
        "created_at",
    )

    search_fields = (
        "description",
        "object_id",
        "user__username",
        "user__first_name",
        "user__last_name",
    )

    readonly_fields = (
        "user",
        "action",
        "model_name",
        "object_id",
        "description",
        "ip_address",
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    def has_add_permission(self, request):
        # Logs should be created by the application,
        # not manually by users.
        return False

    def has_change_permission(self, request, obj=None):
        # Audit records must remain immutable.
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting audit history through admin.
        return False