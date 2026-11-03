import argparse
import os
import sys
from pathlib import Path

import django
from tqdm import tqdm


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.users.factories import UserFactory  # noqa: E402
from apps.users.models import User  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Seed the database with fake users.")
    parser.add_argument("--count", type=int, default=100_000)
    parser.add_argument("--batch-size", type=int, default=2_000)
    args = parser.parse_args()

    remaining = args.count
    with tqdm(total=args.count, desc="Creating users", unit="user") as bar:
        while remaining > 0:
            size = min(args.batch_size, remaining)
            users = UserFactory.build_batch(size)  
            User.objects.bulk_create(users, batch_size=size)
            remaining -= size
            bar.update(size)

    print(f"Done. Total users in DB: {User.objects.count()}")


if __name__ == "__main__":
    main()