# Create your models here.
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import TimeStampedModel


def normalize_plate(plate):
    """Store plates as uppercase without spaces or hyphens: '1234-abc' -> '1234ABC'."""
    return plate.upper().replace(" ", "").replace("-", "")


class Insurer(TimeStampedModel):
    """Insurance company that may cover repairs with a discount."""

    name = models.CharField("nombre", max_length=150, unique=True)
    phone = models.CharField("teléfono", max_length=20, blank=True)
    email = models.EmailField("email", blank=True)
    discount_percent = models.DecimalField(
        "descuento (%)",
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    notes = models.TextField("notas internas", blank=True)

    class Meta:
        verbose_name = "aseguradora"
        verbose_name_plural = "aseguradoras"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Customer(TimeStampedModel):
    """Workshop customer: an individual or a company."""

    class CustomerType(models.TextChoices):
        INDIVIDUAL = "individual", "Particular"
        COMPANY = "company", "Empresa"

    customer_type = models.CharField(
        "tipo de cliente",
        max_length=20,
        choices=CustomerType.choices,
        default=CustomerType.INDIVIDUAL,
    )
    first_name = models.CharField("nombre", max_length=100, blank=True)
    last_name = models.CharField("apellidos", max_length=150, blank=True)
    company_name = models.CharField("razón social", max_length=150, blank=True)
    tax_id = models.CharField("NIF/CIF", max_length=15, blank=True)
    phone = models.CharField("teléfono", max_length=20, blank=True)
    email = models.EmailField("email", blank=True)
    address = models.CharField("dirección", max_length=255, blank=True)
    postal_code = models.CharField("código postal", max_length=10, blank=True)
    city = models.CharField("localidad", max_length=100, blank=True)
    insurer = models.ForeignKey(
        Insurer,
        verbose_name="aseguradora",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customers",
    )

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["company_name", "last_name", "first_name"]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        if self.customer_type == self.CustomerType.COMPANY:
            return self.company_name
        return f"{self.first_name} {self.last_name}".strip()

    def clean(self):
        super().clean()
        errors = {}
        if self.customer_type == self.CustomerType.COMPANY and not self.company_name:
            errors["company_name"] = "La razón social es obligatoria para empresas."
        if self.customer_type == self.CustomerType.INDIVIDUAL:
            if not self.first_name:
                errors["first_name"] = "El nombre es obligatorio."
            if not self.last_name:
                errors["last_name"] = "Los apellidos son obligatorios."
        if not self.phone and not self.email:
            errors["phone"] = "Indica al menos un teléfono o un email."
        if errors:
            raise ValidationError(errors)


class Vehicle(TimeStampedModel):
    """Vehicle owned by a customer."""

    customer = models.ForeignKey(
        Customer,
        verbose_name="cliente",
        on_delete=models.CASCADE,
        related_name="vehicles",
    )
    plate = models.CharField("matrícula", max_length=15, unique=True)
    make = models.CharField("marca", max_length=50)
    model = models.CharField("modelo", max_length=50, blank=True)
    year = models.PositiveSmallIntegerField(
        "año",
        null=True,
        blank=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
    )
    vin = models.CharField("número de bastidor (VIN)", max_length=17, blank=True)
    mileage = models.PositiveIntegerField("kilometraje", null=True, blank=True)

    class Meta:
        verbose_name = "vehículo"
        verbose_name_plural = "vehículos"
        ordering = ["plate"]

    def __str__(self):
        return f"{self.make} {self.model} ({self.plate})".replace("  ", " ")

    def clean(self):
        super().clean()
        self.plate = normalize_plate(self.plate)

    def save(self, *args, **kwargs):
        self.plate = normalize_plate(self.plate)
        super().save(*args, **kwargs)