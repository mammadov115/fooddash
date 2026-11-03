import argparse
import os
import random
import sys
from collections import defaultdict
from decimal import Decimal
from itertools import accumulate
from pathlib import Path

import django
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import transaction  # noqa: E402
from django.db.models import Count  # noqa: E402

from apps.orders.factories import COURIER_STATUSES, OrderFactory  # noqa: E402
from apps.orders.models import Order, OrderItem  # noqa: E402
from apps.restaurants.models import MenuItem, Restaurant  # noqa: E402
from apps.users.models import User  # noqa: E402

# Sifarişin item sayı və miqdar paylanması
ITEM_COUNTS = [1, 2, 3, 4, 5, 6]
ITEM_COUNT_WEIGHTS = [20, 30, 25, 15, 6, 4]
QUANTITIES = [1, 2, 3]
QUANTITY_WEIGHTS = [70, 22, 8]

# Uneven popularity (lognormal): higher sigma values result in a more unequal distribution.
# customer sigma=1.1 → the most active 20% of customers generate ~60% of orders
# restaurant sigma=1.3 → the most popular 10% of restaurants receive ~50% of orders
CUSTOMER_SIGMA = 1.1
RESTAURANT_SIGMA = 1.3


def disable_auto_timestamps():
    """bulk_create sets fields with auto_now_add/auto_now to the current time, overriding the dates we provide.
        We disable this behavior only for this process to generate historical data."""
    for name in ("created_at", "updated_at"):
        field = Order._meta.get_field(name)
        field.auto_now_add = False
        field.auto_now = False


def weighted_population(ids, sigma):
    weights = [random.lognormvariate(0, sigma) for _ in ids]
    return ids, list(accumulate(weights))


def load_menus():
    """restaurant_id -> [(item_id, name, price), ...] (existing items from active restaurants only)"""
    menus = defaultdict(list)
    qs = MenuItem.objects.filter(is_available=True, category__restaurant__is_active=True).values_list(
        "id", "category__restaurant_id", "name", "price"
    )
    for item_id, restaurant_id, name, price in qs.iterator(chunk_size=20_000):
        menus[restaurant_id].append((item_id, name, price))
    return menus


def seed_batch(n, customers, restaurants, menus, fees, courier_ids):
    customer_ids, customer_cum = customers
    restaurant_ids, restaurant_cum = restaurants

    picked_customers = random.choices(customer_ids, cum_weights=customer_cum, k=n)
    picked_restaurants = random.choices(restaurant_ids, cum_weights=restaurant_cum, k=n)

    orders, all_lines = [], []
    for customer_id, restaurant_id in zip(picked_customers, picked_restaurants):
        order = OrderFactory.build(
            customer_id=customer_id,
            restaurant_id=restaurant_id,
            delivery_fee=fees[restaurant_id],
        )
        if order.status in COURIER_STATUSES:
            order.courier_id = random.choice(courier_ids)

        menu = menus[restaurant_id]
        count = min(random.choices(ITEM_COUNTS, ITEM_COUNT_WEIGHTS)[0], len(menu))

        lines, subtotal = [], Decimal("0")
        for item_id, name, price in random.sample(menu, count):
            quantity = random.choices(QUANTITIES, QUANTITY_WEIGHTS)[0]
            lines.append((item_id, name, price, quantity))
            subtotal += price * quantity

        order.subtotal = subtotal
        order.total = subtotal + order.delivery_fee
        orders.append(order)
        all_lines.append(lines)

    Order.objects.bulk_create(orders)  # PostgreSQL returns primary keys.
    items = [
        OrderItem(order_id=order.id, menu_item_id=item_id, name=name, unit_price=price, quantity=quantity)
        for order, lines in zip(orders, all_lines)
        for item_id, name, price, quantity in lines
    ]
    OrderItem.objects.bulk_create(items, batch_size=10_000)
    return len(items)


def main():
    parser = argparse.ArgumentParser(description="Seed orders and order items.")
    parser.add_argument("--count", type=int, default=500_000, help="number of orders")
    parser.add_argument("--batch-size", type=int, default=5_000, help="orders per batch")
    args = parser.parse_args()

    customer_ids = list(User.objects.filter(role="customer").values_list("id", flat=True))
    courier_ids = list(User.objects.filter(role="courier").values_list("id", flat=True))
    if not customer_ids or not courier_ids:
        sys.exit("Customers or couriers not found. Run seed_users.py first.")

    print("Loading menus into memory...")
    menus = load_menus()
    fees = dict(Restaurant.objects.filter(id__in=menus.keys()).values_list("id", "delivery_fee"))
    restaurant_ids = [rid for rid in fees if menus[rid]]
    if not restaurant_ids:
        sys.exit("No active restaurants with available menu items. Run seed_restaurants.py first.")

    customers = weighted_population(customer_ids, CUSTOMER_SIGMA)
    restaurants = weighted_population(restaurant_ids, RESTAURANT_SIGMA)

    disable_auto_timestamps()

    total_items = 0
    with tqdm(total=args.count, desc="Creating orders", unit="order") as bar:
        remaining = args.count
        while remaining > 0:
            size = min(args.batch_size, remaining)
            with transaction.atomic():
                total_items += seed_batch(size, customers, restaurants, menus, fees, courier_ids)
            remaining -= size
            bar.update(size)
            bar.set_postfix(items=total_items)

    print(f"Done. Orders: {Order.objects.count()}, order items: {OrderItem.objects.count()}")
    print("By status:")
    for row in Order.objects.values("status").annotate(n=Count("id")).order_by("-n"):
        print(f"  {row['status']:<10} {row['n']}")


if __name__ == "__main__":
    main()