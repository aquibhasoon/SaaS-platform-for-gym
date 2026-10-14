from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import trainer_permission
from audit_logs.utils import create_audit_log
from memberships.forms import PaymentForm
from memberships.models import Membership, Payment


VALID_PAYMENT_METHODS = {
    "cash",
    "upi",
    "card",
    "bank_transfer",
    "other",
}


def _parse_date(value):
    """
    Safely parse a YYYY-MM-DD value.

    Returns:
        date object when valid
        None when empty or invalid
    """
    if not value:
        return None

    try:
        return timezone.datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()
    except (TypeError, ValueError):
        return None


@trainer_permission("can_view_payments")
def payment_list(request):
    payments = (
        Payment.objects
        .select_related(
            "membership",
            "membership__member",
            "membership__plan",
        )
        .order_by(
            "-payment_date",
            "-id",
        )
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    method = request.GET.get(
        "method",
        "",
    ).strip()

    from_date_input = request.GET.get(
        "from_date",
        "",
    ).strip()

    to_date_input = request.GET.get(
        "to_date",
        "",
    ).strip()

    # Safely validate date filters.
    from_date = _parse_date(from_date_input)
    to_date = _parse_date(to_date_input)

    if from_date_input and not from_date:
        messages.warning(
            request,
            "Invalid start date. Please use a valid date.",
        )

    if to_date_input and not to_date:
        messages.warning(
            request,
            "Invalid end date. Please use a valid date.",
        )

    if (
        from_date
        and to_date
        and from_date > to_date
    ):
        messages.warning(
            request,
            "Start date cannot be later than end date.",
        )
        from_date = None
        to_date = None

    if search:
        payments = payments.filter(
            Q(
                membership__member__first_name__icontains=search
            )
            | Q(
                membership__member__last_name__icontains=search
            )
            | Q(
                membership__member__member_id__icontains=search
            )
            | Q(
                receipt_number__icontains=search
            )
            | Q(
                membership__plan__name__icontains=search
            )
        )

    if method not in VALID_PAYMENT_METHODS:
        method = ""

    if method:
        payments = payments.filter(
            payment_method=method,
        )

    if from_date:
        payments = payments.filter(
            payment_date__gte=from_date,
        )

    if to_date:
        payments = payments.filter(
            payment_date__lte=to_date,
        )

    # Summary cards reflect the currently selected filters.
    filtered_total = (
        payments.aggregate(
            total=Sum("amount"),
        )["total"]
        or 0
    )

    filtered_count = payments.count()

    today = timezone.localdate()

    today_collected = (
        Payment.objects
        .filter(
            payment_date=today,
        )
        .aggregate(
            total=Sum("amount"),
        )["total"]
        or 0
    )

    # Include memberships with zero payments as well.
    all_memberships = (
        Membership.objects
        .prefetch_related("payments")
        .all()
    )

    pending_amount = sum(
        membership.balance_due
        for membership in all_memberships
    )

    fully_paid_memberships = sum(
        1
        for membership in all_memberships
        if membership.is_fully_paid
    )

    pending_memberships = sum(
        1
        for membership in all_memberships
        if membership.balance_due > 0
    )

    context = {
        "payments": payments,
        "search": search,
        "method": method,

        # Keep the original strings for the HTML date inputs.
        "from_date": from_date_input,
        "to_date": to_date_input,

        "total_collected": filtered_total,
        "today_collected": today_collected,
        "payment_count": filtered_count,
        "pending_amount": pending_amount,
        "fully_paid_memberships": fully_paid_memberships,
        "pending_memberships": pending_memberships,
    }

    return render(
        request,
        "payments/payment_list.html",
        context,
    )


@trainer_permission("can_add_payments")
def payment_create(request, membership_id):
    """
    Add a payment to a membership.

    The membership balance is always rechecked inside a database
    transaction with a row lock so concurrent payment requests cannot
    rely on an outdated balance.
    """

    membership = get_object_or_404(
        Membership.objects.select_related(
            "member",
            "plan",
        ),
        id=membership_id,
    )

    # Keep the existing behavior for already-paid memberships.
    if membership.is_fully_paid:
        messages.info(
            request,
            "This membership is already fully paid.",
        )

        return redirect(
            "memberships:detail",
            membership_id=membership.id,
        )

    if request.method == "POST":

        form = PaymentForm(
            request.POST,
            membership=membership,
        )

        if form.is_valid():
            amount = form.cleaned_data["amount"]

            if amount <= 0:
                form.add_error(
                    "amount",
                    "Payment amount must be greater than zero.",
                )

            else:
                with transaction.atomic():

                    # Lock the membership before checking its balance.
                    locked_membership = (
                        Membership.objects
                        .select_for_update()
                        .select_related(
                            "member",
                            "plan",
                        )
                        .get(
                            id=membership.id,
                        )
                    )

                    latest_balance = (
                        locked_membership.balance_due
                    )

                    if latest_balance <= 0:
                        form.add_error(
                            "amount",
                            "This membership is already fully paid.",
                        )

                    elif amount > latest_balance:
                        form.add_error(
                            "amount",
                            (
                                f"Only ₹{latest_balance:.2f} "
                                "is currently outstanding."
                            ),
                        )

                    else:
                        # Do not trust membership information coming
                        # from the browser. Always attach the payment
                        # to the locked membership object.
                        payment = form.save(
                            commit=False,
                        )

                        payment.membership = (
                            locked_membership
                        )

                        payment.save()

                        # Audit only after the payment has been
                        # successfully saved.
                        create_audit_log(
                            request=request,
                            action="payment",
                            model_name="Payment",
                            object_id=payment.pk,
                            description=(
                                f"Recorded payment of "
                                f"₹{payment.amount:.2f} for member "
                                f"'{locked_membership.member.full_name}' "
                                f"({locked_membership.member.member_id}) "
                                f"using {payment.get_payment_method_display()}. "
                                f"Receipt {payment.receipt_number}."
                            ),
                        )

                        messages.success(
                            request,
                            (
                                f"Payment of ₹{payment.amount:.2f} "
                                f"recorded successfully. "
                                f"Receipt {payment.receipt_number}."
                            ),
                        )

                        return redirect(
                            "payments:detail",
                            payment_id=payment.id,
                        )

            messages.error(
                request,
                "Please correct the payment amount.",
            )

    else:
        form = PaymentForm(
            membership=membership,
        )

    context = {
        "form": form,
        "membership": membership,
        "balance_due": membership.balance_due,
    }

    return render(
        request,
        "payments/payment_form.html",
        context,
    )


@trainer_permission("can_view_payments")
def payment_detail(request, payment_id):
    payment = get_object_or_404(
        Payment.objects.select_related(
            "membership",
            "membership__member",
            "membership__plan",
        ),
        id=payment_id,
    )

    total_paid = payment.membership.total_paid
    balance_due = payment.membership.balance_due

    context = {
        "payment": payment,
        "membership": payment.membership,
        "total_paid": total_paid,
        "balance_due": balance_due,
    }

    return render(
        request,
        "payments/payment_detail.html",
        context,
    )