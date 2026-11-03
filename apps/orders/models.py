from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.restaurants.models import MenuItem, Restaurant


class Order(models.Model):
    class Status(models.TextChoices):
        PLACED = "placed", "Placed"
        ACCEPTED = "accepted", "Accepted"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready for pickup"
        PICKED_UP = "picked_up", "Picked up"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        REJECTED = "rejected", "Rejected"

    # Define valid status transitions for the order lifecycle
    TRANSITIONS = {
        Status.PLACED: {Status.ACCEPTED, Status.REJECTED, Status.CANCELLED},
        Status.ACCEPTED: {Status.PREPARING, Status.CANCELLED},
        Status.PREPARING: {Status.READY, Status.CANCELLED},
        Status.READY: {Status.PICKED_UP},
        Status.PICKED_UP: {Status.DELIVERED},
        Status.DELIVERED: set(),
        Status.CANCELLED: set(),
        Status.REJECTED: set(),
    }

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.PROTECT, related_name="orders"
    )
    courier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries",
        limit_choices_to={"role": "courier"},
    )

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PLACED, db_index=True
    )

    # delivery address (snapshot at the time of order placement)
    delivery_address = models.CharField(max_length=255)
    delivery_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    delivery_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    note = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"

    def can_transition_to(self, new_status):
        return new_status in self.TRANSITIONS[self.status]

    def transition_to(self, new_status):
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot change status from {self.status} to {new_status}")
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])

    def recalculate_totals(self):
        self.subtotal = sum(
            (item.line_total for item in self.items.all()), Decimal("0")
        )
        self.total = self.subtotal + self.delivery_fee
        self.save(update_fields=["subtotal", "total", "updated_at"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(
        MenuItem, on_delete=models.SET_NULL, null=True, related_name="order_items"
    )
    # if the menu item is deleted, we keep the name and price at the time of order
    name = models.CharField(max_length=150)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.name}"