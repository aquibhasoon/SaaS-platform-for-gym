from calendar import monthrange

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import trainer_permission
from audit_logs.utils import create_audit_log
from members.models import Member

from .forms import MembershipForm
from .models import Membership, MembershipPlan


VALID_MEMBERSHIP_STATUSES = {
    "active",
    "expired",
    "cancelled",
}


VALID_PLAN_DURATIONS = {
    value for value, _label in MembershipPlan.DURATION_CHOICES
}


def _handle_plan_action(request):
    """Handle owner-only membership-plan management actions."""
    if request.user.role != "owner":
        messages.error(request, "Only the gym owner can manage membership plans.")
        return False

    action = request.POST.get("action", "").strip()
    if action.startswith("plan_"):
        action = action[5:]

    if action == "create_plan":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        duration_raw = request.POST.get("duration_months", "").strip()
        price_raw = request.POST.get("price", "").strip()

        errors = []
        if not name:
            errors.append("Plan name is required.")
        elif len(name) > 100:
            errors.append("Plan name must be 100 characters or fewer.")

        try:
            duration = int(duration_raw)
        except (TypeError, ValueError):
            duration = None
        if duration not in VALID_PLAN_DURATIONS:
            errors.append("Please select a valid plan duration.")

        try:
            price = Decimal(price_raw)
        except (InvalidOperation, TypeError):
            price = None
        if price is None or price < 0:
            errors.append("Plan price must be a valid non-negative amount.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return True

        plan = MembershipPlan.objects.create(
            name=name,
            duration_months=duration,
            price=price,
            description=description,
            is_active=True,
        )

        create_audit_log(
            request=request,
            action="create",
            model_name="MembershipPlan",
            object_id=plan.pk,
            description=(
                f"Created membership plan '{plan.name}' "
                f"({plan.duration_months} months, ₹{plan.price})."
            ),
        )
        messages.success(request, f"Membership plan '{plan.name}' was created.")
        return True

    plan_id = request.POST.get("plan_id", "").strip()
    if not plan_id.isdigit():
        messages.error(request, "Invalid membership plan.")
        return True

    plan = get_object_or_404(MembershipPlan, pk=int(plan_id))

    if action == "toggle_plan":
        plan.is_active = not plan.is_active
        plan.save(update_fields=["is_active"])
        audit_action = "activate" if plan.is_active else "deactivate"
        create_audit_log(
            request=request,
            action=audit_action,
            model_name="MembershipPlan",
            object_id=plan.pk,
            description=(
                f"{'Activated' if plan.is_active else 'Deactivated'} "
                f"membership plan '{plan.name}'."
            ),
        )
        messages.success(
            request,
            f"Membership plan '{plan.name}' was {'activated' if plan.is_active else 'deactivated'}.",
        )
        return True

    if action == "delete_plan":
        if plan.memberships.exists():
            messages.error(
                request,
                f"'{plan.name}' cannot be deleted because it has existing memberships. Deactivate it instead.",
            )
            return True

        plan_name = plan.name
        plan_pk = plan.pk
        create_audit_log(
            request=request,
            action="delete",
            model_name="MembershipPlan",
            object_id=plan_pk,
            description=f"Deleted membership plan '{plan_name}'.",
        )
        plan.delete()
        messages.success(request, f"Membership plan '{plan_name}' was deleted.")
        return True

    if action == "edit_plan":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        duration_raw = request.POST.get("duration_months", "").strip()
        price_raw = request.POST.get("price", "").strip()

        errors = []
        if not name:
            errors.append("Plan name is required.")
        elif len(name) > 100:
            errors.append("Plan name must be 100 characters or fewer.")

        try:
            duration = int(duration_raw)
        except (TypeError, ValueError):
            duration = None
        if duration not in VALID_PLAN_DURATIONS:
            errors.append("Please select a valid plan duration.")

        try:
            price = Decimal(price_raw)
        except (InvalidOperation, TypeError):
            price = None
        if price is None or price < 0:
            errors.append("Plan price must be a valid non-negative amount.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return True

        old_name = plan.name
        old_duration = plan.duration_months
        old_price = plan.price

        plan.name = name
        plan.duration_months = duration
        plan.price = price
        plan.description = description
        plan.save(update_fields=["name", "duration_months", "price", "description"])

        create_audit_log(
            request=request,
            action="update",
            model_name="MembershipPlan",
            object_id=plan.pk,
            description=(
                f"Updated membership plan #{plan.pk}: "
                f"'{old_name}' ({old_duration} months, ₹{old_price}) "
                f"to '{plan.name}' ({plan.duration_months} months, ₹{plan.price})."
            ),
        )
        messages.success(request, f"Membership plan '{plan.name}' was updated.")
        return True

    messages.error(request, "Invalid membership plan action.")
    return True


def add_months(date, months):
    """
    Add calendar months while keeping the day valid.

    Example:
    January 31 + 1 month -> February 28/29
    """

    month = date.month - 1 + months
    year = date.year + month // 12
    month = month % 12 + 1

    day = min(
        date.day,
        monthrange(year, month)[1],
    )

    return date.replace(
        year=year,
        month=month,
        day=day,
    )


def update_expired_memberships():
    """
    Automatically mark memberships as expired when their
    end date has passed.

    Cancelled memberships are never changed.
    """

    today = timezone.localdate()

    Membership.objects.filter(
        status="active",
        end_date__lt=today,
    ).update(
        status="expired",
    )


@trainer_permission("can_view_memberships")
def membership_list(request):
    if request.method == "POST" and request.POST.get("action", "").startswith("plan_"):
        _handle_plan_action(request)
        return redirect("memberships:list")

    update_expired_memberships()

    memberships = (
        Membership.objects
        .select_related(
            "member",
            "plan",
        )
        .all()
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if search:
        memberships = memberships.filter(
            member__first_name__icontains=search
        ) | memberships.filter(
            member__last_name__icontains=search
        ) | memberships.filter(
            member__member_id__icontains=search
        ) | memberships.filter(
            plan__name__icontains=search
        )

    if status in VALID_MEMBERSHIP_STATUSES:
        memberships = memberships.filter(
            status=status,
        )
    else:
        status = ""

    all_memberships = (
        Membership.objects
        .select_related(
            "member",
            "plan",
        )
        .all()
    )

    today = timezone.localdate()

    total_memberships = all_memberships.count()

    active_memberships = all_memberships.filter(
        status="active",
        start_date__lte=today,
        end_date__gte=today,
    ).count()

    expired_memberships = all_memberships.filter(
        status="expired",
    ).count()

    cancelled_memberships = all_memberships.filter(
        status="cancelled",
    ).count()

    pending_amount = sum(
        membership.balance_due
        for membership in all_memberships
    )

    expiring_date = today + timezone.timedelta(
        days=7,
    )

    expiring_memberships = (
        all_memberships
        .filter(
            status="active",
            start_date__lte=today,
            end_date__gte=today,
            end_date__lte=expiring_date,
        )
        .order_by(
            "end_date",
        )
    )

    context = {
        "memberships": memberships,
        "search": search,
        "status": status,

        "total_memberships": total_memberships,
        "active_memberships": active_memberships,
        "expired_memberships": expired_memberships,
        "cancelled_memberships": cancelled_memberships,
        "pending_amount": pending_amount,

        "expiring_memberships": expiring_memberships,
        "today": today,
        "membership_plans": MembershipPlan.objects.order_by("duration_months", "price", "name"),
    }

    return render(
        request,
        "memberships/membership_list.html",
        context,
    )


@trainer_permission("can_create_memberships")
def membership_create(request):
    """
    Create a membership.

    Important security rules:
    - Member must be active and approved.
    - Selected plan must be active.
    - End date is always calculated server-side.
    - Membership amount is taken from the selected plan server-side.
    """

    member_id = request.GET.get(
        "member",
        "",
    ).strip()

    initial = {}

    if member_id:
        member = get_object_or_404(
            Member,
            member_id=member_id,
            status="active",
        )

        if getattr(
            member,
            "approval_status",
            "approved",
        ) != "approved":
            messages.error(
                request,
                "This member has not been approved.",
            )

            return redirect(
                "members:list",
            )

        initial["member"] = member

    if request.method == "POST":

        form = MembershipForm(
            request.POST,
        )

        if form.is_valid():

            membership = form.save(
                commit=False,
            )

            # Never trust the browser's member state.
            member = (
                Member.objects
                .filter(
                    pk=membership.member.pk,
                    status="active",
                )
                .first()
            )

            if not member:
                form.add_error(
                    "member",
                    "The selected member is not active.",
                )

            elif getattr(
                member,
                "approval_status",
                "approved",
            ) != "approved":
                form.add_error(
                    "member",
                    "The selected member has not been approved.",
                )

            else:
                # Never trust a submitted plan's active state.
                plan = (
                    MembershipPlan.objects
                    .filter(
                        pk=membership.plan.pk,
                        is_active=True,
                    )
                    .first()
                )

                if not plan:
                    form.add_error(
                        "plan",
                        "The selected membership plan is not active.",
                    )

                else:
                    # Use the current plan from the database.
                    membership.member = member
                    membership.plan = plan

                    # End date is always calculated on the server.
                    membership.end_date = add_months(
                        membership.start_date,
                        plan.duration_months,
                    )

                    if membership.end_date < membership.start_date:
                        form.add_error(
                            "start_date",
                            "The membership dates are invalid.",
                        )

                    else:
                        # The membership price must come from the plan.
                        membership.amount = plan.price

                        with transaction.atomic():
                            membership.save()

                            create_audit_log(
                                request=request,
                                action="create",
                                model_name="Membership",
                                object_id=membership.pk,
                                description=(
                                    f"Created membership for "
                                    f"'{membership.member.full_name}' "
                                    f"using plan '{membership.plan.name}' "
                                    f"from {membership.start_date} "
                                    f"to {membership.end_date}."
                                ),
                            )

                        messages.success(
                            request,
                            (
                                "Membership created successfully for "
                                f"{membership.member.full_name}."
                            ),
                        )

                        return redirect(
                            "memberships:detail",
                            membership_id=membership.id,
                        )

            messages.error(
                request,
                "Please correct the membership details.",
            )

    else:
        form = MembershipForm(
            initial=initial,
        )

    context = {
        "form": form,
    }

    return render(
        request,
        "memberships/membership_form.html",
        context,
    )


@trainer_permission("can_view_memberships")
def membership_detail(
    request,
    membership_id,
):
    update_expired_memberships()

    membership = get_object_or_404(
        Membership.objects.select_related(
            "member",
            "plan",
        ),
        id=membership_id,
    )

    payments = (
        membership.payments
        .order_by(
            "-payment_date",
            "-id",
        )
    )

    context = {
        "membership": membership,
        "payments": payments,
    }

    return render(
        request,
        "memberships/membership_detail.html",
        context,
    )


@trainer_permission("can_renew_memberships")
def membership_renew(
    request,
    membership_id,
):
    update_expired_memberships()

    old_membership = get_object_or_404(
        Membership.objects.select_related(
            "member",
            "plan",
        ),
        id=membership_id,
    )

    today = timezone.localdate()

    if old_membership.is_currently_active:
        start_date = (
            old_membership.end_date
            + timezone.timedelta(days=1)
        )
    else:
        start_date = today

    if request.method == "POST":

        plan_id = request.POST.get(
            "plan",
            "",
        ).strip()

        if not plan_id:
            messages.error(
                request,
                "Please select a membership plan.",
            )

            return redirect(
                "memberships:renew",
                membership_id=old_membership.id,
            )

        # Make sure the selected plan really exists and is active.
        plan = get_object_or_404(
            MembershipPlan,
            id=plan_id,
            is_active=True,
        )

        with transaction.atomic():

            # Lock the old membership so two simultaneous renewal
            # requests cannot both proceed from the same state.
            locked_membership = (
                Membership.objects
                .select_for_update()
                .select_related(
                    "member",
                    "plan",
                )
                .get(
                    id=old_membership.id,
                )
            )

            # Recalculate everything after acquiring the lock.
            if locked_membership.is_currently_active:
                locked_start_date = (
                    locked_membership.end_date
                    + timezone.timedelta(days=1)
                )
            else:
                locked_start_date = today

            locked_member = locked_membership.member

            # Do not allow renewals for inactive/unapproved members.
            if locked_member.status != "active":
                messages.error(
                    request,
                    "This member is inactive and cannot be renewed.",
                )

                return redirect(
                    "memberships:detail",
                    membership_id=locked_membership.id,
                )

            if getattr(
                locked_member,
                "approval_status",
                "approved",
            ) != "approved":
                messages.error(
                    request,
                    "This member has not been approved.",
                )

                return redirect(
                    "memberships:detail",
                    membership_id=locked_membership.id,
                )

            end_date = add_months(
                locked_start_date,
                plan.duration_months,
            )

            if end_date < locked_start_date:
                messages.error(
                    request,
                    "The selected membership plan produced an invalid date range.",
                )

                return redirect(
                    "memberships:renew",
                    membership_id=locked_membership.id,
                )

            # Prevent duplicate renewal submissions.
            #
            # If another request already created a renewal starting on
            # this exact date, don't create another identical membership.
            duplicate_renewal = (
                Membership.objects
                .filter(
                    member=locked_member,
                    start_date=locked_start_date,
                    status="active",
                )
                .exclude(
                    id=locked_membership.id,
                )
                .exists()
            )

            if duplicate_renewal:
                messages.warning(
                    request,
                    "A renewal for this membership period already exists.",
                )

                return redirect(
                    "memberships:detail",
                    membership_id=locked_membership.id,
                )

            new_membership = Membership.objects.create(
                member=locked_member,
                plan=plan,
                start_date=locked_start_date,
                end_date=end_date,
                amount=plan.price,
                status="active",
                notes=(
                    f"Renewal of membership "
                    f"#{locked_membership.id}"
                ),
            )

            create_audit_log(
                request=request,
                action="create",
                model_name="Membership",
                object_id=new_membership.pk,
                description=(
                    f"Renewed membership for "
                    f"'{locked_member.full_name}' "
                    f"using plan '{plan.name}'. "
                    f"New membership #{new_membership.id} "
                    f"runs from {new_membership.start_date} "
                    f"to {new_membership.end_date}."
                ),
            )

        messages.success(
            request,
            (
                "Membership renewed successfully for "
                f"{locked_member.full_name}."
            ),
        )

        return redirect(
            "memberships:detail",
            membership_id=new_membership.id,
        )

    plans = (
        MembershipPlan.objects
        .filter(
            is_active=True,
        )
        .order_by(
            "duration_months",
            "price",
        )
    )

    context = {
        "membership": old_membership,
        "plans": plans,
        "start_date": start_date,
    }

    return render(
        request,
        "memberships/membership_renew.html",
        context,
    )