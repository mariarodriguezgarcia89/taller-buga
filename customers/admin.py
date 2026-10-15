from django.contrib import admin

from .models import Customer, Insurer, Vehicle


class VehicleInline(admin.TabularInline):
    """Edit a customer's vehicles from the customer page."""

    model = Vehicle
    extra = 0


@admin.register(Insurer)
class InsurerAdmin(admin.ModelAdmin):
    list_display = ["name", "discount_percent", "phone", "email"]
    search_fields = ["name"]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["display_name", "customer_type", "phone", "email", "insurer"]
    list_filter = ["customer_type", "insurer"]
    search_fields = ["first_name", "last_name", "company_name", "tax_id", "phone", "email"]
    inlines = [VehicleInline]


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["plate", "make", "model", "customer"]
    search_fields = ["plate", "make", "model", "customer__last_name", "customer__company_name"]
    autocomplete_fields = ["customer"]