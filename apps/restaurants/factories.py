import random
import uuid
from datetime import time
from decimal import Decimal

import factory
from django.utils.text import slugify
from faker import Faker

fake = Faker()

CUISINES = [
    "Pizza", "Burger", "Sushi", "Kebab", "Dolma", "Plov", "Pasta", "Steak",
    "Seafood", "Chicken", "Salad", "Soup", "Dessert", "Bakery", "Coffee",
    "Breakfast", "Georgian", "Turkish", "Italian", "Chinese", "Japanese",
    "Indian", "Mexican", "Vegan", "Healthy", "Fast Food", "Grill", "Sandwich",
    "Azerbaijani", "Street Food",
]

RESTAURANT_SUFFIXES = ["Restaurant", "Kitchen", "Grill", "Bistro", "House", "Cafe", "Corner", "Express"]

MENU_CATEGORIES = [
    "Starters", "Soups", "Salads", "Main Course", "Grill", "Pizza", "Pasta",
    "Burgers", "Sides", "Desserts", "Drinks", "Breakfast", "Specials",
]

DISHES = [
    "Chicken Kebab", "Lamb Kebab", "Beef Burger", "Cheese Burger", "Margherita",
    "Pepperoni Pizza", "Caesar Salad", "Greek Salad", "Plov", "Dolma", "Lule Kebab",
    "Dushbara", "Gutab", "Spaghetti Carbonara", "Penne Arrabbiata", "Grilled Salmon",
    "Ribeye Steak", "Chicken Wings", "French Fries", "Tomato Soup", "Lentil Soup",
    "Tiramisu", "Cheesecake", "Baklava", "Lemonade", "Iced Tea", "Americano",
    "Cappuccino", "Club Sandwich", "Shawarma", "Falafel Wrap", "Fish & Chips",
]

DISH_ADJECTIVES = ["", "", "Spicy ", "Classic ", "House ", "Crispy ", "Grilled ", "Family "]

# Baku coordinates for generating random restaurant locations
LAT_RANGE = (40.35, 40.45)
LON_RANGE = (49.80, 49.95)


def random_coord(lo, hi):
    return Decimal(str(round(random.uniform(lo, hi), 6)))


def random_phone():
    prefix = random.choice(["12", "50", "51", "55", "70", "77", "99"])
    return f"+994{prefix}{random.randint(1000000, 9999999)}"


def restaurant_name():
    return f"{fake.last_name()} {random.choice(RESTAURANT_SUFFIXES)}"


SEED_IMAGE_COUNT = 15  # generate_seed_images.py ilə eyni say


def seed_image(folder, prefix):
    """media/ qovluğuna nisbətən yol qaytarır, məsələn 'seed/logos/logo_07.jpg'."""
    return f"seed/{folder}/{prefix}_{random.randint(1, SEED_IMAGE_COUNT):02d}.jpg"


class RestaurantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "restaurants.Restaurant"

    name = factory.LazyFunction(restaurant_name)
    # bulk_create not call save() so we generate a unique slug here
    slug = factory.LazyAttribute(lambda o: f"{slugify(o.name)}-{uuid.uuid4().hex[:8]}")
    description = factory.LazyFunction(lambda: fake.sentence(nb_words=12))
    address = factory.LazyFunction(fake.street_address)
    latitude = factory.LazyFunction(lambda: random_coord(*LAT_RANGE))
    longitude = factory.LazyFunction(lambda: random_coord(*LON_RANGE))
    phone = factory.LazyFunction(random_phone)
    delivery_fee = factory.LazyFunction(lambda: Decimal(random.choice([0, 1, 1.5, 2, 2.5, 3])))
    min_order_amount = factory.LazyFunction(lambda: Decimal(random.choice([0, 5, 8, 10, 15])))
    is_active = factory.LazyFunction(lambda: random.random() < 0.95)
    logo = factory.LazyFunction(lambda: seed_image("logos", "logo"))
    cover_image = factory.LazyFunction(lambda: seed_image("covers", "cover"))


class OpeningHoursFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "restaurants.OpeningHours"

    open_time = factory.LazyFunction(lambda: time(random.choice([8, 9, 10, 11]), 0))
    close_time = factory.LazyFunction(lambda: time(random.choice([21, 22, 23]), 0))


class MenuCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "restaurants.MenuCategory"


class MenuItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "restaurants.MenuItem"

    name = factory.LazyFunction(lambda: f"{random.choice(DISH_ADJECTIVES)}{random.choice(DISHES)}".strip())
    description = factory.LazyFunction(lambda: fake.sentence(nb_words=10))
    price = factory.LazyFunction(lambda: Decimal(random.randrange(300, 3500)) / 100)
    is_available = factory.LazyFunction(lambda: random.random() < 0.92)
    image = factory.LazyFunction(lambda: seed_image("items", "item"))