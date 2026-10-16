from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import CatalogItem, Invoice, InvoiceLine, Quote, QuoteLine


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

    actions = ["create_invoices"]

    @admin.action(description="Crear factura de los presupuestos seleccionados")
    def create_invoices(self, request, queryset):
        for quote in queryset:
            try:
                invoice = quote.create_invoice()
            except ValidationError as error:
                self.message_user(request, f"{quote}: {error.messages[0]}", messages.ERROR)
            else:
                self.message_user(request, f"{quote} → factura {invoice} creada.", messages.SUCCESS)
            
class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["number", "issue_date", "customer", "vehicle", "status", "total"]
    list_filter = ["status"]
    search_fields = ["number", "customer__last_name", "customer__company_name", "vehicle__plate"]
    autocomplete_fields = ["customer", "vehicle", "insurer"]
    readonly_fields = ["number", "quote", *TOTAL_FIELDS]
    inlines = [InvoiceLineInline]
