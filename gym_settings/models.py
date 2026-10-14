from django.db import models


class GymSettings(models.Model):
    gym_name = models.CharField(
        max_length=150,
        default="My Gym",
    )

    tagline = models.CharField(
        max_length=200,
        blank=True,
    )

    logo = models.ImageField(
        upload_to="gym/logo/",
        blank=True,
        null=True,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    website = models.URLField(
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    state = models.CharField(
        max_length=100,
        blank=True,
    )

    country = models.CharField(
        max_length=100,
        default="India",
    )

    pincode = models.CharField(
        max_length=10,
        blank=True,
    )

    receipt_footer = models.TextField(
        blank=True,
        default="Thank you for choosing us.",
    )

    currency_symbol = models.CharField(
        max_length=5,
        default="₹",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Gym Settings"
        verbose_name_plural = "Gym Settings"

    def __str__(self):
        return self.gym_name

    @classmethod
    def get_settings(cls):
        settings = cls.objects.first()

        if not settings:
            settings = cls.objects.create()

        return settings