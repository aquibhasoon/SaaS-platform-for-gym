from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from hashlib import sha256

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from attendance.models import Attendance
from members.models import Member
from memberships.models import Membership, Payment
from workouts.models import MemberWorkout

from .forms import MemberRegistrationForm


User = get_user_model()

LOGIN_MAX_ATTEMPTS = 5
LOGIN_FAILURE_WINDOW = 15 * 60
LOGIN_BLOCK_TIME = 15 * 60


def _login_key(prefix, username, ip_address):
    identity = f"{username.lower()}|{ip_address}"
    digest = sha256(identity.encode("utf-8")).hexdigest()
    return f"gym_login:{prefix}:{digest}"


def _login_blocked(prefix, username, ip_address):
    return cache.get(
        _login_key(f"{prefix}:blocked", username, ip_address)
    ) is not None


def _record_login_failure(prefix, username, ip_address):
    key = _login_key(f"{prefix}:failures", username, ip_address)

    if cache.add(key, 1, timeout=LOGIN_FAILURE_WINDOW):
        attempts = 1
    else:
        try:
            attempts = cache.incr(key)
        except ValueError:
            cache.set(
                key,
                1,
                timeout=LOGIN_FAILURE_WINDOW,
            )
            attempts = 1

    if attempts >= LOGIN_MAX_ATTEMPTS:
        cache.set(
            _login_key(
                f"{prefix}:blocked",
                username,
                ip_address,
            ),
            True,
            timeout=LOGIN_BLOCK_TIME,
        )

    return attempts


def _clear_login_failures(prefix, username, ip_address):
    cache.delete(
        _login_key(
            f"{prefix}:failures",
            username,
            ip_address,
        )
    )
    cache.delete(
        _login_key(
            f"{prefix}:blocked",
            username,
            ip_address,
        )
    )


def _request_ip(request):
    # Use the direct peer address here. Do not trust forwarded headers
    # until the deployment's trusted proxy configuration is defined.
    return request.META.get("REMOTE_ADDR", "unknown")



def _get_authenticated_member(request):
    """Return the approved, active Member owned by the current session."""
    if not request.user.is_authenticated:
        return None

    if request.user.role != "member" or not request.user.is_active:
        return None

    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        return None

    if member.approval_status != "approved" or member.status != "active":
        return None

    return member


def member_login(request):

    if request.user.is_authenticated:

        if request.user.role == "member":
            if request.user.is_active:
                try:
                    member = request.user.member_profile
                except Member.DoesNotExist:
                    logout(request)
                else:
                    if (
                        member.approval_status == "approved"
                        and member.status == "active"
                    ):
                        return redirect("member_portal:dashboard")
                    logout(request)
            else:
                logout(request)

        else:
            return redirect("dashboard:home")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        ip_address = _request_ip(request)

        if not username or not password:

            messages.error(
                request,
                "Please enter your username and password."
            )

        elif _login_blocked(
            "member",
            username,
            ip_address,
        ):

            messages.error(
                request,
                "Too many failed login attempts. Please try again later."
            )

        else:

            user = authenticate(
                request,
                username=username,
                password=password,
            )

            if user is None:

                _record_login_failure(
                    "member",
                    username,
                    ip_address,
                )

                # Check whether this is a pending member.
                pending_user = (
                    User.objects
                    .filter(
                        username__iexact=username,
                        role="member"
                    )
                    .select_related("member_profile")
                    .first()
                )

                if pending_user:

                    try:
                        member = pending_user.member_profile

                        if member.approval_status == "pending":

                            messages.warning(
                                request,
                                "Your registration is waiting for owner approval."
                            )

                        elif member.approval_status == "rejected":

                            messages.error(
                                request,
                                "Your registration was not approved."
                            )

                        else:

                            messages.error(
                                request,
                                "Invalid username or password."
                            )

                    except Member.DoesNotExist:

                        messages.error(
                            request,
                            "Invalid username or password."
                        )

                else:

                    messages.error(
                        request,
                        "Invalid username or password."
                    )

            elif user.role != "member":

                _clear_login_failures(
                    "member",
                    username,
                    ip_address,
                )

                messages.error(
                    request,
                    "This login is for gym members only."
                )

            else:

                try:
                    member = user.member_profile

                    if member.approval_status == "pending":

                        messages.warning(
                            request,
                            "Your registration is waiting for owner approval."
                        )

                    elif member.approval_status == "rejected":

                        messages.error(
                            request,
                            "Your registration was not approved."
                        )

                    elif not user.is_active:

                        messages.error(
                            request,
                            "Your account is currently inactive."
                        )

                    else:

                        _clear_login_failures(
                            "member",
                            username,
                            ip_address,
                        )

                        login(
                            request,
                            user
                        )

                        return redirect(
                            "member_portal:dashboard"
                        )

                except Member.DoesNotExist:

                    messages.error(
                        request,
                        "Your member profile is not connected to this account."
                    )

    return render(
        request,
        "member_portal/login.html"
    )


