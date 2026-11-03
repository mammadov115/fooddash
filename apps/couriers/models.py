from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class CourierProfile(models.Model):
    class VehicleType(models.TextChoices):
        FOOT = "foot", "On foot"
        BICYCLE = "bicycle", "Bicycle"
        SCOOTER = "scooter", "Scooter"
        CAR = "car", "Car"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courier_profile",
        limit_choices_to={"role": "courier"},
    )
    vehicle_type = models.CharField(
        max_length=20, choices=VehicleType.choices, default=VehicleType.SCOOTER
    )

    # courier is available for new orders
    is_available = models.BooleanField(default=False, db_index=True)

    # last known location
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_updated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.user_id and self.user.role != "courier":
            raise ValidationError("User must have the courier role.")

    def __str__(self):
        return f"Courier: {self.user}"