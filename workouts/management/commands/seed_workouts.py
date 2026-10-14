from django.core.management.base import BaseCommand

from workouts.models import Exercise, WorkoutPlan, WorkoutExercise


class Command(BaseCommand):
    help = "Create default exercises and workout plans"

    def handle(self, *args, **options):

        exercises = [

            {
                "name": "Barbell Bench Press",
                "category": "chest",
                "description": "A compound exercise for developing the chest, shoulders and triceps.",
                "posture_instructions": "Lie flat on the bench with your eyes below the bar. Keep your feet firmly on the floor and shoulder blades pulled back.",
                "breathing_instructions": "Inhale while lowering the bar. Exhale while pressing the bar upward.",
                "technique_instructions": "Grip the bar slightly wider than shoulder width. Lower it under control toward the middle of your chest, then press it back up.",
                "common_mistakes": "Bouncing the bar off the chest, lifting the hips, or allowing the elbows to flare excessively.",
                "safety_notes": "Use a spotter when lifting heavy weights.",
            },

            {
                "name": "Incline Dumbbell Press",
                "category": "chest",
                "description": "Targets the upper chest with additional shoulder and triceps involvement.",
                "posture_instructions": "Set the bench to a moderate incline. Keep your back against the bench and feet firmly planted.",
                "breathing_instructions": "Inhale while lowering the dumbbells. Exhale while pressing upward.",
                "technique_instructions": "Lower the dumbbells slowly toward the upper chest and press them upward without locking the elbows aggressively.",
                "common_mistakes": "Using excessive weight, bouncing the dumbbells, or losing control at the bottom.",
                "safety_notes": "Choose a manageable weight and maintain control throughout the movement.",
            },

            {
                "name": "Cable Chest Fly",
                "category": "chest",
                "description": "An isolation exercise that focuses on the chest muscles.",
                "posture_instructions": "Stand upright with a stable stance and a slight bend in the knees.",
                "breathing_instructions": "Exhale while bringing the handles together. Inhale while returning them.",
                "technique_instructions": "Keep a slight bend in the elbows and bring the handles together in front of the chest.",
                "common_mistakes": "Using momentum or turning the movement into a pressing exercise.",
                "safety_notes": "Use controlled resistance and avoid excessive stretching.",
            },

            {
                "name": "Lat Pulldown",
                "category": "back",
                "description": "A pulling exercise that primarily targets the latissimus dorsi.",
                "posture_instructions": "Sit upright with your thighs secured under the pads and chest slightly raised.",
                "breathing_instructions": "Exhale while pulling the bar down. Inhale while returning it.",
                "technique_instructions": "Pull the bar toward the upper chest while keeping the torso stable and squeezing the back.",
                "common_mistakes": "Pulling behind the neck, swinging the torso, or using momentum.",
                "safety_notes": "Keep the movement controlled and avoid excessive loads.",
            },

            {
                "name": "Seated Cable Row",
                "category": "back",
                "description": "Builds the middle back while also engaging the biceps.",
                "posture_instructions": "Sit upright with your chest open and knees slightly bent.",
                "breathing_instructions": "Exhale while pulling the handle toward your body. Inhale while extending your arms.",
                "technique_instructions": "Pull the handle toward your lower chest or abdomen while squeezing the shoulder blades.",
                "common_mistakes": "Rounding the back or using excessive body movement.",
                "safety_notes": "Keep the spine neutral throughout the exercise.",
            },

            {
                "name": "Dumbbell Row",
                "category": "back",
                "description": "A unilateral back exercise that targets the lats and upper back.",
                "posture_instructions": "Support one hand on a bench and keep your back flat.",
                "breathing_instructions": "Exhale while pulling the dumbbell upward. Inhale while lowering it.",
                "technique_instructions": "Pull the dumbbell toward your hip while keeping the elbow close to your body.",
                "common_mistakes": "Rotating the torso or using momentum.",
                "safety_notes": "Maintain a stable spine and controlled movement.",
            },

            {
                "name": "Dumbbell Shoulder Press",
                "category": "shoulders",
                "description": "A pressing exercise for the shoulders and triceps.",
                "posture_instructions": "Sit or stand tall with the dumbbells positioned near shoulder height.",
                "breathing_instructions": "Exhale while pressing upward. Inhale while lowering the weights.",
                "technique_instructions": "Press the dumbbells overhead in a controlled path and return them slowly.",
                "common_mistakes": "Arching the lower back or using excessive weight.",
                "safety_notes": "Use a weight that allows full control.",
            },

            {
                "name": "Dumbbell Lateral Raise",
                "category": "shoulders",
                "description": "An isolation exercise focused on the lateral deltoids.",
                "posture_instructions": "Stand tall with feet shoulder-width apart and dumbbells beside your body.",
                "breathing_instructions": "Exhale while raising the dumbbells. Inhale while lowering them.",
                "technique_instructions": "Raise the arms outward until approximately shoulder height, then lower them slowly.",
                "common_mistakes": "Swinging the weights or shrugging the shoulders.",
                "safety_notes": "Use light to moderate weight and controlled movement.",
            },

            {
                "name": "Dumbbell Biceps Curl",
                "category": "biceps",
                "description": "A basic isolation exercise for the biceps.",
                "posture_instructions": "Stand upright with your elbows close to your torso.",
                "breathing_instructions": "Exhale while curling the dumbbells. Inhale while lowering them.",
                "technique_instructions": "Curl the dumbbells toward the shoulders without moving the upper arms.",
                "common_mistakes": "Swinging the body or moving the elbows forward.",
                "safety_notes": "Use controlled repetitions.",
            },

            {
                "name": "Cable Triceps Pushdown",
                "category": "triceps",
                "description": "An isolation exercise targeting the triceps.",
                "posture_instructions": "Stand upright with the cable handle held near chest height.",
                "breathing_instructions": "Exhale while pushing the handle down. Inhale while returning it.",
                "technique_instructions": "Keep the elbows close to the body and extend the arms downward.",
                "common_mistakes": "Moving the elbows excessively or leaning over the cable.",
                "safety_notes": "Avoid locking the elbows aggressively.",
            },

            {
                "name": "Barbell Squat",
                "category": "legs",
                "description": "A compound lower-body exercise targeting the quadriceps, glutes and hamstrings.",
                "posture_instructions": "Keep the chest up, spine neutral and feet approximately shoulder-width apart.",
                "breathing_instructions": "Take a breath before descending and exhale as you stand up.",
                "technique_instructions": "Brace the core, bend the knees and hips, descend under control, then drive through the feet to stand.",
                "common_mistakes": "Allowing the knees to collapse inward, rounding the back, or losing control.",
                "safety_notes": "Use appropriate weight and proper rack and safety equipment.",
            },

            {
                "name": "Leg Press",
                "category": "legs",
                "description": "A machine-based exercise targeting the quadriceps, glutes and hamstrings.",
                "posture_instructions": "Keep your back and hips firmly against the machine pad.",
                "breathing_instructions": "Inhale while lowering the platform. Exhale while pressing it away.",
                "technique_instructions": "Lower the platform under control and press through the feet without fully locking the knees.",
                "common_mistakes": "Lowering too far, lifting the hips, or locking the knees.",
                "safety_notes": "Never release the safety mechanism while under load.",
            },

            {
                "name": "Romanian Deadlift",
                "category": "legs",
                "description": "A hip-hinge movement that targets the hamstrings and glutes.",
                "posture_instructions": "Stand tall with a neutral spine and hold the bar close to your body.",
                "breathing_instructions": "Inhale before lowering and exhale while returning to standing.",
                "technique_instructions": "Push the hips backward while keeping the knees slightly bent and the spine neutral.",
                "common_mistakes": "Rounding the back or bending the knees excessively.",
                "safety_notes": "Keep the weight close to the legs and use controlled movement.",
            },

            {
                "name": "Hip Thrust",
                "category": "glutes",
                "description": "A glute-focused exercise performed using a bench and resistance.",
                "posture_instructions": "Position the upper back against the bench with feet planted firmly.",
                "breathing_instructions": "Exhale while driving the hips upward. Inhale while lowering.",
                "technique_instructions": "Drive through the feet and squeeze the glutes at the top without excessively arching the back.",
                "common_mistakes": "Hyperextending the lower back or placing the feet incorrectly.",
                "safety_notes": "Use suitable padding when using a barbell.",
            },

            {
                "name": "Plank",
                "category": "core",
                "description": "An isometric exercise that develops core stability.",
                "posture_instructions": "Keep the body in a straight line from head to heels.",
                "breathing_instructions": "Breathe steadily throughout the hold.",
                "technique_instructions": "Brace the abdominal muscles and maintain a neutral spine.",
                "common_mistakes": "Dropping the hips or raising them too high.",
                "safety_notes": "Stop if you experience lower-back pain.",
            },

            {
                "name": "Cable Crunch",
                "category": "core",
                "description": "A weighted abdominal exercise using a cable machine.",
                "posture_instructions": "Kneel facing the cable machine with the rope positioned near the head.",
                "breathing_instructions": "Exhale while contracting the abdominal muscles. Inhale while returning.",
                "technique_instructions": "Curl the torso downward using the abdominal muscles rather than pulling with the arms.",
                "common_mistakes": "Using the arms to pull or moving too quickly.",
                "safety_notes": "Use moderate resistance and controlled repetitions.",
            },

            {
                "name": "Treadmill Walk",
                "category": "cardio",
                "description": "A low-impact cardiovascular exercise suitable for warm-up and general fitness.",
                "posture_instructions": "Walk upright with your eyes forward and shoulders relaxed.",
                "breathing_instructions": "Maintain a steady and comfortable breathing rhythm.",
                "technique_instructions": "Walk naturally and gradually increase speed according to fitness level.",
                "common_mistakes": "Holding the rails unnecessarily or increasing speed too quickly.",
                "safety_notes": "Use the emergency stop mechanism when necessary.",
            },

            {
                "name": "Stationary Cycling",
                "category": "cardio",
                "description": "A low-impact cardiovascular exercise using a stationary bicycle.",
                "posture_instructions": "Adjust the seat so the knee remains slightly bent at the bottom of the pedal stroke.",
                "breathing_instructions": "Maintain steady breathing throughout the session.",
                "technique_instructions": "Pedal smoothly at a resistance appropriate for your fitness level.",
                "common_mistakes": "Using excessive resistance or poor seat height.",
                "safety_notes": "Adjust the equipment before starting.",
            },
        ]


        created_exercises = {}

        for data in exercises:

            exercise, created = Exercise.objects.get_or_create(
                name=data["name"],
                defaults={
                    **data,
                    "is_default": True,
                    "is_active": True,
                    "created_by": None,
                },
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created exercise: {exercise.name}"
                    )
                )

            created_exercises[exercise.name] = exercise


        # -----------------------------------------
        # DEFAULT WORKOUT PLANS
        # -----------------------------------------

        plans = [

            {
                "name": "Full Body Beginner",
                "description": "A beginner-friendly full-body workout covering all major muscle groups.",
                "exercises": [
                    ("Barbell Squat", 3, "8-12", 90),
                    ("Barbell Bench Press", 3, "8-12", 90),
                    ("Lat Pulldown", 3, "10-12", 75),
                    ("Dumbbell Shoulder Press", 3, "10-12", 75),
                    ("Dumbbell Biceps Curl", 2, "10-15", 60),
                    ("Cable Triceps Pushdown", 2, "10-15", 60),
                    ("Plank", 3, "30-60 sec", 45),
                ],
            },

            {
                "name": "Push Day",
                "description": "Chest, shoulders and triceps focused workout.",
                "exercises": [
                    ("Barbell Bench Press", 3, "8-12", 90),
                    ("Incline Dumbbell Press", 3, "10-12", 75),
                    ("Cable Chest Fly", 3, "12-15", 60),
                    ("Dumbbell Shoulder Press", 3, "8-12", 90),
                    ("Dumbbell Lateral Raise", 3, "12-15", 60),
                    ("Cable Triceps Pushdown", 3, "10-15", 60),
                ],
            },

            {
                "name": "Pull Day",
                "description": "Back and biceps focused workout.",
                "exercises": [
                    ("Lat Pulldown", 3, "8-12", 90),
                    ("Seated Cable Row", 3, "10-12", 75),
                    ("Dumbbell Row", 3, "10-12", 75),
                    ("Dumbbell Biceps Curl", 3, "10-15", 60),
                ],
            },

            {
                "name": "Leg Day",
                "description": "Lower-body workout focusing on legs and glutes.",
                "exercises": [
                    ("Barbell Squat", 4, "8-12", 120),
                    ("Leg Press", 3, "10-15", 90),
                    ("Romanian Deadlift", 3, "8-12", 90),
                    ("Hip Thrust", 3, "10-15", 75),
                ],
            },

            {
                "name": "Cardio & Core",
                "description": "A simple cardiovascular and core conditioning workout.",
                "exercises": [
                    ("Treadmill Walk", 1, "20-30 min", 30),
                    ("Stationary Cycling", 1, "15-20 min", 30),
                    ("Plank", 3, "30-60 sec", 45),
                    ("Cable Crunch", 3, "12-15", 45),
                ],
            },
        ]


        for plan_data in plans:

            plan, created = WorkoutPlan.objects.get_or_create(
                name=plan_data["name"],
                defaults={
                    "description": plan_data["description"],
                    "is_default": True,
                    "is_active": True,
                    "created_by": None,
                },
            )

            if created:

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created workout plan: {plan.name}"
                    )
                )


            for order, item in enumerate(
                plan_data["exercises"],
                start=1
            ):

                exercise_name, sets, reps, rest = item

                exercise = created_exercises.get(
                    exercise_name
                )

                if not exercise:
                    exercise = Exercise.objects.get(
                        name=exercise_name
                    )

                WorkoutExercise.objects.get_or_create(
                    plan=plan,
                    exercise=exercise,
                    defaults={
                        "order": order,
                        "sets": sets,
                        "reps": reps,
                        "rest_seconds": rest,
                    },
                )


        self.stdout.write(
            self.style.SUCCESS(
                "Default exercises and workout plans are ready."
            )
        )