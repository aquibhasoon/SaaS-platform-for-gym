from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTION_CHOICES = (
        ("create", "Created"),
        ("update", "Updated"),
        ("delete", "Deleted"),
        ("login", "Logged In"),
        ("logout", "Logged Out"),
        ("approve", "Approved"),
        ("reject", "Rejected"),
        ("activate", "Activated"),
        ("deactivate", "Deactivated"),
        ("payment", "Payment"),
        ("attendance", "Attendance"),
        ("other", "Other"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
    )

    model_name = models.CharField(
        max_length=100,
        blank=True,
    )

    object_id = models.CharField(
        max_length=100,
        blank=True,
    )

    description = models.TextField()

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        username = (
            self.user.username
            if self.user
            else "System"
        )

        return (
            f"{username} - "
            f"{self.get_action_display()} - "
            f"{self.description}"
        )