from django.conf import settings
from django.db import models
from django.utils import timezone

from members.models import Member


class Attendance(models.Model):

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )

    check_in = models.DateTimeField(
        default=timezone.now
    )

    # Stores the local calendar date of this check-in.
    # This makes the "one attendance per member per day"
    # rule enforceable at the database level.
    check_in_date = models.DateField(
        editable=False,
        default=timezone.localdate
    )

    scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_scans"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-check_in"]
        constraints = [
            models.UniqueConstraint(
                fields=["member", "check_in_date"],
                name="unique_member_attendance_per_day",
            ),
        ]

    def save(self, *args, **kwargs):
        self.check_in_date = timezone.localtime(self.check_in).date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.member.full_name} - {self.check_in}"

    @property
    def attendance_date(self):
        return self.check_in_date
