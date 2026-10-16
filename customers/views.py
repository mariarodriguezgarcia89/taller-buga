from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q, Value
from django.db.models.functions import Coalesce, Lower, NullIf
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import CustomerForm, VehicleForm
from .models import Customer, Vehicle, normalize_plate

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from django.shortcuts import get_object_or_404

def customer_search_filter(term):
    """Match a single search term against the customer's main fields and plates."""
    return (
        Q(first_name__icontains=term)
        | Q(last_name__icontains=term)
        | Q(company_name__icontains=term)
        | Q(tax_id__icontains=term)
        | Q(phone__icontains=term)
        | Q(email__icontains=term)
        | Q(vehicles__plate__icontains=normalize_plate(term))
    )


class CustomerListView(ListView):
    model = Customer
    paginate_by = 20

    def get_queryset(self):
        queryset = Customer.objects.select_related("insurer").annotate(
            vehicle_count=Count("vehicles", distinct=True)
        )
        for term in self.search_query.split():
            queryset = queryset.filter(customer_search_filter(term))
        return (
            queryset.annotate(
                sort_name=Lower(Coalesce(NullIf("company_name", Value("")), "last_name"))
            )
            .order_by("sort_name", "first_name")
            .distinct()
        )

    @property
    def search_query(self):
        return self.request.GET.get("q", "").strip()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.search_query
        return context


class CustomerDetailView(DetailView):
    model = Customer

    def get_queryset(self):
        return Customer.objects.select_related("insurer")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object
        context["vehicles"] = customer.vehicles.all()
        context["quotes"] = customer.quotes.select_related("vehicle").prefetch_related("lines")[:5]
        context["invoices"] = customer.invoices.select_related("vehicle").prefetch_related("lines")[:5]
        return context


class CustomerCreateView(SuccessMessageMixin, CreateView):
    model = Customer
    form_class = CustomerForm

    def get_success_message(self, cleaned_data):
        return f"Cliente «{self.object.display_name}» creado."


class CustomerUpdateView(SuccessMessageMixin, UpdateView):
    model = Customer
    form_class = CustomerForm

    def get_success_message(self, cleaned_data):
        return f"Cambios de «{self.object.display_name}» guardados."

class VehicleListView(ListView):
    model = Vehicle
    paginate_by = 20

    def get_queryset(self):
        queryset = Vehicle.objects.select_related("customer")
        for term in self.search_query.split():
            queryset = queryset.filter(
                Q(plate__icontains=normalize_plate(term))
                | Q(make__icontains=term)
                | Q(model__icontains=term)
                | Q(customer__first_name__icontains=term)
                | Q(customer__last_name__icontains=term)
                | Q(customer__company_name__icontains=term)
            )
        return queryset

    @property
    def search_query(self):
        return self.request.GET.get("q", "").strip()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.search_query
        return context


@dataclass
class HistoryEntry:
    """One row of a vehicle's history, from an invoice or an imported record."""

    date: date
    description: str
    amount: Decimal
    source: str
    reference: str = ""
    url: str = ""


class VehicleDetailView(DetailView):
    model = Vehicle

    def get_queryset(self):
        return Vehicle.objects.select_related("customer")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicle = self.object
        history = [
            HistoryEntry(
                date=invoice.issue_date,
                description=", ".join(line.description for line in invoice.lines.all()),
                amount=invoice.taxable_base,
                source="invoice",
                reference=invoice.number,
            )
            for invoice in vehicle.invoices.prefetch_related("lines")
        ]
        history += [
            HistoryEntry(
                date=record.date,
                description=record.description,
                amount=record.amount,
                source="record",
            )
            for record in vehicle.service_records.all()
        ]
        context["history"] = sorted(history, key=lambda entry: entry.date, reverse=True)
        return context

class VehicleCreateView(SuccessMessageMixin, CreateView):
    """Add a vehicle to the customer given in the URL."""

    model = Vehicle
    form_class = VehicleForm

    def dispatch(self, request, *args, **kwargs):
        self.customer = get_object_or_404(Customer, pk=kwargs["customer_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.customer = self.customer
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer"] = self.customer
        return context

    def get_success_url(self):
        return self.customer.get_absolute_url()

    def get_success_message(self, cleaned_data):
        return f"Vehículo {self.object.plate} añadido a {self.customer.display_name}."


class VehicleUpdateView(SuccessMessageMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm

    def get_queryset(self):
        return Vehicle.objects.select_related("customer")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer"] = self.object.customer
        return context

    def get_success_message(self, cleaned_data):
        return f"Cambios de {self.object.plate} guardados."