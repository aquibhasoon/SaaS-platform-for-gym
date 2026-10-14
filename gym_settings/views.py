from django.contrib import messages
from django.shortcuts import redirect, render

from accounts.decorators import owner_required

from .forms import GymSettingsForm
from .models import GymSettings


@owner_required
def settings_dashboard(request):

    settings = GymSettings.get_settings()

    if request.method == "POST":

        form = GymSettingsForm(
            request.POST,
            request.FILES,
            instance=settings,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Gym settings were updated successfully.",
            )

            return redirect(
                "gym_settings:dashboard"
            )

        messages.error(
            request,
            "Please correct the highlighted fields.",
        )

    else:

        form = GymSettingsForm(
            instance=settings
        )

    context = {
        "form": form,
        "gym_settings": settings,
    }

    return render(
        request,
        "gym_settings/settings.html",
        context,
    )