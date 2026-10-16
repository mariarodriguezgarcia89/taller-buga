from decimal import Decimal

import pytest

from billing.models import Quote
from customers.models import Customer, Vehicle


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        first_name="Lucía", last_name="Otero Fernández", phone="600123456"
    )


@pytest.fixture
def vehicle(customer):
    return Vehicle.objects.create(customer=customer, plate="1234ABC", make="Seat")


@pytest.fixture
def quote(customer, vehicle):
    """Quote with two lines and a 10% discount: total 168.69."""
    quote = Quote.objects.create(
        customer=customer, vehicle=vehicle, discount_percent=Decimal("10")
    )
    quote.lines.create(description="Mano de obra", quantity=Decimal("2"), unit_price=Decimal("45"))
    quote.lines.create(
        description="Pastillas de freno delanteras", quantity=Decimal("1"), unit_price=Decimal("64.90")
    )
    return quote

@pytest.fixture
def logged_client(client, django_user_model, db):
    user = django_user_model.objects.create_user(username="staff", password="test-pass-123")
    client.force_login(user)
    return client