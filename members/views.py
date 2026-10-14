from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from trainers.authorization import (
    accessible_members,
    trainer_permission,
)

from audit_logs.utils import create_audit_log

from .forms import MemberForm
from .models import Member


VALID_MEMBER_ACTIONS = {
    "approve",
    "reject",
}


@trainer_permission("can_view_members")
def member_list(request):
    """
    Main member management page.

    Owners/trainers with the appropriate permission can view members.

    Approval and rejection are:
    - POST-only
    - owner-only
    - protected by Django CSRF middleware
    - performed atomically with the linked User account
    """

    if request.method == "POST":

        action = request.POST.get(
            "action",
            "",
        ).strip()

        member_id = request.POST.get(
            "member_id",
            "",
        ).strip()

        # Approval/rejection is deliberately restricted to owners.
        if request.user.role != "owner":
            messages.error(
                request,
                "Only the gym owner can approve or reject members.",
            )
            return redirect("members:list")

        if action not in VALID_MEMBER_ACTIONS:
            messages.error(
                request,
                "Invalid member action.",
            )
            return redirect("members:list")

        if not member_id:
            messages.error(
                request,
                "A valid member was not selected.",
            )
            return redirect("members:list")

        # Lock the member while changing both member and user state.
        with transaction.atomic():

            member = get_object_or_404(
                Member.objects.select_related("user"),
                id=member_id,
            )

            if action == "approve":

                member.approval_status = "approved"
                member.status = "active"

                if member.user:
                    member.user.is_active = True
                    member.user.save(
                        update_fields=[
                            "is_active",
                        ]
                    )

                member.save(
                    update_fields=[
                        "approval_status",
                        "status",
                        "updated_at",
                    ]
                )

                member_name = member.full_name

                create_audit_log(
                    request=request,
                    action="approve",
                    model_name="Member",
                    object_id=member.pk,
                    description=(
                        f"Approved member '{member_name}' "
                        f"({member.member_id})."
                    ),
                )

                messages.success(
                    request,
                    f"{member_name} has been approved.",
                )

                return redirect(
                    "members:list",
                )

            if action == "reject":

                member.approval_status = "rejected"
                member.status = "inactive"

                if member.user:
                    member.user.is_active = False
                    member.user.save(
                        update_fields=[
                            "is_active",
                        ]
                    )

                member.save(
                    update_fields=[
                        "approval_status",
                        "status",
                        "updated_at",
                    ]
                )

                member_name = member.full_name

                create_audit_log(
                    request=request,
                    action="reject",
                    model_name="Member",
                    object_id=member.pk,
                    description=(
                        f"Rejected registration for member "
                        f"'{member_name}' ({member.member_id})."
                    ),
                )

                messages.success(
                    request,
                    f"{member_name}'s registration was rejected.",
                )

                return redirect(
                    "members:list",
                )

    members = Member.objects.all()

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if search:
        members = members.filter(
            first_name__icontains=search
        ) | members.filter(
            last_name__icontains=search
        ) | members.filter(
            member_id__icontains=search
        ) | members.filter(
            phone__icontains=search
        )

    if status in {
        "active",
        "inactive",
    }:
        members = members.filter(
            status=status,
        )
    else:
        status = ""

    pending_members = []

    if request.user.role == "owner":
        pending_members = (
            Member.objects
            .filter(
                approval_status="pending",
            )
            .select_related("user")
            .order_by(
                "created_at",
            )
        )

    context = {
        "members": members,
        "search": search,
        "status": status,
        "pending_members": pending_members,
    }

    return render(
        request,
        "members/member_list.html",
        context,
    )


@trainer_permission("can_view_members")
def member_detail(
    request,
    member_id,
):
    """
    Display a member and their related membership,
    payment, and attendance information.

    Access is controlled by can_view_members
    and trainer/member assignment.
    """

    member = get_object_or_404(
        accessible_members(request.user),
        member_id=member_id,
    )

    memberships = (
        member.memberships
        .select_related("plan")
        .prefetch_related("payments")
        .all()
    )

    current_membership = next(
        (
            membership
            for membership in memberships
            if membership.is_currently_active
        ),
        None,
    )

    payments = []

    for membership in memberships:
        payments.extend(
            membership.payments.all()
        )

    payments.sort(
        key=lambda payment: (
            payment.payment_date,
            payment.id,
        ),
        reverse=True,
    )

    attendance_records = (
        member.attendance_records
        .select_related("scanned_by")
        .order_by(
            "-check_in",
        )[:10]
    )

    total_paid = sum(
        payment.amount
        for payment in payments
    )

    pending_amount = sum(
        membership.balance_due
        for membership in memberships
    )

    context = {
        "member": member,
        "memberships": memberships,
        "current_membership": current_membership,
        "payments": payments[:10],
        "attendance_records": attendance_records,
        "total_paid": total_paid,
        "pending_amount": pending_amount,
    }

    return render(
        request,
        "members/member_detail.html",
        context,
    )


@trainer_permission("can_add_members")
def member_create(request):
    """
    Create a member directly from the staff interface.

    Members created by authorized staff are immediately approved and
    active. Approval state is controlled server-side and is never
    trusted from submitted form data.
    """

    if request.method == "POST":

        form = MemberForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            with transaction.atomic():

                member = form.save(
                    commit=False,
                )

                # Never allow the submitted form to determine
                # approval or activation state.
                member.approval_status = "approved"
                member.status = "active"

                member.save()

                create_audit_log(
                    request=request,
                    action="create",
                    model_name="Member",
                    object_id=member.pk,
                    description=(
                        f"Created member '{member.full_name}' "
                        f"({member.member_id})."
                    ),
                )

            messages.success(
                request,
                (
                    f"{member.full_name} was added successfully "
                    "and is now active."
                ),
            )

            return redirect(
                "members:detail",
                member_id=member.member_id,
            )

    else:
        form = MemberForm()

    return render(
        request,
        "members/member_form.html",
        {
            "form": form,
        },
    )