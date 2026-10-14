from django import forms
from django.contrib.auth import get_user_model

from accounts.models import TrainerPermission


User = get_user_model()


class TrainerCreateForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=6,
        label="Password"
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "phone",
            "password",
        ]

    def save(self, commit=True):
        user = super().save(commit=False)

        user.role = "trainer"
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

            TrainerPermission.objects.get_or_create(
                user=user
            )

        return user


class TrainerPermissionForm(forms.ModelForm):

    class Meta:
        model = TrainerPermission
        exclude = ["user"]