from django import forms

from members.models import Member

from .models import Exercise, WorkoutExercise, WorkoutPlan, MemberWorkout


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = [
            "name",
            "category",
            "description",
            "posture_instructions",
            "breathing_instructions",
            "technique_instructions",
            "common_mistakes",
            "safety_notes",
            "additional_instructions",
            "demo_video_url",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "e.g. Barbell Bench Press",
                "class": "form-input",
            }),
            "category": forms.Select(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Briefly describe the exercise...",
                "class": "form-input",
            }),
            "posture_instructions": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Explain the correct starting posture...",
                "class": "form-input",
            }),
            "breathing_instructions": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Explain when to inhale and exhale...",
                "class": "form-input",
            }),
            "technique_instructions": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Step-by-step technique instructions...",
                "class": "form-input",
            }),
            "common_mistakes": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Common mistakes to avoid...",
                "class": "form-input",
            }),
            "safety_notes": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Safety precautions...",
                "class": "form-input",
            }),
            "additional_instructions": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Any additional instructions from the trainer...",
                "class": "form-input",
            }),
            "demo_video_url": forms.URLInput(attrs={
                "placeholder": "https://...",
                "class": "form-input",
            }),
        }


class WorkoutPlanForm(forms.ModelForm):
    class Meta:
        model = WorkoutPlan
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Push Day, Beginner Full Body",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Describe the goal and focus of this workout plan...",
            }),
        }


class WorkoutExerciseForm(forms.ModelForm):
    class Meta:
        model = WorkoutExercise
        fields = [
            "exercise",
            "order",
            "sets",
            "reps",
            "target_weight",
            "duration_minutes",
            "rest_seconds",
            "trainer_notes",
        ]
        widgets = {
            "exercise": forms.Select(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "sets": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "reps": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. 8-12",
            }),
            "target_weight": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. 40 kg",
            }),
            "duration_minutes": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "placeholder": "Minutes",
            }),
            "rest_seconds": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0,
                "placeholder": "Seconds",
            }),
            "trainer_notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Trainer-specific instructions...",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["exercise"].queryset = (
            Exercise.objects.filter(is_active=True).order_by("name")
        )


class MemberWorkoutForm(forms.ModelForm):
    class Meta:
        model = MemberWorkout
        fields = [
            "member",
            "plan",
            "start_date",
            "end_date",
            "trainer_notes",
        ]
        widgets = {
            "member": forms.Select(attrs={"class": "form-control"}),
            "plan": forms.Select(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "end_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "trainer_notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional notes for this member...",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["member"].queryset = (
            Member.objects.filter(status="active").order_by(
                "first_name", "last_name"
            )
        )
        self.fields["plan"].queryset = (
            WorkoutPlan.objects.filter(is_active=True).order_by("name")
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            self.add_error(
                "end_date",
                "End date cannot be earlier than the start date.",
            )

        return cleaned_data
