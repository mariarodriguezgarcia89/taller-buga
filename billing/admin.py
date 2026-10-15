from django.contrib import admin

from .models import CatalogItem, Quote, QuoteLine

TOTAL_FIELDS = ["subtotal", "discount_amount", "taxable_base", "vat_amount", "total"]


@admin.register(CatalogItem)
class CatalogItemAdmin(admin.ModelAdmin):
    list_display = ["code", "description", "category", "unit_price", "is_active"]
    list_filter = ["category", "is_active"]
    search_fields = ["code", "description"]


class QuoteLineInline(admin.TabularInline):
    model = QuoteLine
    extra = 1
    autocomplete_fields = ["catalog_item"]


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ["number", "issue_date", "customer", "vehicle", "status", "total"]
    list_filter = ["status"]
    search_fields = ["number", "customer__last_name", "customer__company_name", "vehicle__plate"]
    autocomplete_fields = ["customer", "vehicle", "insurer"]
    readonly_fields = ["number", *TOTAL_FIELDS]
    inlines = [QuoteLineInline]