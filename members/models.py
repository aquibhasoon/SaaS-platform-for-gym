import uuid

from django.conf import settings
from django.db import models


class Member(models.Model):

    GENDER_CHOICES = (
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    )

    STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
    )

    APPROVAL_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="member_profile",
    )

    member_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100,
        blank=True
    )

    phone = models.CharField(
        max_length=15
    )

    email = models.EmailField(
        blank=True
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True
    )

    emergency_contact_phone = models.CharField(
        max_length=15,
        blank=True
    )

    profile_photo = models.ImageField(
        upload_to="members/profile/",
        blank=True,
        null=True
    )

    join_date = models.DateField(
        auto_now_add=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="active"
    )

    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        default="approved"
    )

    qr_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):

        if not self.member_id:
            self.member_id = self.generate_member_id()

        super().save(*args, **kwargs)

    @staticmethod
    def generate_member_id():

        last_member = Member.objects.order_by("-id").first()

        if last_member:
            number = last_member.id + 1
        else:
            number = 1

        return f"GYM{number:05d}"

    @property
    def full_name(self):

        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_approved(self):

        return self.approval_status == "approved"

    def __str__(self):

        return f"{self.member_id} - {self.full_name}"