import random
from datetime import timedelta
from decimal import Decimal

import factory
from django.utils import timezone

VEHICLES = ["scooter", "bicycle", "car", "foot"]
VEHICLE_WEIGHTS = [40, 25, 20, 15]

ONLINE_RATIO = 0.35

# Bakı ətrafı
LAT_RANGE = (40.35, 40.45)
LON_RANGE = (49.80, 49.95)


def random_coord(lo, hi):
    return Decimal(str(round(random.uniform(lo, hi), 6)))


def random_location_updated_at(is_available):
    now = timezone.now()
    if is_available:
        # online courier: last 1-5 minutes
        return now - timedelta(seconds=random.randint(60, 300))
    # offline courier: 1 hour to 7 days ago
    return now - timedelta(seconds=random.randint(3600, 7 * 24 * 3600))


class CourierProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "couriers.CourierProfile"

    vehicle_type = factory.LazyFunction(lambda: random.choices(VEHICLES, VEHICLE_WEIGHTS)[0])
    is_available = factory.LazyFunction(lambda: random.random() < ONLINE_RATIO)
    latitude = factory.LazyFunction(lambda: random_coord(*LAT_RANGE))
    longitude = factory.LazyFunction(lambda: random_coord(*LON_RANGE))
    location_updated_at = factory.LazyAttribute(lambda o: random_location_updated_at(o.is_available))