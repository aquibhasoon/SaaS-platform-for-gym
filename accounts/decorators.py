from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import TrainerPermission


def _active_user(request):
    """
    Return True only for an authenticated, active account.

    Django normally blocks inactive users at authentication time, but an
    already-authenticated session can otherwise remain valid until it is
    replaced. Checking here closes that gap for protected views.
    """
    return (
        request.user.is_authenticated
        and request.user.is_active
    )


def owner_required(view_func):
    """
    Protect a view so only an active owner can access it.
    """

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not _active_user(request):
            messages.error(
                request,
                "Your account is inactive. Please contact the gym owner.",
            )
            return redirect("accounts:login")

        if request.user.role != "owner":
            messages.error(
                request,
                "You do not have permission to access this page.",
            )
            return redirect("dashboard:home")

        return view_func(request, *args, **kwargs)

    return wrapper


def trainer_permission(permission):
    """
    Protect owner/trainer views using the granular TrainerPermission model.

    Owners always have access.
    Trainers must have the requested permission explicitly enabled.
    Members and other roles are denied.
    Missing trainer-permission records fail closed.
    """

    @wraps(trainer_permission)
    def decorator(view_func):

        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):

            if not _active_user(request):
                messages.error(
                    request,
                    "Your account is inactive. Please contact the gym owner.",
                )
                return redirect("accounts:login")

            # Owners have full management access.
            if request.user.role == "owner":
                return view_func(request, *args, **kwargs)

            # Only trainers can use trainer-level permissions.
            if request.user.role != "trainer":
                messages.error(
                    request,
                    "You do not have permission to access this page.",
                )
                return redirect("dashboard:home")

            # Fail closed if the trainer has no permission record.
            try:
                permissions = request.user.trainer_permissions
            except TrainerPermission.DoesNotExist:
                messages.error(
                    request,
                    "Trainer permissions have not been configured.",
                )
                return redirect("dashboard:home")

            # Reject unknown permission names instead of accidentally
            # granting access because of a typo.
            if not hasattr(permissions, permission):
                messages.error(
                    request,
                    "Invalid permission configuration.",
                )
                return redirect("dashboard:home")

            if not getattr(permissions, permission, False):
                messages.error(
                    request,
                    "You do not have permission to perform this action.",
                )
                return redirect("dashboard:home")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    "owner_required",
    "trainer_permission",
]
