from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from core.models import TimeStampedModel
from customers.models import Customer, Insurer, Vehicle

CENT = Decimal("0.01")
PERCENT_VALIDATORS = [MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))]


def round_money(value):
    """Round to cents like invoices do (0.005 -> 0.01), not banker's rounding."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


class CatalogItem(TimeStampedModel):
    """Priced service or part that can be added to a quote."""

    class Category(models.TextChoices):
        LABOUR = "labour", "Mano de obra"
        PART = "part", "Recambio"

    code = models.CharField("código", max_length=30, unique=True)
    description = models.CharField("descripción", max_length=255)
    category = models.CharField(
        "categoría", max_length=20, choices=Category.choices, default=Category.PART
    )
    unit_price = models.DecimalField(
        "precio unitario",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    is_active = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "elemento del catálogo"
        verbose_name_plural = "catálogo"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} · {self.description}"


class BillingDocument(TimeStampedModel):
    """Shared fields, numbering and totals for quotes and invoices."""

    NUMBER_PREFIX = ""

    number = models.CharField("número", max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(
        Customer, verbose_name="cliente", on_delete=models.PROTECT, related_name="%(class)ss"
    )
    vehicle = models.ForeignKey(
        Vehicle, verbose_name="vehículo", on_delete=models.PROTECT, related_name="%(class)ss"
    )
    insurer = models.ForeignKey(
        Insurer,
        verbose_name="aseguradora",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)ss",
    )
    issue_date = models.DateField("fecha", default=timezone.localdate)
    discount_percent = models.DecimalField(
        "descuento (%)",
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=PERCENT_VALIDATORS,
    )
    vat_rate = models.DecimalField(
        "IVA (%)",
        max_digits=5,
        decimal_places=2,
        default=Decimal("21.00"),
        validators=PERCENT_VALIDATORS,
    )
    notes = models.TextField("observaciones", blank=True)

    class Meta:
        abstract = True
        ordering = ["-issue_date", "-number"]

    def __str__(self):
        return self.number

    def clean(self):
        super().clean()
        if self.customer_id and self.vehicle_id and self.vehicle.customer_id != self.customer_id:
            raise ValidationError(
                {"vehicle": "Este vehículo no pertenece al cliente seleccionado."}
            )

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._next_number()
        super().save(*args, **kwargs)

    def _next_number(self):
        """Yearly correlative number, e.g. P-2026-0001."""
        prefix = f"{self.NUMBER_PREFIX}-{self.issue_date.year}-"
        last = type(self).objects.filter(number__startswith=prefix).order_by("-number").first()
        sequence = int(last.number.removeprefix(prefix)) + 1 if last else 1
        return f"{prefix}{sequence:04d}"

    @property
    def subtotal(self):
        return round_money(sum((line.amount for line in self.lines.all()), Decimal("0")))

    @property
    def discount_amount(self):
        return round_money(self.subtotal * self.discount_percent / 100)

    @property
    def taxable_base(self):
        return self.subtotal - self.discount_amount

    @property
    def vat_amount(self):
        return round_money(self.taxable_base * self.vat_rate / 100)

    @property
    def total(self):
        return self.taxable_base + self.vat_amount


class DocumentLine(TimeStampedModel):
    """Shared fields for quote and invoice lines."""

    description = models.CharField("descripción", max_length=255)
    quantity = models.DecimalField(
        "cantidad",
        max_digits=8,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit_price = models.DecimalField(
        "precio unitario",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        abstract = True
        ordering = ["id"]

    def __str__(self):
        return self.description

    @property
    def amount(self):
        return round_money(self.quantity * self.unit_price)

class Quote(BillingDocument):
    NUMBER_PREFIX = "P"

    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"
        SENT = "sent", "Enviado"
        ACCEPTED = "accepted", "Aceptado"
        REJECTED = "rejected", "Rechazado"

    status = models.CharField(
        "estado", max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    valid_until = models.DateField("válido hasta", null=True, blank=True)

    class Meta(BillingDocument.Meta):
        verbose_name = "presupuesto"
        verbose_name_plural = "presupuestos"

    @transaction.atomic
    def create_invoice(self):
        """Create an invoice copying this quote's data and lines."""
        if self.status != self.Status.ACCEPTED:
            raise ValidationError("Solo se pueden facturar presupuestos aceptados.")
        if hasattr(self, "invoice"):
            raise ValidationError("Este presupuesto ya tiene una factura.")

        invoice = Invoice.objects.create(
            quote=self,
            customer=self.customer,
            vehicle=self.vehicle,
            insurer=self.insurer,
            discount_percent=self.discount_percent,
            vat_rate=self.vat_rate,
        )
        InvoiceLine.objects.bulk_create(
            InvoiceLine(
                invoice=invoice,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
            )
            for line in self.lines.all()
        )
        return invoice
        
class QuoteLine(DocumentLine):
    quote = models.ForeignKey(
        Quote, verbose_name="presupuesto", on_delete=models.CASCADE, related_name="lines"
    )
    catalog_item = models.ForeignKey(
        CatalogItem,
        verbose_name="elemento del catálogo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quote_lines",
    )

    class Meta(DocumentLine.Meta):
        verbose_name = "línea de presupuesto"
        verbose_name_plural = "líneas de presupuesto"


class Invoice(BillingDocument):
    NUMBER_PREFIX = "F"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente de cobro"
        PAID = "paid", "Cobrada"
        CANCELLED = "cancelled", "Anulada"

    quote = models.OneToOneField(
        Quote,
        verbose_name="presupuesto",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="invoice",
    )
    status = models.CharField(
        "estado", max_length=20, choices=Status.choices, default=Status.PENDING
    )
    due_date = models.DateField("vencimiento", null=True, blank=True)
    paid_date = models.DateField("fecha de cobro", null=True, blank=True)

    class Meta(BillingDocument.Meta):
        verbose_name = "factura"
        verbose_name_plural = "facturas"


class InvoiceLine(DocumentLine):
    invoice = models.ForeignKey(
        Invoice, verbose_name="factura", on_delete=models.CASCADE, related_name="lines"
    )

    class Meta(DocumentLine.Meta):
        verbose_name = "línea de factura"
        verbose_name_plural = "líneas de factura"
