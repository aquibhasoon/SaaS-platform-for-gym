from django.conf import settings
from django.db import models
from django.utils import timezone

from members.models import Member


class ProgressRecord(models.Model):
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="progress_records",
    )

    measurement_date = models.DateField(
        default=timezone.localdate
    )

    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weight in kg",
    )

    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Height in cm",
    )

    body_fat = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Body fat percentage",
    )

    chest = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Chest measurement in cm",
    )

    waist = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Waist measurement in cm",
    )

    hip = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Hip measurement in cm",
    )

    left_arm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Left arm measurement in cm",
    )

    right_arm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Right arm measurement in cm",
    )

    left_thigh = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Left thigh measurement in cm",
    )

    right_thigh = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Right thigh measurement in cm",
    )

    trainer_notes = models.TextField(
        blank=True
    )

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_progress",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "-measurement_date",
            "-id",
        ]

    def __str__(self):
        return (
            f"{self.member.full_name} - "
            f"{self.measurement_date}"
        )