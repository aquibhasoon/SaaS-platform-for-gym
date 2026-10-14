from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from memberships.models import Membership


def gym_settings(request):
    """
    Existing gym settings context processor.

    Keeps gym information available globally to templates.
    """
    from .models import GymSettings

    return {
        "gym_settings": GymSettings.get_settings()
    }


def notifications(request):
    """
    Build live notifications from existing membership data.

    Notifications are calculated from the database each time a
    management-system page is rendered.

    Members using the member portal are excluded.
    """

    # Not logged in
    if not request.user.is_authenticated:
        return {
            "notifications": [],
            "notification_count": 0,
            "notification_high_count": 0,
        }

    # Member portal has its own notification experience.
    if request.user.role == "member":
        return {
            "notifications": [],
            "notification_count": 0,
            "notification_high_count": 0,
        }

    today = timezone.localdate()

    three_days = today + timedelta(days=3)
    seven_days = today + timedelta(days=7)

    notification_items = []

    # ---------------------------------------------------------
    # EXPIRED MEMBERSHIPS
    # ---------------------------------------------------------

    expired_memberships = (
        Membership.objects
        .select_related("member", "plan")
        .filter(
            status="expired",
            end_date__lt=today
        )
        .order_by("-end_date")[:10]
    )

    for membership in expired_memberships:
        notification_items.append({
            "type": "expired",
            "priority": "high",
            "icon": "🔴",
            "title": "Membership expired",
            "message": (
                f"{membership.member.full_name}'s "
                f"{membership.plan.name} membership expired "
                f"on {membership.end_date.strftime('%d %b %Y')}."
            ),
            "url": (
                f"/memberships/{membership.id}/"
            ),
            "date": membership.end_date,
        })

    # ---------------------------------------------------------
    # EXPIRING TODAY
    # ---------------------------------------------------------

    expiring_today = (
        Membership.objects
        .select_related("member", "plan")
        .filter(
            status="active",
            start_date__lte=today,
            end_date=today
        )
        .order_by("member__first_name")
    )

    for membership in expiring_today:
        notification_items.append({
            "type": "expiring_today",
            "priority": "high",
            "icon": "⚠️",
            "title": "Membership expires today",
            "message": (
                f"{membership.member.full_name}'s "
                f"{membership.plan.name} membership "
                f"expires today."
            ),
            "url": (
                f"/memberships/{membership.id}/"
            ),
            "date": membership.end_date,
        })

    # ---------------------------------------------------------
    # EXPIRING WITHIN 3 DAYS
    # ---------------------------------------------------------

    expiring_soon = (
        Membership.objects
        .select_related("member", "plan")
        .filter(
            status="active",
            start_date__lte=today,
            end_date__gt=today,
            end_date__lte=three_days
        )
        .order_by("end_date")
    )

    for membership in expiring_soon:
        days_left = (membership.end_date - today).days

        notification_items.append({
            "type": "expiring_soon",
            "priority": "medium",
            "icon": "🟠",
            "title": "Membership expiring soon",
            "message": (
                f"{membership.member.full_name}'s "
                f"{membership.plan.name} membership "
                f"expires in {days_left} day"
                f"{'s' if days_left != 1 else ''}."
            ),
            "url": (
                f"/memberships/{membership.id}/"
            ),
            "date": membership.end_date,
        })

    # ---------------------------------------------------------
    # EXPIRING WITHIN 7 DAYS
    # ---------------------------------------------------------

    expiring_week = (
        Membership.objects
        .select_related("member", "plan")
        .filter(
            status="active",
            start_date__lte=today,
            end_date__gt=three_days,
            end_date__lte=seven_days
        )
        .order_by("end_date")
    )

    for membership in expiring_week:
        days_left = (membership.end_date - today).days

        notification_items.append({
            "type": "expiring_week",
            "priority": "normal",
            "icon": "🟡",
            "title": "Membership expiring",
            "message": (
                f"{membership.member.full_name}'s "
                f"{membership.plan.name} membership "
                f"expires in {days_left} days."
            ),
            "url": (
                f"/memberships/{membership.id}/"
            ),
            "date": membership.end_date,
        })

    # ---------------------------------------------------------
    # PENDING PAYMENTS
    # ---------------------------------------------------------

    pending_memberships = (
        Membership.objects
        .select_related("member", "plan")
        .prefetch_related("payments")
        .filter(
            status__in=["active", "expired"]
        )
        .order_by("-end_date")
    )

    pending_count = 0

    for membership in pending_memberships:

        balance = membership.balance_due

        if balance <= 0:
            continue

        pending_count += 1

        notification_items.append({
            "type": "payment",
            "priority": "financial",
            "icon": "💰",
            "title": "Pending payment",
            "message": (
                f"{membership.member.full_name} has "
                f"₹{balance:,.2f} pending for "
                f"{membership.plan.name}."
            ),
            "url": (
                f"/memberships/{membership.id}/"
            ),
            "date": membership.end_date,
        })

        # Avoid making the notification panel enormous.
        if pending_count >= 10:
            break

    # ---------------------------------------------------------
    # ORDER
    # ---------------------------------------------------------

    priority_order = {
        "high": 0,
        "medium": 1,
        "financial": 2,
        "normal": 3,
    }

    notification_items.sort(
        key=lambda item: (
            priority_order.get(item["priority"], 99),
            item.get("date") or today
        )
    )

    # Keep the global notification panel manageable.
    notification_items = notification_items[:30]

    high_count = sum(
        1
        for item in notification_items
        if item["priority"] == "high"
    )

    return {
        "notifications": notification_items,
        "notification_count": len(notification_items),
        "notification_high_count": high_count,
    }