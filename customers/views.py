from .models import Customer, normalize_plate

from django.db.models import Count, Q, Value
from django.db.models.functions import Coalesce, Lower, NullIf

from django.views.generic import DetailView, ListView


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
        return queryset.annotate(
            sort_name=Lower(Coalesce(NullIf("company_name", Value("")), "last_name"))
        ).order_by("sort_name", "first_name").distinct()
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

def test_customer_detail_shows_vehicles(logged_client, vehicle):
    response = logged_client.get(vehicle.customer.get_absolute_url())
    assert response.status_code == 200
    assert "1234ABC" in response.content.decode()


def test_customer_detail_returns_404_for_unknown_customer(logged_client):
    response = logged_client.get(reverse("customers:customer_detail", args=[999999]))
    assert response.status_code == 404