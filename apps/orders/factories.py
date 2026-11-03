import random
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import factory
from django.utils import timezone
from faker import Faker

fake = Faker()

BAKU = ZoneInfo("Asia/Baku")

# Baku region
LAT_RANGE = (40.35, 40.45)
LON_RANGE = (49.80, 49.95)

HISTORY_DAYS = 90

# Status distribution (total: 100): delivered 88, cancelled 5, rejected 3.
STATUSES = ["delivered", "cancelled", "rejected", "placed", "accepted", "preparing", "ready", "picked_up"]
STATUS_WEIGHTS = [88, 5, 3, 1, 1, 1, 0.5, 0.5]

# active orders are new: status → how many minutes ago they were created (min, max)
ACTIVE_AGE_MINUTES = {
    "placed": (1, 5),
    "accepted": (4, 12),
    "preparing": (8, 25),
    "ready": (15, 35),
    "picked_up": (20, 50),
}

# A courier is assigned only for orders with these statuses.
COURIER_STATUSES = {"picked_up", "delivered"}

# Order volume by hour (00:00–23:00), with peak periods at lunchtime (12:00–14:00) and in the evening (19:00–22:00).
HOUR_WEIGHTS = [1, 0.5, 0.3, 0.2, 0.2, 0.3, 0.8, 2, 3, 3, 4, 7, 12, 12, 7, 4, 4, 5, 8, 11, 12, 10, 6, 3]

NOTES = [
    "No onions please",
    "Ring the bell",
    "Leave at the door",
    "Call when you arrive",
    "Extra napkins",
    "Less spicy",
    "Please do not ring, baby sleeping",
]

# Faker is slow: 5,000 addresses are pre-generated, and orders select from them.
ADDRESS_POOL = [fake.street_address() for _ in range(5_000)]


def random_coord(lo, hi):
    return Decimal(str(round(random.uniform(lo, hi), 6)))


def random_status():
    return random.choices(STATUSES, STATUS_WEIGHTS)[0]


def random_created_at(status):
    now = timezone.now()

    if status in ACTIVE_AGE_MINUTES:
        lo, hi = ACTIVE_AGE_MINUTES[status]
        return now - timedelta(minutes=random.randint(lo, hi), seconds=random.randint(0, 59))

    # History: last 90 days, biased toward peak hours (Baku time).
    day = (now.astimezone(BAKU) - timedelta(days=random.randint(0, HISTORY_DAYS - 1))).date()
    hour = random.choices(range(24), HOUR_WEIGHTS)[0]
    created = datetime.combine(
        day, time(hour, random.randint(0, 59), random.randint(0, 59)), tzinfo=BAKU
    )
    # Completed orders must not fall within the last 2 hours.
    while created > now - timedelta(hours=2):
        created -= timedelta(days=1)
    return created


def random_updated_at(status, created_at):
    if status == "delivered":
        delta = timedelta(minutes=random.randint(25, 70))
    elif status == "cancelled":
        delta = timedelta(minutes=random.randint(2, 20))
    elif status == "rejected":
        delta = timedelta(minutes=random.randint(1, 5))
    else:
        delta = timedelta(minutes=random.randint(0, 3))
    return min(created_at + delta, timezone.now())


def random_note():
    return random.choice(NOTES) if random.random() < 0.15 else ""


class OrderFactory(factory.django.DjangoModelFactory):
    """customer_id, restaurant_id və delivery_fee seed scriptindən ötürülür.
    courier_id, subtotal və total isə item-lər seçiləndən sonra scriptdə təyin olunur."""

    class Meta:
        model = "orders.Order"

    status = factory.LazyFunction(random_status)
    created_at = factory.LazyAttribute(lambda o: random_created_at(o.status))
    updated_at = factory.LazyAttribute(lambda o: random_updated_at(o.status, o.created_at))
    delivery_address = factory.LazyFunction(lambda: random.choice(ADDRESS_POOL))
    delivery_latitude = factory.LazyFunction(lambda: random_coord(*LAT_RANGE))
    delivery_longitude = factory.LazyFunction(lambda: random_coord(*LON_RANGE))
    note = factory.LazyFunction(random_note)