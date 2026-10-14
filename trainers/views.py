from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import owner_required
from accounts.models import TrainerPermission
from audit_logs.utils import create_audit_log
from members.models import Member

from .forms import TrainerCreateForm, TrainerPermissionForm
from .models import TrainerMemberAssignment


User = get_user_model()


@owner_required
def trainer_list(request):
    """
    Owner-only trainer management.

    The same page manages trainer accounts, permissions, and
    trainer-to-member assignments. Assignment changes are POST-only.
    """

    trainers = (
        User.objects
        .filter(role="trainer")
        .prefetch_related("trainer_permissions")
        .order_by("first_name", "last_name")
    )

    create_form = TrainerCreateForm()
    selected_trainer = None
    permission_form = None

    if request.method == "POST":
        action = request.POST.get("action", "").strip()

        if action == "add_trainer":
            create_form = TrainerCreateForm(request.POST)

            if create_form.is_valid():
                with transaction.atomic():
                    trainer = create_form.save()
                    TrainerPermission.objects.get_or_create(user=trainer)

                    create_audit_log(
                        request=request,
                        action="create",
                        model_name="User",
                        object_id=trainer.pk,
                        description=(
                            f"Created trainer account "
                            f"'{trainer.get_full_name() or trainer.username}'."
                        ),
                    )

                trainer_name = trainer.get_full_name() or trainer.username
                messages.success(
                    request,
                    f"Trainer {trainer_name} created successfully.",
                )
                return redirect("trainers:list")

            messages.error(request, "Please correct the trainer details.")

        elif action == "permissions":
            trainer_id = request.POST.get("trainer_id", "").strip()

            if not trainer_id:
                messages.error(request, "A valid trainer was not selected.")
                return redirect("trainers:list")

            selected_trainer = get_object_or_404(
                User,
                id=trainer_id,
                role="trainer",
            )

            with transaction.atomic():
                permission, _ = (
                    TrainerPermission.objects
                    .select_for_update()
                    .get_or_create(user=selected_trainer)
                )

                permission_form = TrainerPermissionForm(
                    request.POST,
                    instance=permission,
                )

                if permission_form.is_valid():
                    permission_form.save()

                    trainer_name = (
                        selected_trainer.get_full_name()
                        or selected_trainer.username
                    )

                    create_audit_log(
                        request=request,
                        action="update",
                        model_name="TrainerPermission",
                        object_id=permission.pk,
                        description=(
                            f"Updated permissions for trainer "
                            f"'{trainer_name}'."
                        ),
                    )

                    messages.success(
                        request,
                        f"Permissions updated for {trainer_name}.",
                    )
                    return redirect("trainers:list")

            messages.error(
                request,
                "Please correct the permission settings.",
            )

        elif action == "toggle_status":
            trainer_id = request.POST.get("trainer_id", "").strip()

            if not trainer_id:
                messages.error(request, "A valid trainer was not selected.")
                return redirect("trainers:list")

            trainer = get_object_or_404(
                User,
                id=trainer_id,
                role="trainer",
            )

            with transaction.atomic():
                trainer.is_active = not trainer.is_active
                trainer.save(update_fields=["is_active"])

                audit_action = (
                    "activate"
                    if trainer.is_active
                    else "deactivate"
                )
                trainer_name = trainer.get_full_name() or trainer.username

                create_audit_log(
                    request=request,
                    action=audit_action,
                    model_name="User",
                    object_id=trainer.pk,
                    description=(
                        f"{'Activated' if trainer.is_active else 'Deactivated'} "
                        f"trainer account '{trainer_name}'."
                    ),
                )

            status = "activated" if trainer.is_active else "deactivated"
            messages.success(
                request,
                f"Trainer {trainer_name} has been {status}.",
            )
            return redirect("trainers:list")

        elif action == "assign_member":
            trainer_id = request.POST.get("trainer_id", "").strip()
            member_id = request.POST.get("member_id", "").strip()

            if not trainer_id or not member_id:
                messages.error(
                    request,
                    "A valid trainer and member must be selected.",
                )
                return redirect("trainers:list")

            trainer = get_object_or_404(
                User,
                id=trainer_id,
                role="trainer",
                is_active=True,
            )
            member = get_object_or_404(
                Member,
                id=member_id,
                status="active",
                approval_status="approved",
            )

            with transaction.atomic():
                assignment, created = (
                    TrainerMemberAssignment.objects
                    .select_for_update()
                    .get_or_create(
                        trainer=trainer,
                        member=member,
                        is_active=True,
                        defaults={
                            "assigned_by": request.user,
                        },
                    )
                )

                if not created and assignment.assigned_by_id != request.user.pk:
                    assignment.assigned_by = request.user
                    assignment.save(
                        update_fields=[
                            "assigned_by",
                            "updated_at",
                        ]
                    )

                if created:
                    create_audit_log(
                        request=request,
                        action="create",
                        model_name="TrainerMemberAssignment",
                        object_id=assignment.pk,
                        description=(
                            f"Assigned member '{member.full_name}' "
                            f"({member.member_id}) to trainer "
                            f"'{trainer.get_full_name() or trainer.username}'."
                        ),
                    )

            if created:
                messages.success(
                    request,
                    (
                        f"{member.full_name} was assigned to "
                        f"{trainer.get_full_name() or trainer.username}."
                    ),
                )
            else:
                messages.info(
                    request,
                    "That member is already assigned to this trainer.",
                )

            return redirect("trainers:list")

        elif action == "unassign_member":
            assignment_id = request.POST.get("assignment_id", "").strip()

            if not assignment_id:
                messages.error(
                    request,
                    "A valid member assignment was not selected.",
                )
                return redirect("trainers:list")

            assignment = get_object_or_404(
                TrainerMemberAssignment.objects.select_related(
                    "trainer",
                    "member",
                ),
                id=assignment_id,
                is_active=True,
            )

            with transaction.atomic():
                assignment.is_active = False
                assignment.save(
                    update_fields=[
                        "is_active",
                        "updated_at",
                    ]
                )

                create_audit_log(
                    request=request,
                    action="update",
                    model_name="TrainerMemberAssignment",
                    object_id=assignment.pk,
                    description=(
                        f"Unassigned member '{assignment.member.full_name}' "
                        f"({assignment.member.member_id}) from trainer "
                        f"'{assignment.trainer.get_full_name() or assignment.trainer.username}'."
                    ),
                )

            messages.success(
                request,
                f"{assignment.member.full_name} was unassigned.",
            )
            return redirect("trainers:list")

        else:
            messages.error(request, "Invalid trainer action.")
            return redirect("trainers:list")

    permission_trainer_id = request.GET.get("permissions", "").strip()

    if permission_trainer_id:
        selected_trainer = get_object_or_404(
            User,
            id=permission_trainer_id,
            role="trainer",
        )

        permission, _ = TrainerPermission.objects.get_or_create(
            user=selected_trainer
        )

        permission_form = TrainerPermissionForm(
            instance=permission
        )

    assignments = (
        TrainerMemberAssignment.objects
        .filter(is_active=True)
        .select_related("trainer", "member", "assigned_by")
        .order_by(
            "trainer__first_name",
            "trainer__last_name",
            "member__first_name",
            "member__last_name",
        )
    )

    available_members = (
        Member.objects
        .filter(
            status="active",
            approval_status="approved",
        )
        .order_by("first_name", "last_name")
    )

    return render(
        request,
        "trainers/trainer_list.html",
        {
            "trainers": trainers,
            "create_form": create_form,
            "selected_trainer": selected_trainer,
            "permission_form": permission_form,
            "member_assignments": assignments,
            "available_members": available_members,
        },
    )
