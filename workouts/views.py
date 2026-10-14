from django.contrib import messages
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import trainer_permission
from members.models import Member

from .forms import (
    ExerciseForm,
    MemberWorkoutForm,
    WorkoutExerciseForm,
    WorkoutPlanForm,
)
from .models import Exercise, MemberWorkout, WorkoutExercise, WorkoutPlan


def _can_manage_workouts(request):
    if request.user.role == "owner":
        return True

    if request.user.role != "trainer":
        return False

    try:
        permissions = request.user.trainer_permissions
    except AttributeError:
        return False

    return permissions.can_manage_workouts


@trainer_permission("can_view_workouts")
def workout_list(request):
    can_manage = _can_manage_workouts(request)

    if request.method == "POST":
        if not can_manage:
            messages.error(
                request,
                "You do not have permission to manage workouts.",
            )
            return redirect("workouts:list")

        action = request.POST.get("action")

        # ---------------------------------------------------------
        # ADD EXERCISE
        # ---------------------------------------------------------
        if action == "add_exercise":
            form = ExerciseForm(request.POST)

            if form.is_valid():
                exercise = form.save(commit=False)
                exercise.created_by = request.user
                exercise.is_default = False
                exercise.save()

                messages.success(
                    request,
                    f"{exercise.name} was added successfully.",
                )
                return redirect("workouts:list")

            messages.error(
                request,
                "Please correct the exercise details.",
            )

        # ---------------------------------------------------------
        # EDIT EXERCISE
        # ---------------------------------------------------------
        elif action == "edit_exercise":
            exercise = get_object_or_404(
                Exercise,
                id=request.POST.get("exercise_id"),
            )

            form = ExerciseForm(
                request.POST,
                instance=exercise,
            )

            if form.is_valid():
                updated = form.save()
                messages.success(
                    request,
                    f"{updated.name} was updated successfully.",
                )
                return redirect("workouts:list")

            messages.error(
                request,
                "Please correct the exercise details.",
            )

        # ---------------------------------------------------------
        # ACTIVATE / DEACTIVATE EXERCISE
        # ---------------------------------------------------------
        elif action == "toggle_exercise":
            exercise = get_object_or_404(
                Exercise,
                id=request.POST.get("exercise_id"),
            )

            exercise.is_active = not exercise.is_active
            exercise.save(update_fields=["is_active", "updated_at"])

            state = "activated" if exercise.is_active else "deactivated"

            messages.success(
                request,
                f"{exercise.name} was {state}.",
            )
            return redirect("workouts:list")

        # ---------------------------------------------------------
        # DELETE EXERCISE FROM LIBRARY
        # ---------------------------------------------------------
        elif action == "delete_exercise_library":
            exercise = get_object_or_404(
                Exercise,
                id=request.POST.get("exercise_id"),
            )

            if exercise.is_default:
                messages.error(request, "Default exercises cannot be deleted.")
                return redirect("workouts:list")

            try:
                exercise_name = exercise.name
                exercise.delete()
            except ProtectedError:
                messages.error(
                    request,
                    f"{exercise_name} cannot be deleted because it is already used in a workout plan. Deactivate it instead.",
                )
                return redirect("workouts:list")

            messages.success(request, f"{exercise_name} was deleted permanently.")
            return redirect("workouts:list")

        # ---------------------------------------------------------
        # CREATE PLAN + EXERCISES
        # ---------------------------------------------------------
        elif action == "add_plan":
            plan_form = WorkoutPlanForm(request.POST)

            exercise_ids = request.POST.getlist("exercise_ids[]")
            orders = request.POST.getlist("exercise_orders[]")
            sets_values = request.POST.getlist("exercise_sets[]")
            reps_values = request.POST.getlist("exercise_reps[]")
            weights = request.POST.getlist("exercise_weights[]")
            rests = request.POST.getlist("exercise_rest[]")
            durations = request.POST.getlist("exercise_duration[]")
            notes = request.POST.getlist("exercise_notes[]")

            if not exercise_ids:
                messages.error(
                    request,
                    "Add at least one exercise to the workout plan.",
                )
                return redirect("workouts:list")

            if not plan_form.is_valid():
                messages.error(
                    request,
                    "Please enter a valid workout plan name.",
                )
                return redirect("workouts:list")

            row_count = len(exercise_ids)

            def value_at(values, index, default=""):
                return values[index].strip() if index < len(values) else default

            active_exercises = {
                exercise.id: exercise
                for exercise in Exercise.objects.filter(
                    id__in=exercise_ids,
                    is_active=True,
                )
            }

            if len(active_exercises) != len(set(exercise_ids)):
                messages.error(
                    request,
                    "One or more selected exercises are no longer active.",
                )
                return redirect("workouts:list")

            try:
                with transaction.atomic():
                    plan = plan_form.save(commit=False)
                    plan.created_by = request.user
                    plan.is_default = False
                    plan.is_active = True
                    plan.save()

                    for index in range(row_count):
                        exercise_id_raw = value_at(exercise_ids, index)

                        try:
                            exercise_id = int(exercise_id_raw)
                        except (TypeError, ValueError):
                            raise ValueError(
                                "One or more selected exercises are invalid."
                            )

                        if exercise_id not in active_exercises:
                            raise ValueError(
                                "One or more selected exercises are no longer active."
                            )

                        order_raw = value_at(orders, index, str(index + 1))
                        sets_raw = value_at(sets_values, index)
                        rest_raw = value_at(rests, index)
                        duration_raw = value_at(durations, index)

                        try:
                            order = int(order_raw or index + 1)
                            sets = int(sets_raw) if sets_raw else None
                            rest_seconds = int(rest_raw) if rest_raw else None
                            duration_minutes = (
                                int(duration_raw)
                                if duration_raw
                                else None
                            )
                        except ValueError:
                            raise ValueError(
                                "Sets, order, rest and duration must be numbers."
                            )

                        if order < 1:
                            raise ValueError("Exercise order must be at least 1.")

                        if sets is not None and sets < 1:
                            raise ValueError("Sets must be at least 1.")

                        if rest_seconds is not None and rest_seconds < 0:
                            raise ValueError("Rest cannot be negative.")

                        if duration_minutes is not None and duration_minutes < 1:
                            raise ValueError(
                                "Duration must be at least 1 minute."
                            )

                        WorkoutExercise.objects.create(
                            plan=plan,
                            exercise=active_exercises[exercise_id],
                            order=order,
                            sets=sets,
                            reps=value_at(reps_values, index),
                            target_weight=value_at(weights, index),
                            duration_minutes=duration_minutes,
                            rest_seconds=rest_seconds,
                            trainer_notes=value_at(notes, index),
                        )

            except ValueError as exc:
                messages.error(request, str(exc))
                return redirect("workouts:list")

            messages.success(
                request,
                f"{plan.name} was created with {row_count} exercises.",
            )
            return redirect(
                "workouts:plan_detail",
                plan_id=plan.id,
            )

        # ---------------------------------------------------------
        # ADD EXERCISE TO EXISTING PLAN
        # ---------------------------------------------------------
        elif action == "add_plan_exercise":
            plan = get_object_or_404(
                WorkoutPlan,
                id=request.POST.get("plan_id"),
                is_active=True,
            )

            form = WorkoutExerciseForm(request.POST)
            form.fields["exercise"].queryset = (
                Exercise.objects.filter(is_active=True).order_by("name")
            )

            if form.is_valid():
                item = form.save(commit=False)
                item.plan = plan

                if not item.order:
                    last_item = (
                        WorkoutExercise.objects
                        .filter(plan=plan)
                        .order_by("-order", "-id")
                        .first()
                    )
                    item.order = (
                        last_item.order + 1
                        if last_item
                        else 1
                    )

                item.save()

                messages.success(
                    request,
                    f"{item.exercise.name} was added to {plan.name}.",
                )
                return redirect("workouts:list")

            messages.error(
                request,
                "Could not add the exercise to the plan.",
            )

        # ---------------------------------------------------------
        # TOGGLE PLAN
        # ---------------------------------------------------------
        elif action == "toggle_plan":
            plan = get_object_or_404(
                WorkoutPlan,
                id=request.POST.get("plan_id"),
            )

            plan.is_active = not plan.is_active
            plan.save(update_fields=["is_active", "updated_at"])

            state = "activated" if plan.is_active else "deactivated"

            messages.success(
                request,
                f"{plan.name} was {state}.",
            )
            return redirect("workouts:list")

        # ---------------------------------------------------------
        # ASSIGN WORKOUT
        # ---------------------------------------------------------
        elif action == "assign_workout":
            form = MemberWorkoutForm(request.POST)

            if form.is_valid():
                assignment = form.save(commit=False)

                with transaction.atomic():
                    member = (
                        Member.objects
                        .select_for_update()
                        .get(pk=assignment.member.pk)
                    )

                    assignment.member = member

                    existing_active = (
                        MemberWorkout.objects
                        .select_related("plan")
                        .filter(
                            member=member,
                            status="active",
                        )
                        .exclude(pk=assignment.pk)
                        .first()
                    )

                    if existing_active:
                        existing_active.status = "completed"
                        existing_active.save(
                            update_fields=["status", "updated_at"]
                        )

                    assignment.assigned_by = request.user
                    assignment.status = "active"
                    assignment.save()

                if existing_active:
                    messages.info(
                        request,
                        (
                            f"{existing_active.plan.name} was marked completed "
                            f"before assigning the new workout."
                        ),
                    )

                messages.success(
                    request,
                    f"{assignment.plan.name} was assigned to "
                    f"{assignment.member.full_name}.",
                )
                return redirect("workouts:list")

            messages.error(
                request,
                "Please correct the assignment details.",
            )

        # ---------------------------------------------------------
        # UPDATE ASSIGNMENT STATUS
        # ---------------------------------------------------------
        elif action == "update_assignment_status":
            assignment = get_object_or_404(
                MemberWorkout,
                id=request.POST.get("assignment_id"),
            )

            new_status = request.POST.get("status")

            if new_status not in {
                "active",
                "completed",
                "cancelled",
            }:
                messages.error(request, "Invalid workout status.")
                return redirect("workouts:list")

            with transaction.atomic():
                member = (
                    Member.objects
                    .select_for_update()
                    .get(pk=assignment.member_id)
                )

                assignment = (
                    MemberWorkout.objects
                    .select_related("member", "plan")
                    .get(pk=assignment.pk)
                )

                other_active = None

                if new_status == "active":
                    other_active = (
                        MemberWorkout.objects
                        .select_related("plan")
                        .filter(
                            member=member,
                            status="active",
                        )
                        .exclude(pk=assignment.pk)
                        .first()
                    )

                    if other_active:
                        other_active.status = "completed"
                        other_active.save(
                            update_fields=["status", "updated_at"]
                        )

                assignment.status = new_status
                assignment.save(update_fields=["status", "updated_at"])

            if other_active:
                messages.info(
                    request,
                    (
                        f"{other_active.plan.name} was marked completed "
                        f"because another workout became active."
                    ),
                )

            messages.success(
                request,
                f"Workout assignment for {assignment.member.full_name} "
                f"was changed to {assignment.get_status_display()}.",
            )
            return redirect("workouts:list")

        else:
            messages.error(request, "Invalid workout action.")
            return redirect("workouts:list")

    exercises = (
        Exercise.objects
        .all()
        .order_by("-is_active", "name")
    )

    exercise_status = request.GET.get("exercise_status", "active")
    if exercise_status not in {"active", "inactive", "all"}:
        exercise_status = "active"

    if exercise_status == "active":
        exercises = exercises.filter(is_active=True)
    elif exercise_status == "inactive":
        exercises = exercises.filter(is_active=False)

    workout_plans = (
        WorkoutPlan.objects
        .filter(is_active=True)
        .prefetch_related("exercises__exercise")
        .order_by("name")
    )

    assignments = (
        MemberWorkout.objects
        .select_related("member", "plan", "assigned_by")
        .order_by("-created_at")
    )

    assignment_search = request.GET.get("assignment_search", "").strip()
    assignment_status = request.GET.get("assignment_status", "all").strip()
    assignment_member = request.GET.get("assignment_member", "").strip()

    if assignment_search:
        assignments = assignments.filter(
            Q(member__first_name__icontains=assignment_search)
            | Q(member__last_name__icontains=assignment_search)
            | Q(member__member_id__icontains=assignment_search)
            | Q(plan__name__icontains=assignment_search)
        )

    if assignment_status in {"active", "completed", "cancelled"}:
        assignments = assignments.filter(status=assignment_status)
    else:
        assignment_status = "all"

    if assignment_member:
        assignments = assignments.filter(member_id=assignment_member)

    assignments = assignments[:50]

    all_assignments = MemberWorkout.objects.all()
    active_assignment_count = all_assignments.filter(status="active").count()
    completed_assignment_count = all_assignments.filter(status="completed").count()
    cancelled_assignment_count = all_assignments.filter(status="cancelled").count()

    exercise_form = ExerciseForm()
    plan_form = WorkoutPlanForm()
    plan_exercise_form = WorkoutExerciseForm()
    plan_exercise_form.fields["exercise"].queryset = (
        Exercise.objects
        .filter(is_active=True)
        .order_by("name")
    )
    assignment_form = MemberWorkoutForm()

    all_exercises = Exercise.objects.all()
    default_exercise_count = all_exercises.filter(is_default=True).count()
    trainer_exercise_count = all_exercises.filter(is_default=False).count()
    active_exercise_count = all_exercises.filter(is_active=True).count()
    inactive_exercise_count = all_exercises.filter(is_active=False).count()

    context = {
        "exercises": exercises,
        "workout_plans": workout_plans,
        "plans": workout_plans,
        "assignments": assignments,
        "assignment_search": assignment_search,
        "assignment_status": assignment_status,
        "assignment_member": assignment_member,
        "active_assignment_count": active_assignment_count,
        "completed_assignment_count": completed_assignment_count,
        "cancelled_assignment_count": cancelled_assignment_count,
        "exercise_form": exercise_form,
        "form": exercise_form,
        "plan_form": plan_form,
        "plan_exercise_form": plan_exercise_form,
        "assignment_form": assignment_form,
        "default_exercise_count": default_exercise_count,
        "trainer_exercise_count": trainer_exercise_count,
        "active_exercise_count": active_exercise_count,
        "inactive_exercise_count": inactive_exercise_count,
        "exercise_status": exercise_status,
        "can_manage_workouts": can_manage,
    }

    return render(
        request,
        "workouts/workout_list.html",
        context,
    )


