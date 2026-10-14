from datetime import datetime

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render

from accounts.decorators import owner_required

from .models import AuditLog


VALID_ACTIONS = {
    choice[0]
    for choice in AuditLog.ACTION_CHOICES
}


def _parse_date(value):
    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()
    except (TypeError, ValueError):
        return None


@owner_required
def audit_log_list(request):
    """
    Owner-only audit log viewer.

    Audit records are read-only from this interface.
    """

    logs = (
        AuditLog.objects
        .select_related("user")
        .order_by("-created_at")
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    action = request.GET.get(
        "action",
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

    if from_date and to_date and from_date > to_date:
        messages.warning(
            request,
            "Start date cannot be later than end date.",
        )
        from_date = None
        to_date = None

    if action not in VALID_ACTIONS:
        action = ""

    if search:
        logs = logs.filter(
            Q(description__icontains=search)
            | Q(model_name__icontains=search)
            | Q(object_id__icontains=search)
            | Q(user__username__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
        )

    if action:
        logs = logs.filter(
            action=action,
        )

    if from_date:
        logs = logs.filter(
            created_at__date__gte=from_date,
        )

    if to_date:
        logs = logs.filter(
            created_at__date__lte=to_date,
        )

    total_logs = logs.count()

    context = {
        "logs": logs,
        "search": search,
        "action": action,
        "from_date": from_date_input,
        "to_date": to_date_input,
        "total_logs": total_logs,
        "action_choices": AuditLog.ACTION_CHOICES,
    }

    return render(
        request,
        "audit_logs/audit_log_list.html",
        context,
    )