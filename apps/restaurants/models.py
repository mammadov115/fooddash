import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from pathlib import Path


def restaurant_image_path(instance, filename):
    ext = Path(filename).suffix.lower()
    return f"restaurants/{instance.slug or 'new'}/{uuid.uuid4().hex}{ext}"


def menu_item_image_path(instance, filename):
    ext = Path(filename).suffix.lower()
    return f"menu_items/{uuid.uuid4().hex}{ext}"


class Cuisine(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Restaurant(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="restaurants",
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    cuisines = models.ManyToManyField(Cuisine, related_name="restaurants", blank=True)

    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    logo = models.ImageField(upload_to=restaurant_image_path, blank=True)
    cover_image = models.ImageField(upload_to=restaurant_image_path, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    min_order_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)  # admin/owner tərəfindən söndürülə bilər
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug, i = base, 1
            while Restaurant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class OpeningHours(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="opening_hours"
    )
    weekday = models.IntegerField(choices=Weekday.choices)
    open_time = models.TimeField()
    close_time = models.TimeField()

    class Meta:
        ordering = ["weekday", "open_time"]
        verbose_name_plural = "Opening hours"

    def __str__(self):
        return f"{self.restaurant} - {self.get_weekday_display()} {self.open_time}-{self.close_time}"


class MenuCategory(models.Model):
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="menu_categories"
    )
    name = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]
        verbose_name_plural = "Menu categories"

    def __str__(self):
        return f"{self.restaurant} / {self.name}"


class MenuItem(models.Model):
    category = models.ForeignKey(
        MenuCategory, on_delete=models.CASCADE, related_name="items"
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to=menu_item_image_path, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name