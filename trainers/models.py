from django.conf import settings
from django.db import models
from django.db.models import Q

from members.models import Member


class TrainerMemberAssignment(models.Model):
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="member_assignments",
    )

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="trainer_assignments",
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_trainer_member_assignments",
    )

    is_active = models.BooleanField(default=True)

    assigned_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-assigned_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["trainer", "member"],
                condition=Q(is_active=True),
                name="unique_active_trainer_member_assignment",
            ),
        ]

    def __str__(self):
        return (
            f"{self.trainer.get_full_name() or self.trainer.username} "
            f"→ {self.member.full_name}"
        )