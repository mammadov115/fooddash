from django.contrib import admin

from .models import Cuisine, MenuCategory, MenuItem, OpeningHours, Restaurant


class OpeningHoursInline(admin.TabularInline):
    model = OpeningHours
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "is_active", "delivery_fee")
    list_filter = ("is_active", "cuisines")
    search_fields = ("name", "address")
    inlines = [OpeningHoursInline]


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 0


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "position")
    inlines = [MenuItemInline]


admin.site.register(Cuisine)