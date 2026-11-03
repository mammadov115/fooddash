from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "restaurant", "courier", "status", "total", "created_at")
    list_filter = ("status", "restaurant")
    search_fields = ("id", "customer__username", "restaurant__name")
    inlines = [OrderItemInline]