from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from accounts.models import TrainerPermission
from .models import TrainerMemberAssignment
from members.models import Member


def _active_user(request):
    """
    Return True only for an authenticated, active account.
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

        return view_func(
            request,
            *args,
            **kwargs,
        )

    return wrapper


def trainer_permission(permission):
    """
    Protect owner/trainer views using the granular TrainerPermission model.

    Owners always have access.

    Trainers must:
    - have an active account
    - have role='trainer'
    - have a TrainerPermission record
    - have the requested permission enabled

    Members and other roles are denied.

    Missing trainer-permission records fail closed.
    """

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

            if request.user.role == "owner":
                return view_func(
                    request,
                    *args,
                    **kwargs,
                )

            if request.user.role != "trainer":
                messages.error(
                    request,
                    "You do not have permission to access this page.",
                )
                return redirect("dashboard:home")

            try:
                permissions = request.user.trainer_permissions
            except TrainerPermission.DoesNotExist:
                messages.error(
                    request,
                    "Trainer permissions have not been configured.",
                )
                return redirect("dashboard:home")

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

            return view_func(
                request,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator


def trainer_can_access_member(user, member):
    """
    Return True when the user is allowed to access the member.
    """

    if not user.is_authenticated or not user.is_active:
        return False

    if user.role == "owner":
        return True

    if user.role != "trainer":
        return False

    return TrainerMemberAssignment.objects.filter(
        trainer=user,
        member=member,
        is_active=True,
    ).exists()


def accessible_members(user):
    """
    Return the queryset of members the user is allowed to access.
    """

    if not user.is_authenticated or not user.is_active:
        return Member.objects.none()

    if user.role == "owner":
        return Member.objects.all()

    if user.role == "trainer":
        return Member.objects.filter(
            trainer_assignments__trainer=user,
            trainer_assignments__is_active=True,
        ).distinct()

    return Member.objects.none()


__all__ = [
    "owner_required",
    "trainer_permission",
    "trainer_can_access_member",
    "accessible_members",
]