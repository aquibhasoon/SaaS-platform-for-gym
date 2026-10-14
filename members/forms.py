from django import forms

from .models import Member


class MemberForm(forms.ModelForm):

    class Meta:
        model = Member

        fields = [
            "first_name",
            "last_name",
            "phone",
            "email",
            "date_of_birth",
            "gender",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "profile_photo",
            "status",
        ]

        widgets = {

            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "First name"
                }
            ),

            "last_name": forms.TextInput(
                attrs={
                    "placeholder": "Last name"
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "placeholder": "Phone number"
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Email address"
                }
            ),

            "date_of_birth": forms.DateInput(
                attrs={
                    "type": "date"
                }
            ),

            "gender": forms.Select(),

            "address": forms.Textarea(
                attrs={
                    "placeholder": "Address",
                    "rows": 3
                }
            ),

            "emergency_contact_name": forms.TextInput(
                attrs={
                    "placeholder": "Emergency contact name"
                }
            ),

            "emergency_contact_phone": forms.TextInput(
                attrs={
                    "placeholder": "Emergency contact phone"
                }
            ),

            "profile_photo": forms.ClearableFileInput(),

            "status": forms.Select(),
        }

        labels = {

            "first_name": "First Name",

            "last_name": "Last Name",

            "phone": "Phone Number",

            "email": "Email Address",

            "date_of_birth": "Date of Birth",

            "gender": "Gender",

            "address": "Address",

            "emergency_contact_name": (
                "Emergency Contact Name"
            ),

            "emergency_contact_phone": (
                "Emergency Contact Phone"
            ),

            "profile_photo": "Profile Photo",

            "status": "Member Status",
        }