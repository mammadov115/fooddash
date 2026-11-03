from django.contrib import admin

from .models import CourierProfile


@admin.register(CourierProfile)
class CourierProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "vehicle_type", "is_available", "location_updated_at")
    list_filter = ("vehicle_type", "is_available")
    search_fields = ("user__username",)