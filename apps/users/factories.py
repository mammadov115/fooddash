import random
import uuid

import factory
from django.contrib.auth.hashers import make_password
from faker import Faker

fake = Faker()

ROLES = ["customer", "courier", "restaurant_owner"]
ROLE_WEIGHTS = [85, 10, 5]

# PBKDF2 hash-i yavaşdır (100k user = saatlarla). Bir dəfə hash edib hamısına veririk.
DEFAULT_PASSWORD_HASH = make_password("password123")


def random_phone():
    prefix = random.choice(["50", "51", "55", "70", "77", "99"])
    return f"+994{prefix}{random.randint(1000000, 9999999)}"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "users.User"

    # uuid sayəsində komandanı təkrar işlətsən də username toqquşmur
    username = factory.LazyFunction(lambda: f"user_{uuid.uuid4().hex[:12]}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    first_name = factory.LazyFunction(fake.first_name)
    last_name = factory.LazyFunction(fake.last_name)
    password = DEFAULT_PASSWORD_HASH
    role = factory.LazyFunction(lambda: random.choices(ROLES, ROLE_WEIGHTS)[0])
    phone = factory.LazyFunction(random_phone)