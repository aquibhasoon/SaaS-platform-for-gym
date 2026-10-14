from datetime import datetime, timedelta

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import trainer_permission
from attendance.models import Attendance
from members.models import Member
from memberships.models import Membership, MembershipPlan, Payment


MAX_REPORT_DAYS = 366


@trainer_permission("can_view_reports")
def reports_dashboard(request):
    today = timezone.localdate()

    # =========================================================
    # DATE FILTER
    # =========================================================

    start_date_string = request.GET.get(
        "start_date",
        "",
    ).strip()

    end_date_string = request.GET.get(
        "end_date",
        "",
    ).strip()

    start_date = None
    end_date = None
    invalid_date_filter = False

    # ---------------------------------------------------------
    # Parse start date
    # ---------------------------------------------------------
    if start_date_string:
        try:
            start_date = datetime.strptime(
                start_date_string,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            invalid_date_filter = True

    # ---------------------------------------------------------
    # Parse end date
    # ---------------------------------------------------------
    if end_date_string:
        try:
            end_date = datetime.strptime(
                end_date_string,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            invalid_date_filter = True

    # ---------------------------------------------------------
    # Default report period: current month
    # ---------------------------------------------------------
    if not start_date:
        start_date = today.replace(day=1)

    if not end_date:
        end_date = today

    # ---------------------------------------------------------
    # Prevent reversed dates
    # ---------------------------------------------------------
    if end_date < start_date:
        start_date, end_date = end_date, start_date

    # ---------------------------------------------------------
    # Prevent extremely large report ranges
    # ---------------------------------------------------------
    report_days = (end_date - start_date).days + 1

    if report_days > MAX_REPORT_DAYS:
        messages.warning(
            request,
            "The report period cannot exceed 366 days.",
        )

        start_date = today.replace(day=1)
        end_date = today

    if invalid_date_filter:
        messages.warning(
            request,
            "One or more date filters were invalid. "
            "The available valid dates were used.",
        )

    # =========================================================
    # PAYMENTS / REVENUE
    # =========================================================

    payments = Payment.objects.filter(
        payment_date__range=[
            start_date,
            end_date,
        ]
    )

    total_revenue = (
        payments.aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    payment_count = payments.count()

    # =========================================================
    # MEMBERS
    # =========================================================

    new_members = Member.objects.filter(
        join_date__range=[
            start_date,
            end_date,
        ]
    )

    new_member_count = new_members.count()

    active_member_count = Member.objects.filter(
        status="active"
    ).count()

    inactive_member_count = Member.objects.filter(
        status="inactive"
    ).count()

    # =========================================================
    # MEMBERSHIPS
    # =========================================================

    active_memberships = Membership.objects.filter(
        status="active",
        start_date__lte=today,
        end_date__gte=today,
    )

    active_membership_count = (
        active_memberships.count()
    )

    expired_membership_count = Membership.objects.filter(
        end_date__lt=today
    ).count()

    memberships_started = Membership.objects.filter(
        start_date__range=[
            start_date,
            end_date,
        ]
    ).count()

    memberships_expiring = Membership.objects.filter(
        status="active",
        end_date__range=[
            today,
            today + timedelta(days=30),
        ]
    ).count()

    # =========================================================
    # PENDING PAYMENTS
    # =========================================================

    memberships_with_balance = (
        Membership.objects
        .select_related(
            "member",
            "plan",
        )
        .prefetch_related("payments")
        .all()
    )

    pending_amount = sum(
        membership.balance_due
        for membership in memberships_with_balance
    )

    pending_membership_count = sum(
        1
        for membership in memberships_with_balance
        if membership.balance_due > 0
    )

    # =========================================================
    # ATTENDANCE
    # =========================================================

    attendance_records = Attendance.objects.filter(
        check_in__date__range=[
            start_date,
            end_date,
        ]
    )

    attendance_count = attendance_records.count()

    unique_attendance_members = (
        attendance_records
        .values("member_id")
        .distinct()
        .count()
    )

    today_attendance = Attendance.objects.filter(
        check_in__date=today
    ).count()

    # =========================================================
    # PLAN PERFORMANCE
    # =========================================================

    plan_performance = []

    plans = (
        MembershipPlan.objects
        .filter(is_active=True)
        .annotate(
            membership_count=Count(
                "memberships",
                filter=Q(
                    memberships__start_date__range=[
                        start_date,
                        end_date,
                    ]
                ),
            )
        )
        .order_by(
            "-membership_count",
            "name",
        )
    )

    for plan in plans:
        plan_revenue = (
            Payment.objects
            .filter(
                membership__plan=plan,
                payment_date__range=[
                    start_date,
                    end_date,
                ],
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        plan_performance.append(
            {
                "name": plan.name,
                "membership_count": plan.membership_count,
                "revenue": plan_revenue,
            }
        )

    # =========================================================
    # REVENUE CHART
    # =========================================================

    revenue_labels = []
    revenue_data = []

    current_date = start_date

    while current_date <= end_date:
        daily_revenue = (
            Payment.objects
            .filter(
                payment_date=current_date,
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        revenue_labels.append(
            current_date.strftime("%d %b")
        )

        revenue_data.append(
            float(daily_revenue)
        )

        current_date += timedelta(days=1)

    # =========================================================
    # ATTENDANCE CHART
    # =========================================================

    attendance_labels = []
    attendance_data = []

    current_date = start_date

    while current_date <= end_date:
        daily_attendance = (
            Attendance.objects
            .filter(
                check_in__date=current_date,
            )
            .count()
        )

        attendance_labels.append(
            current_date.strftime("%d %b")
        )

        attendance_data.append(
            daily_attendance
        )

        current_date += timedelta(days=1)

    # =========================================================
    # PAYMENT METHODS
    # =========================================================

    payment_methods = []

    payment_method_data = (
        payments
        .values("payment_method")
        .annotate(
            total=Sum("amount"),
            count=Count("id"),
        )
        .order_by("-total")
    )

    payment_method_choices = dict(
        Payment.PAYMENT_METHOD_CHOICES
    )

    for item in payment_method_data:
        payment_methods.append(
            {
                "method": payment_method_choices.get(
                    item["payment_method"],
                    item["payment_method"],
                ),
                "amount": item["total"],
                "count": item["count"],
            }
        )

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {
        # Date filter
        "start_date": start_date,
        "end_date": end_date,

        # Revenue
        "total_revenue": total_revenue,
        "payment_count": payment_count,

        # Members
        "new_member_count": new_member_count,
        "active_member_count": active_member_count,
        "inactive_member_count": inactive_member_count,

        # Memberships
        "active_membership_count": active_membership_count,
        "expired_membership_count": expired_membership_count,
        "memberships_started": memberships_started,
        "memberships_expiring": memberships_expiring,

        # Pending
        "pending_amount": pending_amount,
        "pending_membership_count": pending_membership_count,

        # Attendance
        "attendance_count": attendance_count,
        "unique_attendance_members": unique_attendance_members,
        "today_attendance": today_attendance,

        # Performance
        "plan_performance": plan_performance,
        "payment_methods": payment_methods,

        # Charts
        "revenue_labels": revenue_labels,
        "revenue_data": revenue_data,
        "attendance_labels": attendance_labels,
        "attendance_data": attendance_data,
    }

    return render(
        request,
        "reports/reports.html",
        context,
    )