def member_register(request):

    if request.user.is_authenticated:

        if request.user.role == "member":

            return redirect(
                "member_portal:dashboard"
            )

        return redirect(
            "dashboard:home"
        )

    if request.method == "POST":

        form = MemberRegistrationForm(
            request.POST
        )

        if form.is_valid():

            data = form.cleaned_data

            try:
                with transaction.atomic():

                    user = User.objects.create_user(
                        username=data["username"],
                        password=data["password"],
                        first_name=data["first_name"],
                        last_name=data["last_name"],
                        email=data["email"],
                        phone=data["phone"],
                        role="member",
                        is_active=False,
                    )

                    Member.objects.create(
                        user=user,
                        first_name=data["first_name"],
                        last_name=data["last_name"],
                        phone=data["phone"],
                        email=data["email"],
                        date_of_birth=data["date_of_birth"],
                        gender=data["gender"],
                        address=data["address"],
                        emergency_contact_name=(
                            data["emergency_contact_name"]
                        ),
                        emergency_contact_phone=(
                            data["emergency_contact_phone"]
                        ),
                        status="inactive",
                        approval_status="pending",
                    )

            except Exception:
                messages.error(
                    request,
                    "Registration could not be completed. "
                    "Please try again."
                )

            else:
                messages.success(
                    request,
                    "Registration submitted successfully. "
                    "Your account is now waiting for owner approval."
                )

                return redirect(
                    "member_portal:login"
                )

    else:

        form = MemberRegistrationForm()

    return render(
        request,
        "member_portal/register.html",
        {
            "form": form
        }
    )


@login_required
def member_dashboard(request):

    # Never trust a member id from the URL or request data. The only member
    # record used by this dashboard is the one-to-one profile of the
    # authenticated User.
    if request.user.role != "member":
        return redirect("dashboard:home")

    if not request.user.is_active:
        logout(request)
        messages.error(
            request,
            "Your account is currently inactive."
        )
        return redirect("member_portal:login")

    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        logout(request)
        messages.error(
            request,
            "Your member profile is not connected to this account."
        )
        return redirect("member_portal:login")

    if member.approval_status != "approved":
        logout(request)
        messages.warning(
            request,
            "Your account is not approved yet."
        )
        return redirect("member_portal:login")

    if member.status != "active":
        logout(request)
        messages.error(
            request,
            "Your membership account is currently inactive."
        )
        return redirect("member_portal:login")

    today = timezone.localdate()

    current_membership = (
        Membership.objects
        .select_related("plan")
        .filter(
            member=member,
            status="active",
            start_date__lte=today,
            end_date__gte=today,
        )
        .order_by("-end_date")
        .first()
    )

    latest_membership = (
        Membership.objects
        .select_related("plan")
        .filter(
            member=member
        )
        .order_by(
            "-start_date",
            "-id"
        )
        .first()
    )

    membership = (
        current_membership
        or latest_membership
    )

    days_remaining = 0

    if current_membership:

        days_remaining = (
            current_membership.end_date - today
        ).days

    payments = (
        Payment.objects
        .filter(
            membership__member=member
        )
        .select_related(
            "membership",
            "membership__plan",
        )
        .order_by(
            "-payment_date",
            "-id"
        )
    )

    total_paid = (
        payments.aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    total_membership_amount = sum(
        membership.amount
        for membership in Membership.objects.filter(
            member=member
        )
    )

    total_balance = max(
        total_membership_amount - total_paid,
        0,
    )

    recent_payments = payments[:5]

    attendance_records = (
        Attendance.objects
        .filter(
            member=member
        )
        .order_by(
            "-check_in"
        )
    )

    attendance_count = (
        attendance_records.count()
    )

    today_checked_in = (
        attendance_records
        .filter(
            check_in__date=today
        )
        .exists()
    )

    recent_attendance = (
        attendance_records[:7]
    )

    active_workouts = (
        MemberWorkout.objects
        .filter(
            member=member,
            status="active",
        )
        .select_related("plan")
        .prefetch_related(
            "plan__exercises__exercise"
        )
        .order_by(
            "-created_at"
        )
    )

    current_workout = (
        active_workouts.first()
    )

    progress_records = []

    for relation in member._meta.related_objects:

        related_model = relation.related_model

        fields = {
            field.name
            for field in related_model._meta.get_fields()
        }

        if (
            "measurement_date" in fields
            and "weight" in fields
            and "member" in fields
        ):

            manager = getattr(
                member,
                relation.get_accessor_name()
            )

            try:

                progress_records = (
                    manager.all()
                    .order_by(
                        "-measurement_date",
                        "-id",
                    )
                )

            except Exception:

                progress_records = []

            break

    latest_progress = (
        progress_records.first()
        if progress_records
        else None
    )

    progress_count = (
        progress_records.count()
        if progress_records
        else 0
    )

    context = {

        "member": member,

        "today": today,

        "membership": membership,

        "current_membership": (
            current_membership
        ),

        "days_remaining": days_remaining,

        "total_paid": total_paid,

        "total_balance": total_balance,

        "payments": recent_payments,

        "attendance_count": (
            attendance_count
        ),

        "today_checked_in": (
            today_checked_in
        ),

        "recent_attendance": (
            recent_attendance
        ),

        "active_workouts": (
            active_workouts
        ),

        "current_workout": (
            current_workout
        ),

        "latest_progress": (
            latest_progress
        ),

        "progress_count": (
            progress_count
        ),

        "progress_records": (
            progress_records[:5]
            if progress_records
            else []
        ),
    }

    return render(
        request,
        "member_portal/dashboard.html",
        context
    )


@login_required
def member_logout(request):
    """
    Log out the authenticated member.

    Logout is intentionally POST-only because it changes authentication state.
    """
    if request.method != "POST":
        return redirect("member_portal:dashboard")

    logout(request)

    return redirect(
        "member_portal:login"
    )