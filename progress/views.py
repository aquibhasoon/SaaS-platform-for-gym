from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import trainer_permission
from members.models import Member

from .forms import ProgressRecordForm
from .models import ProgressRecord


def _can_manage_progress(user):
    return (
        user.role == "owner"
        or (
            user.role == "trainer"
            and getattr(
                getattr(user, "trainer_permissions", None),
                "can_manage_progress",
                False,
            )
        )
    )


@login_required
@trainer_permission("can_view_progress")
def progress_list(request):
    records = (
        ProgressRecord.objects
        .select_related("member", "recorded_by")
        .order_by("-measurement_date", "-id")
    )

    search = request.GET.get("search", "").strip()
    member_id = request.GET.get("member", "").strip()

    if search:
        records = records.filter(
            member__first_name__icontains=search
        ) | records.filter(
            member__last_name__icontains=search
        ) | records.filter(
            member__member_id__icontains=search
        )

    if member_id:
        records = records.filter(member_id=member_id)

    members = (
        Member.objects
        .filter(status="active")
        .order_by("first_name", "last_name")
    )

    context = {
        "records": records,
        "members": members,
        "search": search,
        "member_id": member_id,
        "total_records": records.count(),
        "can_manage_progress": _can_manage_progress(request.user),
    }

    return render(request, "progress/progress_list.html", context)


@login_required
@trainer_permission("can_manage_progress")
def progress_create(request):
    initial = {}

    member_id = request.GET.get("member")
    if member_id:
        member = Member.objects.filter(
            id=member_id,
            status="active",
        ).first()
        if member:
            initial["member"] = member

    if request.method == "POST":
        form = ProgressRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.recorded_by = request.user
            record.save()

            messages.success(
                request,
                f"Progress record for {record.member.full_name} was added successfully.",
            )
            return redirect(
                "progress:member_progress",
                member_id=record.member.id,
            )

        messages.error(request, "Please correct the progress details.")
    else:
        form = ProgressRecordForm(initial=initial)

    return render(
        request,
        "progress/progress_form.html",
        {"form": form},
    )


@login_required
@trainer_permission("can_manage_progress")
def progress_edit(request, record_id):
    record = get_object_or_404(
        ProgressRecord.objects.select_related("member"),
        id=record_id,
    )

    if request.method == "POST":
        form = ProgressRecordForm(request.POST, instance=record)
        if form.is_valid():
            updated_record = form.save(commit=False)
            updated_record.recorded_by = record.recorded_by or request.user
            updated_record.save()

            messages.success(
                request,
                "Progress record updated successfully.",
            )
            return redirect(
                "progress:member_progress",
                member_id=updated_record.member.id,
            )

        messages.error(request, "Please correct the progress details.")
    else:
        form = ProgressRecordForm(instance=record)

    return render(
        request,
        "progress/progress_form.html",
        {
            "form": form,
            "record": record,
        },
    )


@login_required
@trainer_permission("can_manage_progress")
def progress_delete(request, record_id):
    record = get_object_or_404(
        ProgressRecord.objects.select_related("member"),
        id=record_id,
    )

    if request.method != "POST":
        return redirect("progress:list")

    member_name = record.member.full_name
    member_id = record.member.id
    record.delete()

    messages.success(
        request,
        f"Progress record for {member_name} was deleted.",
    )

    return redirect(
        "progress:member_progress",
        member_id=member_id,
    )


@login_required
@trainer_permission("can_view_progress")
def member_progress(request, member_id):
    member = get_object_or_404(Member, id=member_id)

    all_records = list(
        ProgressRecord.objects
        .filter(member=member)
        .select_related("recorded_by")
        .order_by("-measurement_date", "-id")
    )

    # Optional history/chart date range.
    from_date = request.GET.get("from_date", "").strip()
    to_date = request.GET.get("to_date", "").strip()

    filtered_records = all_records

    if from_date:
        try:
            parsed_from = datetime.strptime(
                from_date, "%Y-%m-%d"
            ).date()
            filtered_records = [
                record for record in filtered_records
                if record.measurement_date >= parsed_from
            ]
        except ValueError:
            from_date = ""

    if to_date:
        try:
            parsed_to = datetime.strptime(
                to_date, "%Y-%m-%d"
            ).date()
            filtered_records = [
                record for record in filtered_records
                if record.measurement_date <= parsed_to
            ]
        except ValueError:
            to_date = ""

    # Summary always uses the member's complete history.
    latest = all_records[0] if all_records else None
    first = all_records[-1] if all_records else None

    previous = all_records[1] if len(all_records) > 1 else None

    def change(field):
        if not latest or not first:
            return None
        latest_value = getattr(latest, field)
        first_value = getattr(first, field)
        if latest_value is None or first_value is None:
            return None
        return latest_value - first_value

    weight_change = change("weight")
    body_fat_change = change("body_fat")
    waist_change = change("waist")
    height_change = change("height")
    chest_change = change("chest")
    hip_change = change("hip")
    left_arm_change = change("left_arm")
    right_arm_change = change("right_arm")
    left_thigh_change = change("left_thigh")
    right_thigh_change = change("right_thigh")

    bmi = None
    bmi_status = None

    if latest and latest.weight is not None and latest.height:
        height_m = float(latest.height) / 100
        if height_m > 0:
            bmi = round(float(latest.weight) / (height_m ** 2), 1)
            if bmi < 18.5:
                bmi_status = "Underweight"
            elif bmi < 25:
                bmi_status = "Healthy range"
            elif bmi < 30:
                bmi_status = "Overweight"
            else:
                bmi_status = "Obesity range"

    # Charts use the selected date range, while the summary remains all-time.
    chart_records = list(reversed(filtered_records))

    chart_labels = [
        record.measurement_date.strftime("%d %b %Y")
        for record in chart_records
    ]

    def chart_data(field):
        return [
            float(getattr(record, field))
            if getattr(record, field) is not None
            else None
            for record in chart_records
        ]

    context = {
        "member": member,
        "records": filtered_records,
        "latest": latest,
        "previous": previous,
        "first": first,

        "weight_change": weight_change,
        "body_fat_change": body_fat_change,
        "waist_change": waist_change,
        "height_change": height_change,
        "chest_change": chest_change,
        "hip_change": hip_change,
        "left_arm_change": left_arm_change,
        "right_arm_change": right_arm_change,
        "left_thigh_change": left_thigh_change,
        "right_thigh_change": right_thigh_change,

        "bmi": bmi,
        "bmi_status": bmi_status,

        "record_count": len(all_records),
        "filtered_record_count": len(filtered_records),

        "from_date": from_date,
        "to_date": to_date,

        "chart_labels": chart_labels,
        "weight_data": chart_data("weight"),
        "body_fat_data": chart_data("body_fat"),
        "waist_data": chart_data("waist"),
        "chest_data": chart_data("chest"),
        "hip_data": chart_data("hip"),
        "left_arm_data": chart_data("left_arm"),
        "right_arm_data": chart_data("right_arm"),
        "left_thigh_data": chart_data("left_thigh"),
        "right_thigh_data": chart_data("right_thigh"),

        "can_manage_progress": _can_manage_progress(request.user),
    }

    return render(
        request,
        "progress/member_progress.html",
        context,
    )
