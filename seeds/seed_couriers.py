import argparse
import os
import sys
from pathlib import Path

import django
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.couriers.factories import CourierProfileFactory  # noqa: E402
from apps.couriers.models import CourierProfile  # noqa: E402
from apps.users.models import User  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Seed courier profiles for users with the courier role.")
    parser.add_argument("--batch-size", type=int, default=2_000)
    args = parser.parse_args()

    # (safe to re-run) only courier users without a profile
    user_ids = list(
        User.objects.filter(role="courier", courier_profile__isnull=True).values_list("id", flat=True)
    )
    if not user_ids:
        sys.exit("No courier users without a profile found. Run seed_users.py first (or all profiles already exist).")

    with tqdm(total=len(user_ids), desc="Creating courier profiles", unit="courier") as bar:
        for start in range(0, len(user_ids), args.batch_size):
            chunk = user_ids[start:start + args.batch_size]
            profiles = [CourierProfileFactory.build(user_id=uid) for uid in chunk]
            CourierProfile.objects.bulk_create(profiles)
            bar.update(len(chunk))

    total = CourierProfile.objects.count()
    online = CourierProfile.objects.filter(is_available=True).count()
    print(f"Done. Courier profiles: {total} (online: {online})")


if __name__ == "__main__":
    main()