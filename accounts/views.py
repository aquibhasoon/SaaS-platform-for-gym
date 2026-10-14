from hashlib import sha256

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from audit_logs.utils import create_audit_log


STAFF_ROLES = {"owner", "trainer"}

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
    # Use the direct peer address here. Do not trust a forwarded
    # header until the deployment's trusted proxy configuration exists.
    return request.META.get("REMOTE_ADDR", "unknown")


def staff_login(request):
    """
    Login page for gym owners and trainers.

    Members use the separate member portal login.
    """

    if request.user.is_authenticated:

        if request.user.role == "member":
            return redirect("member_portal:dashboard")

        if request.user.role in STAFF_ROLES:
            return redirect("dashboard:home")

        logout(request)
        messages.error(
            request,
            "Your account role is not configured correctly.",
        )
        return redirect("accounts:login")

    next_url = request.GET.get("next", "").strip()

    if request.method == "POST":
        username = request.POST.get(
            "username",
            "",
        ).strip()

        password = request.POST.get(
            "password",
            "",
        )

        next_url = request.POST.get(
            "next",
            "",
        ).strip()

        ip_address = _request_ip(request)

        if not username or not password:
            messages.error(
                request,
                "Please enter your username and password.",
            )

        elif _login_blocked(
            "staff",
            username,
            ip_address,
        ):
            messages.error(
                request,
                "Too many failed login attempts. Please try again later.",
            )

        else:
            user = authenticate(
                request,
                username=username,
                password=password,
            )

            if user is None:
                _record_login_failure(
                    "staff",
                    username,
                    ip_address,
                )

                messages.error(
                    request,
                    "Invalid username or password.",
                )

            elif user.role == "member":
                _clear_login_failures(
                    "staff",
                    username,
                    ip_address,
                )

                messages.error(
                    request,
                    "Members must use the Member Portal login.",
                )

            elif user.role not in STAFF_ROLES:
                _clear_login_failures(
                    "staff",
                    username,
                    ip_address,
                )

                messages.error(
                    request,
                    "This account is not authorized to access the staff portal.",
                )

            elif not user.is_active:
                _clear_login_failures(
                    "staff",
                    username,
                    ip_address,
                )

                messages.error(
                    request,
                    "This account has been deactivated.",
                )

            else:
                _clear_login_failures(
                    "staff",
                    username,
                    ip_address,
                )

                login(request, user)

                create_audit_log(
                    request=request,
                    action="login",
                    model_name="User",
                    object_id=user.pk,
                    description=(
                        f"Staff user "
                        f"'{user.get_full_name() or user.username}' "
                        f"logged in successfully."
                    ),
                )

                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)

                return redirect("dashboard:home")

    return render(
        request,
        "accounts/login.html",
        {
            "next": next_url,
        },
    )


@login_required
def staff_logout(request):
    """
    Logout endpoint for owners and trainers.

    Logout is intentionally POST-only because it changes authentication state.
    """

    if request.method != "POST":
        return redirect("dashboard:home")

    if request.user.role not in STAFF_ROLES:
        messages.error(
            request,
            "You do not have permission to access the staff portal.",
        )

        if request.user.role == "member":
            return redirect("member_portal:dashboard")

        return redirect("accounts:login")

    user = request.user
    user_name = user.get_full_name() or user.username

    create_audit_log(
        request=request,
        action="logout",
        model_name="User",
        object_id=user.pk,
        description=(
            f"Staff user "
            f"'{user_name}' "
            f"logged out."
        ),
    )

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully.",
    )

    return redirect("accounts:login")
