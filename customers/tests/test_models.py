import pytest
from django.core.exceptions import ValidationError

from customers.models import Customer, Vehicle


def test_plate_is_normalized(customer):
    vehicle = Vehicle.objects.create(customer=customer, plate="5678-xyz", make="Renault")
    assert vehicle.plate == "5678XYZ"


def test_company_requires_company_name():
    company = Customer(customer_type=Customer.CustomerType.COMPANY, phone="986234567")
    with pytest.raises(ValidationError) as error:
        company.full_clean()
    assert "company_name" in error.value.message_dict


def test_customer_requires_phone_or_email():
    customer = Customer(first_name="Ana", last_name="Pérez")
    with pytest.raises(ValidationError) as error:
        customer.full_clean()
    assert "phone" in error.value.message_dict