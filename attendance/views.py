import io

import qrcode

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import trainer_permission
from members.models import Member

from .models import Attendance


@trainer_permission("can_view_attendance")
def attendance_list(request):
    """
    Display attendance records for the selected day.

    Owners always have access. Trainers must have can_view_attendance.
    Members and inactive/unauthorized accounts are rejected by the
    trainer_permission decorator before reaching this view.
    """

    today = timezone.localdate()

    selected_date = request.GET.get(
        "date",
        ""
    ).strip()

    search = request.GET.get(
        "search",
        ""
    ).strip()

    # Default to today. Invalid dates also safely fall back to today.
    if selected_date:
        try:
            selected_date = timezone.datetime.strptime(
                selected_date,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    attendance_records = (
        Attendance.objects
        .select_related(
            "member",
            "scanned_by"
        )
        .filter(
            check_in__date=selected_date
        )
        .order_by("-check_in")
    )

    if search:
        attendance_records = attendance_records.filter(
            Q(member__first_name__icontains=search)
            | Q(member__last_name__icontains=search)
            | Q(member__member_id__icontains=search)
            | Q(member__phone__icontains=search)
        )

    total_checkins = Attendance.objects.filter(
        check_in__date=selected_date
    ).count()

    unique_members = (
        Attendance.objects
        .filter(check_in__date=selected_date)
        .values("member")
        .distinct()
        .count()
    )

    context = {
        "attendance_records": attendance_records,
        "selected_date": selected_date,
        "search": search,
        "total_checkins": total_checkins,
        "unique_members": unique_members,
    }

    return render(
        request,
        "attendance/attendance_list.html",
        context
    )


@trainer_permission("can_scan_attendance")
def scanner(request):
    """
    Process QR attendance scans.

    Scanning is strictly permission-controlled. The member is resolved
    only from the secure QR token submitted by the scanner. Attendance
    is always attributed to the currently authenticated user.
    """

    if request.method == "POST":

        token = request.POST.get(
            "qr_token",
            ""
        ).strip()

        if not token:
            messages.error(
                request,
                "No QR code was received."
            )
            return redirect("attendance:scanner")

        # UUIDField performs strict token conversion/filtering.
        # Invalid tokens simply result in no matching member.
        member = Member.objects.filter(
            qr_token=token
        ).first()

        if not member:
            messages.error(
                request,
                "Invalid QR code. Member not found."
            )
            return redirect("attendance:scanner")

        # Do not allow attendance for rejected/pending/inactive members.
        if (
            getattr(member, "approval_status", "approved") != "approved"
            or member.status != "active"
        ):
            messages.error(
                request,
                f"{member.full_name} is not an active approved member."
            )
            return redirect("attendance:scanner")

        today = timezone.localdate()

        # Lock the member row while checking and creating today's
        # attendance. This prevents two simultaneous scans from creating
        # duplicate check-ins through a race condition.
        with transaction.atomic():
            locked_member = (
                Member.objects
                .select_for_update()
                .get(pk=member.pk)
            )

            # Re-check state after acquiring the lock.
            if (
                getattr(locked_member, "approval_status", "approved")
                != "approved"
                or locked_member.status != "active"
            ):
                messages.error(
                    request,
                    f"{locked_member.full_name} is not an active approved member."
                )
                return redirect("attendance:scanner")

            # Membership must be valid for today.
            active_membership = locked_member.memberships.filter(
                status="active",
                start_date__lte=today,
                end_date__gte=today,
            ).first()

            if not active_membership:
                messages.error(
                    request,
                    f"{locked_member.full_name} does not have an active membership."
                )
                return redirect("attendance:scanner")

            # Prevent duplicate check-in on the same day.
            already_checked_in = Attendance.objects.filter(
                member=locked_member,
                check_in__date=today
            ).exists()

            if already_checked_in:
                messages.warning(
                    request,
                    f"{locked_member.full_name} has already checked in today."
                )
                return redirect("attendance:scanner")

            # Never accept scanned_by from POST data. It must always be
            # the authenticated staff account performing the scan.
            Attendance.objects.create(
                member=locked_member,
                scanned_by=request.user
            )

            member_name = locked_member.full_name

        messages.success(
            request,
            f"Welcome {member_name}! Attendance recorded successfully."
        )

        return redirect("attendance:scanner")

    return render(
        request,
        "attendance/scanner.html"
    )


@trainer_permission("can_view_members")
def member_qr(request, member_id):
    """
    Generate the member's secure QR image.

    Viewing a member QR follows the existing member-view permission,
    because the QR is part of the member record.
    """

    member = get_object_or_404(
        Member,
        member_id=member_id
    )

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )

    qr.add_data(
        str(member.qr_token)
    )

    qr.make(
        fit=True
    )

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="PNG"
    )

    return HttpResponse(
        buffer.getvalue(),
        content_type="image/png"
    )
