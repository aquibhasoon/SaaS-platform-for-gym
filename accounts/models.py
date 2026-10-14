from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = (
        ("owner", "Owner"),
        ("trainer", "Trainer"),
        ("member", "Member"),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="member"
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    def __str__(self):
        return self.get_full_name() or self.username


class TrainerPermission(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="trainer_permissions"
    )

    # Members
    can_view_members = models.BooleanField(default=True)
    can_add_members = models.BooleanField(default=False)
    can_edit_members = models.BooleanField(default=False)
    can_delete_members = models.BooleanField(default=False)

    # Attendance
    can_view_attendance = models.BooleanField(default=True)
    can_scan_attendance = models.BooleanField(default=True)
    can_edit_attendance = models.BooleanField(default=False)

    # Memberships
    can_view_memberships = models.BooleanField(default=True)
    can_create_memberships = models.BooleanField(default=False)
    can_renew_memberships = models.BooleanField(default=False)

    # Payments
    can_view_payments = models.BooleanField(default=False)
    can_add_payments = models.BooleanField(default=False)

    # Workouts
    can_view_workouts = models.BooleanField(default=True)
    can_manage_workouts = models.BooleanField(default=True)

    # Progress
    can_view_progress = models.BooleanField(default=True)
    can_manage_progress = models.BooleanField(default=True)

    # Reports
    can_view_reports = models.BooleanField(default=False)

    def __str__(self):
        return f"Permissions - {self.user.username}"