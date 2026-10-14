from django.db import models
from django.db.models import Q
from django.utils import timezone

from members.models import Member


class MembershipPlan(models.Model):

    DURATION_CHOICES = (
        (1, "1 Month"),
        (3, "3 Months"),
        (6, "6 Months"),
        (12, "12 Months"),
    )

    name = models.CharField(max_length=100)

    duration_months = models.PositiveIntegerField(
        choices=DURATION_CHOICES
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["duration_months", "price"]
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="membership_plan_price_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.duration_months} months"


class Membership(models.Model):

    STATUS_CHOICES = (
        ("active", "Active"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    )

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    plan = models.ForeignKey(
        MembershipPlan,
        on_delete=models.PROTECT,
        related_name="memberships"
    )

    start_date = models.DateField()
    end_date = models.DateField()

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active"
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gte=models.F("start_date")),
                name="membership_end_date_after_start_date",
            ),
            models.CheckConstraint(
                condition=Q(amount__gte=0),
                name="membership_amount_non_negative",
            ),
        ]

    def __str__(self):
        return (
            f"{self.member.full_name} - "
            f"{self.plan.name}"
        )

    @property
    def is_currently_active(self):
        today = timezone.localdate()
        return (
            self.status == "active"
            and self.start_date <= today <= self.end_date
        )

    @property
    def days_remaining(self):
        if not self.is_currently_active:
            return 0
        today = timezone.localdate()
        return (self.end_date - today).days

    @property
    def total_paid(self):
        return sum(
            payment.amount
            for payment in self.payments.all()
        )

    @property
    def balance_due(self):
        return max(
            self.amount - self.total_paid,
            0
        )

    @property
    def is_fully_paid(self):
        return self.balance_due == 0


class Payment(models.Model):

    PAYMENT_METHOD_CHOICES = (
        ("cash", "Cash"),
        ("upi", "UPI"),
        ("card", "Card"),
        ("bank_transfer", "Bank Transfer"),
        ("other", "Other"),
    )

    membership = models.ForeignKey(
        Membership,
        on_delete=models.PROTECT,
        related_name="payments"
    )

    receipt_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=20,
        default="cash",
        choices=PAYMENT_METHOD_CHOICES
    )

    payment_date = models.DateField(default=timezone.localdate)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="payment_amount_positive",
            ),
        ]

    def save(self, *args, **kwargs):

        if not self.receipt_number:
            self.receipt_number = self.generate_receipt_number()

        super().save(*args, **kwargs)

    @staticmethod
    def generate_receipt_number():

        last_payment = (
            Payment.objects
            .order_by("-id")
            .first()
        )

        if last_payment:
            number = last_payment.id + 1
        else:
            number = 1

        return f"REC{number:06d}"

    def __str__(self):
        return f"{self.receipt_number} - ₹{self.amount}"

    @property
    def member(self):
        return self.membership.member
