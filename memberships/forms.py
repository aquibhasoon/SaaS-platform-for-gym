from django import forms
from django.utils import timezone

from members.models import Member

from .models import Membership, MembershipPlan, Payment


class MembershipForm(forms.ModelForm):

    class Meta:
        model = Membership

        fields = [
            "member",
            "plan",
            "start_date",
            "amount",
            "status",
            "notes",
        ]

        widgets = {
            "member": forms.Select(
                attrs={"class": "form-control"}
            ),
            "plan": forms.Select(
                attrs={"class": "form-control"}
            ),
            "start_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control"
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01"
                }
            ),
            "status": forms.Select(
                attrs={"class": "form-control"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Optional notes..."
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["member"].queryset = (
            Member.objects
            .filter(status="active")
            .order_by("first_name", "last_name")
        )

        self.fields["plan"].queryset = (
            MembershipPlan.objects
            .filter(is_active=True)
            .order_by("duration_months", "price")
        )

        if not self.instance.pk:
            self.fields["start_date"].initial = (
                timezone.localdate()
            )

    def clean_amount(self):

        amount = self.cleaned_data["amount"]

        if amount < 0:
            raise forms.ValidationError(
                "Amount cannot be negative."
            )

        return amount


class PaymentForm(forms.ModelForm):

    class Meta:
        model = Payment

        fields = [
            "amount",
            "payment_method",
            "payment_date",
            "notes",
        ]

        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01"
                }
            ),

            "payment_method": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),

            "payment_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control"
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Optional notes..."
                }
            ),
        }

    def __init__(
        self,
        *args,
        membership=None,
        **kwargs
    ):

        super().__init__(*args, **kwargs)

        self.membership = membership

        if not self.instance.pk:
            self.fields["payment_date"].initial = (
                timezone.localdate()
            )

    def clean_amount(self):

        amount = self.cleaned_data["amount"]

        if amount <= 0:
            raise forms.ValidationError(
                "Payment amount must be greater than zero."
            )

        if self.membership:

            remaining = self.membership.balance_due

            if amount > remaining:

                raise forms.ValidationError(
                    f"Payment cannot exceed the "
                    f"pending amount of ₹{remaining}."
                )

        return amount