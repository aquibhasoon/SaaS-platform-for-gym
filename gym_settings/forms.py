from django import forms

from .models import GymSettings


class GymSettingsForm(forms.ModelForm):

    class Meta:
        model = GymSettings

        fields = [
            "gym_name",
            "tagline",
            "logo",
            "phone",
            "email",
            "website",
            "address",
            "city",
            "state",
            "country",
            "pincode",
            "currency_symbol",
            "receipt_footer",
        ]

        widgets = {

            "gym_name": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "e.g. PowerFit Fitness Centre",
                }
            ),

            "tagline": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Your gym tagline",
                }
            ),

            "logo": forms.ClearableFileInput(
                attrs={
                    "class": "form-input",
                    "accept": "image/*",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "+91 XXXXX XXXXX",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "gym@example.com",
                }
            ),

            "website": forms.URLInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "https://example.com",
                }
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "rows": 3,
                    "placeholder": "Full gym address",
                }
            ),

            "city": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "City",
                }
            ),

            "state": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "State",
                }
            ),

            "country": forms.TextInput(
                attrs={
                    "class": "form-input",
                }
            ),

            "pincode": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "PIN code",
                }
            ),

            "currency_symbol": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "₹",
                    "maxlength": "5",
                }
            ),

            "receipt_footer": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "rows": 3,
                    "placeholder": "Message displayed at the bottom of receipts",
                }
            ),
        }