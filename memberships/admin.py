from django.contrib import admin

from .models import MembershipPlan, Membership, Payment


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "duration_months",
        "price",
        "is_active",
        "created_at",
    )

    list_filter = (
        "duration_months",
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):

    list_display = (
        "member",
        "plan",
        "start_date",
        "end_date",
        "amount",
        "status",
    )

    list_filter = (
        "status",
        "plan",
        "start_date",
        "end_date",
    )

    search_fields = (
        "member__member_id",
        "member__first_name",
        "member__last_name",
        "member__phone",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "receipt_number",
        "member_name",
        "membership",
        "amount",
        "payment_method",
        "payment_date",
    )

    list_filter = (
        "payment_method",
        "payment_date",
    )

    search_fields = (
        "receipt_number",
        "membership__member__member_id",
        "membership__member__first_name",
        "membership__member__last_name",
        "membership__member__phone",
    )

    readonly_fields = (
        "receipt_number",
        "created_at",
    )

    def member_name(self, obj):
        return obj.membership.member.full_name

    member_name.short_description = "Member"