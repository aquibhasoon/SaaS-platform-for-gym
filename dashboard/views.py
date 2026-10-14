from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from attendance.models import Attendance
from members.models import Member
from memberships.models import Membership, Payment


def update_expired_memberships():
    """
    Keep membership status synchronized with the current date.
    Cancelled memberships are not modified.
    """
    today = timezone.localdate()

    Membership.objects.filter(
        status="active",
        end_date__lt=today,
    ).update(
        status="expired"
    )


@login_required
def dashboard(request):

    # Members use their own portal.
    if request.user.role == "member":
        return redirect("member_portal:dashboard")

    # Keep membership statuses current before calculating dashboard data.
    update_expired_memberships()

    today = timezone.localdate()
    seven_days_from_today = today + timedelta(days=7)

    # =========================================================
    # MEMBERS
    # =========================================================

    total_members = Member.objects.count()

    active_members = Member.objects.filter(
        status="active"
    ).count()

    inactive_members = Member.objects.filter(
        status="inactive"
    ).count()

    # =========================================================
    # MEMBERSHIPS
    # =========================================================

    active_memberships = Membership.objects.filter(
        status="active",
        start_date__lte=today,
        end_date__gte=today,
    ).count()

    expired_memberships = Membership.objects.filter(
        status="expired"
    ).count()

    expiring_memberships = (
        Membership.objects
        .select_related("member", "plan")
        .filter(
            status="active",
            start_date__lte=today,
            end_date__gte=today,
            end_date__lte=seven_days_from_today,
        )
        .order_by("end_date", "member__first_name")
    )

    # =========================================================
    # PAYMENTS
    # =========================================================

    total_revenue = (
        Payment.objects.aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    today_revenue = (
        Payment.objects
        .filter(payment_date=today)
        .aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    # Calculate pending amount from ALL memberships,
    # including memberships where no payment has been made yet.
    all_memberships = (
        Membership.objects
        .prefetch_related("payments")
        .all()
    )

    pending_fees = sum(
        membership.balance_due
        for membership in all_memberships
    )

    # =========================================================
    # ATTENDANCE
    # =========================================================

    today_attendance = Attendance.objects.filter(
        check_in__date=today
    ).count()

    recent_attendance = (
        Attendance.objects
        .select_related("member", "scanned_by")
        .order_by("-check_in")[:6]
    )

    # =========================================================
    # RECENT PAYMENTS
    # =========================================================

    recent_payments = (
        Payment.objects
        .select_related(
            "membership",
            "membership__member",
            "membership__plan",
        )
        .order_by(
            "-payment_date",
            "-id",
        )[:6]
    )

    # =========================================================
    # REVENUE CHART — LAST 7 DAYS
    # =========================================================

    revenue_chart = []

    for days_ago in range(6, -1, -1):

        chart_date = today - timedelta(days=days_ago)

        amount = (
            Payment.objects
            .filter(payment_date=chart_date)
            .aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        revenue_chart.append({
            "date": chart_date.strftime("%d %b"),
            "amount": float(amount),
        })

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {
        "today": today,

        # Members
        "total_members": total_members,
        "active_members": active_members,
        "inactive_members": inactive_members,

        # Memberships
        "active_memberships": active_memberships,
        "expired_memberships": expired_memberships,
        "expiring_memberships": expiring_memberships,

        # Payments
        "total_revenue": total_revenue,
        "today_revenue": today_revenue,
        "pending_fees": pending_fees,
        "recent_payments": recent_payments,

        # Attendance
        "today_attendance": today_attendance,
        "recent_attendance": recent_attendance,

        # Chart
        "revenue_chart": revenue_chart,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context
    )