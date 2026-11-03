import argparse
import colorsys
import os
import random
import sys
from pathlib import Path

import django
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings  # noqa: E402
from django.db import transaction  # noqa: E402

from apps.restaurants.factories import (  # noqa: E402
    CUISINES,
    MENU_CATEGORIES,
    SEED_IMAGE_COUNT,
    MenuCategoryFactory,
    MenuItemFactory,
    OpeningHoursFactory,
    RestaurantFactory,
)
from apps.restaurants.models import (  # noqa: E402
    Cuisine,
    MenuCategory,
    MenuItem,
    OpeningHours,
    Restaurant,
)
from apps.users.models import User  # noqa: E402

# ---------------------------------------------------------------------------
# Image generation (Pillow)
# ---------------------------------------------------------------------------

SEED_IMAGES_DIR = Path(settings.MEDIA_ROOT) / "seed"

# (label, base color) — SEED_IMAGE_COUNT (15) should be the same as len(IMAGE_VARIANTS)
IMAGE_VARIANTS = [
    ("Pizza", "#E4572E"),
    ("Burger", "#F3A712"),
    ("Sushi", "#EF476F"),
    ("Kebab", "#B5651D"),
    ("Salad", "#52B788"),
    ("Pasta", "#F4D35E"),
    ("Steak", "#8D2F2F"),
    ("Soup", "#E76F51"),
    ("Dessert", "#C77DFF"),
    ("Coffee", "#6F4E37"),
    ("Grill", "#D1495B"),
    ("Seafood", "#3A86FF"),
    ("Plov", "#E9B44C"),
    ("Bakery", "#DDA15E"),
    ("Wrap", "#2A9D8F"),
]

# (folder, prefix, size)
IMAGE_KINDS = [
    ("logos", "logo", (400, 400)),
    ("covers", "cover", (1200, 600)),
    ("items", "item", (600, 400)),
]


def _hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def _shade(rgb, factor):
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    l = max(0, min(1, l * factor))
    return tuple(int(c * 255) for c in colorsys.hls_to_rgb(h, l, s))


def _make_image(size, base_rgb, label):
    width, height = size
    top, bottom = _shade(base_rgb, 1.15), _shade(base_rgb, 0.7)

    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(height - 1, 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)

    font = ImageFont.load_default(size=max(24, min(width, height) // 6))
    bbox = draw.textbbox((0, 0), label, font=font)
    x = (width - (bbox[2] - bbox[0])) / 2 - bbox[0]
    y = (height - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((x, y), label, font=font, fill="white")
    return img


def ensure_seed_images(force=False):
    """Images don't exist (or force=True) then create them under media/seed/."""
    assert len(IMAGE_VARIANTS) == SEED_IMAGE_COUNT, "IMAGE_VARIANTS count doesn't match SEED_IMAGE_COUNT"

    jobs = []
    for folder, prefix, size in IMAGE_KINDS:
        target = SEED_IMAGES_DIR / folder
        target.mkdir(parents=True, exist_ok=True)
        for i, (label, color) in enumerate(IMAGE_VARIANTS, start=1):
            path = target / f"{prefix}_{i:02d}.jpg"
            if force or not path.exists():
                jobs.append((path, size, color, label))

    if not jobs:
        print(f"Seed images already exist in {SEED_IMAGES_DIR}, skipping.")
        return

    for path, size, color, label in tqdm(jobs, desc="Generating images", unit="img"):
        _make_image(size, _hex_to_rgb(color), label).save(path, quality=85)


# ---------------------------------------------------------------------------
# Restoran seed-i
# ---------------------------------------------------------------------------


def seed_cuisines():
    cuisines = [Cuisine.objects.get_or_create(name=name)[0] for name in CUISINES]
    return [c.id for c in cuisines]


def seed_batch(owner_ids, cuisine_ids):
    """Bir batch: restoranlar + iş saatları + cuisine əlaqələri + menu kateqoriyaları + item-lər."""
    restaurants = [RestaurantFactory.build(owner_id=oid) for oid in owner_ids]
    Restaurant.objects.bulk_create(restaurants)  #Returns postgreSQL pks

    hours, through_rows, categories = [], [], []
    through = Restaurant.cuisines.through

    for r in restaurants:
        for weekday in range(7):
            hours.append(OpeningHoursFactory.build(restaurant_id=r.id, weekday=weekday))

        for cid in random.sample(cuisine_ids, k=random.randint(1, 3)):
            through_rows.append(through(restaurant_id=r.id, cuisine_id=cid))

        names = random.sample(MENU_CATEGORIES, k=random.randint(4, 8))
        for position, name in enumerate(names):
            categories.append(MenuCategoryFactory.build(restaurant_id=r.id, name=name, position=position))

    OpeningHours.objects.bulk_create(hours)
    through.objects.bulk_create(through_rows)
    MenuCategory.objects.bulk_create(categories)

    items = []
    for c in categories:
        for _ in range(random.randint(6, 12)):
            items.append(MenuItemFactory.build(category_id=c.id))
    MenuItem.objects.bulk_create(items, batch_size=5000)

    return len(items)


def main():
    parser = argparse.ArgumentParser(description="Seed restaurants, menus, opening hours and images.")
    parser.add_argument("--count", type=int, default=5_000, help="number of restaurants")
    parser.add_argument("--batch-size", type=int, default=250, help="restaurants per batch")
    parser.add_argument("--regenerate-images", action="store_true", help="re-create seed images even if they exist")
    args = parser.parse_args()

    owner_ids = list(User.objects.filter(role="restaurant_owner").values_list("id", flat=True))
    if not owner_ids:
        sys.exit("No restaurant_owner users found. Run seed_users.py first.")

    ensure_seed_images(force=args.regenerate_images)
    cuisine_ids = seed_cuisines()

    #  each owner gets 1 restaurant first, remaining are randomly assigned
    if args.count <= len(owner_ids):
        assigned = random.sample(owner_ids, k=args.count)
    else:
        assigned = owner_ids + random.choices(owner_ids, k=args.count - len(owner_ids))
        random.shuffle(assigned)

    total_items = 0
    with tqdm(total=args.count, desc="Creating restaurants", unit="rest") as bar:
        for start in range(0, args.count, args.batch_size):
            chunk = assigned[start:start + args.batch_size]
            with transaction.atomic():
                total_items += seed_batch(chunk, cuisine_ids)
            bar.update(len(chunk))
            bar.set_postfix(items=total_items)

    print(
        f"Done. Restaurants: {Restaurant.objects.count()}, "
        f"categories: {MenuCategory.objects.count()}, "
        f"items: {MenuItem.objects.count()}"
    )


if __name__ == "__main__":
    main()