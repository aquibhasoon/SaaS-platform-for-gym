from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from members.models import Member


class Exercise(models.Model):
    CATEGORY_CHOICES = (
        ("chest", "Chest"),
        ("back", "Back"),
        ("shoulders", "Shoulders"),
        ("biceps", "Biceps"),
        ("triceps", "Triceps"),
        ("legs", "Legs"),
        ("glutes", "Glutes"),
        ("core", "Core"),
        ("cardio", "Cardio"),
        ("full_body", "Full Body"),
        ("mobility", "Mobility"),
        ("other", "Other"),
    )

    name = models.CharField(max_length=150)

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="other",
    )

    description = models.TextField(blank=True)
    posture_instructions = models.TextField(blank=True)
    breathing_instructions = models.TextField(blank=True)
    technique_instructions = models.TextField(blank=True)
    common_mistakes = models.TextField(blank=True)
    safety_notes = models.TextField(blank=True)
    additional_instructions = models.TextField(blank=True)

    demo_video_url = models.URLField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_exercises",
    )

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkoutPlan(models.Model):
    name = models.CharField(max_length=150)

    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_workout_plans",
    )

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkoutExercise(models.Model):
    plan = models.ForeignKey(
        WorkoutPlan,
        on_delete=models.CASCADE,
        related_name="exercises",
    )

    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.PROTECT,
        related_name="workout_items",
    )

    order = models.PositiveIntegerField(default=1)

    sets = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    reps = models.CharField(
        max_length=50,
        blank=True,
    )

    target_weight = models.CharField(
        max_length=50,
        blank=True,
    )

    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    rest_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    trainer_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.plan.name} - {self.exercise.name}"


class MemberWorkout(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="workout_assignments",
    )

    plan = models.ForeignKey(
        WorkoutPlan,
        on_delete=models.PROTECT,
        related_name="member_assignments",
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_workouts",
    )

    start_date = models.DateField(
        default=timezone.localdate,
    )

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    trainer_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["member"],
                condition=Q(status="active"),
                name="unique_active_workout_per_member",
            ),
            models.CheckConstraint(
                condition=Q(end_date__isnull=True)
                | Q(end_date__gte=models.F("start_date")),
                name="workout_end_date_after_start_date",
            ),
        ]

    def __str__(self):
        return f"{self.member.full_name} - {self.plan.name}"