from django import forms
from django.utils import timezone

from members.models import Member

from .models import ProgressRecord


class ProgressRecordForm(forms.ModelForm):
    class Meta:
        model = ProgressRecord

        fields = [
            "member",
            "measurement_date",
            "weight",
            "height",
            "body_fat",
            "chest",
            "waist",
            "hip",
            "left_arm",
            "right_arm",
            "left_thigh",
            "right_thigh",
            "trainer_notes",
        ]

        widgets = {
            "member": forms.Select(
                attrs={"class": "form-control"}
            ),
            "measurement_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "weight": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "e.g. 72.5",
                }
            ),
            "height": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "e.g. 175",
                }
            ),
            "body_fat": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                    "placeholder": "e.g. 18.5",
                }
            ),
            "chest": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "cm",
                }
            ),
            "waist": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "cm",
                }
            ),
            "hip": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "cm",
                }
            ),
            "left_arm": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "cm",
                }
            ),
            "right_arm": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "cm",
                }
            ),
            "left_thigh": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "cm",
                }
            ),
            "right_thigh": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "cm",
                }
            ),
            "trainer_notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Add observations, goals, or trainer notes...",
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

    def clean_body_fat(self):
        value = self.cleaned_data.get("body_fat")

        if value is not None and not 0 <= value <= 100:
            raise forms.ValidationError(
                "Body fat must be between 0 and 100%."
            )

        return value

    def clean_measurement_date(self):
        value = self.cleaned_data.get("measurement_date")

        if value and value > timezone.localdate():
            raise forms.ValidationError(
                "Measurement date cannot be in the future."
            )

        return value

    def clean(self):
        cleaned_data = super().clean()

        numeric_fields = [
            "weight",
            "height",
            "chest",
            "waist",
            "hip",
            "left_arm",
            "right_arm",
            "left_thigh",
            "right_thigh",
        ]

        for field_name in numeric_fields:
            value = cleaned_data.get(field_name)
            if value is not None and value < 0:
                self.add_error(
                    field_name,
                    "This measurement cannot be negative.",
                )

        return cleaned_data
