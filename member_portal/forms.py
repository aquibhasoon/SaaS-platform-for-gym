from django import forms
from django.contrib.auth import get_user_model

from members.models import Member


User = get_user_model()


class MemberRegistrationForm(forms.Form):

    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "placeholder": "First name"
            }
        )
    )

    last_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Last name"
            }
        )
    )

    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Phone number"
            }
        )
    )

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Email address"
            }
        )
    )

    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date"
            }
        )
    )

    gender = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Select gender"),
            *Member.GENDER_CHOICES,
        ]
    )

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Address",
                "rows": 3
            }
        )
    )

    emergency_contact_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Emergency contact name"
            }
        )
    )

    emergency_contact_phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Emergency contact phone"
            }
        )
    )

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Choose a username",
                "autocomplete": "username"
            }
        )
    )

    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Create a password",
                "autocomplete": "new-password"
            }
        )
    )

    confirm_password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirm password",
                "autocomplete": "new-password"
            }
        )
    )

    def clean_username(self):

        username = self.cleaned_data["username"].strip()

        if User.objects.filter(
            username__iexact=username
        ).exists():

            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    def clean_phone(self):

        phone = self.cleaned_data["phone"].strip()

        if Member.objects.filter(
            phone=phone
        ).exists():

            raise forms.ValidationError(
                "A member with this phone number already exists."
            )

        return phone

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get(
            "confirm_password"
        )

        if (
            password
            and confirm_password
            and password != confirm_password
        ):

            self.add_error(
                "confirm_password",
                "Passwords do not match."
            )

        return cleaned_data