from datetime import date
from decimal import Decimal

from django.urls import reverse

from billing.models import Quote
from customers.models import ServiceRecord

LIST_URL = reverse("customers:vehicle_list")


def search(client, query):
    response = client.get(LIST_URL, {"q": query})
    assert response.status_code == 200
    return list(response.context["vehicle_list"])


def test_search_vehicle_by_plate(logged_client, vehicle):
    assert search(logged_client, "1234 abc") == [vehicle]


def test_search_vehicle_by_owner_name(logged_client, vehicle):
    assert search(logged_client, "otero") == [vehicle]


def test_history_combines_invoices_and_records_newest_first(logged_client, quote):
    ServiceRecord.objects.create(
        vehicle=quote.vehicle,
        date=date(2025, 3, 12),
        description="Cambio de aceite y filtros",
        amount=Decimal("89.50"),
    )
    quote.status = Quote.Status.ACCEPTED
    quote.save()
    invoice = quote.create_invoice()

    response = logged_client.get(quote.vehicle.get_absolute_url())
    history = response.context["history"]

    assert [entry.source for entry in history] == ["invoice", "record"]
    assert history[0].reference == invoice.number
    assert history[0].amount == Decimal("139.41")  # taxable base, without VAT


def test_vehicle_without_history_shows_empty_state(logged_client, vehicle):
    response = logged_client.get(vehicle.get_absolute_url())
    assert response.context["history"] == []
    assert "aún no tiene reparaciones" in response.content.decode()