@trainer_permission("can_view_workouts")
def plan_detail(request, plan_id):
    plan = get_object_or_404(
        WorkoutPlan,
        id=plan_id,
        is_active=True,
    )

    can_manage_workouts = _can_manage_workouts(request)

    if request.method == "POST":
        if not can_manage_workouts:
            messages.error(
                request,
                "You do not have permission to manage this workout plan.",
            )
            return redirect(
                "workouts:plan_detail",
                plan_id=plan.id,
            )

        action = request.POST.get("action")

        if action == "add_exercise":
            form = WorkoutExerciseForm(request.POST)

            if form.is_valid():
                item = form.save(commit=False)
                item.plan = plan

                if not item.order:
                    last_item = (
                        WorkoutExercise.objects
                        .filter(plan=plan)
                        .order_by("-order", "-id")
                        .first()
                    )
                    item.order = last_item.order + 1 if last_item else 1

                item.save()

                messages.success(
                    request,
                    f"{item.exercise.name} was added to {plan.name}.",
                )
                return redirect(
                    "workouts:plan_detail",
                    plan_id=plan.id,
                )

            messages.error(
                request,
                "Could not add the exercise. Please check the form.",
            )

        elif action == "edit_exercise":
            item = get_object_or_404(
                WorkoutExercise,
                id=request.POST.get("item_id"),
                plan=plan,
            )

            form = WorkoutExerciseForm(
                request.POST,
                instance=item,
            )

            if form.is_valid():
                updated_item = form.save()

                messages.success(
                    request,
                    f"{updated_item.exercise.name} was updated.",
                )
                return redirect(
                    "workouts:plan_detail",
                    plan_id=plan.id,
                )

            messages.error(
                request,
                "Could not update the exercise. Please check the form.",
            )

        elif action == "delete_exercise":
            item = get_object_or_404(
                WorkoutExercise,
                id=request.POST.get("item_id"),
                plan=plan,
            )

            name = item.exercise.name
            item.delete()

            messages.success(
                request,
                f"{name} was removed from the plan.",
            )
            return redirect(
                "workouts:plan_detail",
                plan_id=plan.id,
            )

        else:
            messages.error(
                request,
                "Invalid workout plan action.",
            )
            return redirect(
                "workouts:plan_detail",
                plan_id=plan.id,
            )

    plan_exercises = (
        WorkoutExercise.objects
        .filter(plan=plan)
        .select_related("exercise")
        .order_by("order", "id")
    )

    all_exercises = (
        Exercise.objects
        .filter(is_active=True)
        .order_by("name")
    )

    members = (
        Member.objects
        .filter(status="active")
        .order_by("first_name", "last_name")
    )

    add_form = WorkoutExerciseForm()
    add_form.fields["exercise"].queryset = all_exercises

    context = {
        "plan": plan,
        "plan_exercises": plan_exercises,
        "all_exercises": all_exercises,
        "workout_exercises": plan_exercises,
        "available_exercises": all_exercises,
        "members": members,
        "add_form": add_form,
        "can_manage_workouts": can_manage_workouts,
        "can_manage": can_manage_workouts,
    }

    return render(
        request,
        "workouts/plan_detail.html",
        context,
    )
