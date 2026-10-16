from django import forms

from core.forms import BootstrapFormMixin

from .models import Customer, Vehicle


class CustomerForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "customer_type",
            "first_name",
            "last_name",
            "company_name",
            "tax_id",
            "phone",
            "email",
            "address",
            "postal_code",
            "city",
            "insurer",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["insurer"].empty_label = "Sin aseguradora"

    def clean_tax_id(self):
        """Store NIF/CIF uppercase and without spaces or hyphens."""
        tax_id = self.cleaned_data["tax_id"]
        return tax_id.upper().replace(" ", "").replace("-", "")

class VehicleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ["plate", "make", "model", "year", "mileage", "vin"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plate"].widget.attrs.update(
            placeholder="1234 ABC", style="text-transform: uppercase", autocomplete="off"
        )

    def clean_vin(self):
        return self.cleaned_data["vin"].upper().replace(" ", "")