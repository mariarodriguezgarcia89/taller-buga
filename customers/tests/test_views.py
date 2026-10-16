from django.urls import reverse

from customers.models import Customer

LIST_URL = reverse("customers:customer_list")


def search(client, query):
    response = client.get(LIST_URL, {"q": query})
    assert response.status_code == 200
    return list(response.context["customer_list"])


def make_company():
    return Customer.objects.create(
        customer_type=Customer.CustomerType.COMPANY,
        company_name="Transportes Bouzas S.L.",
        phone="986234567",
    )


def test_list_shows_all_customers(logged_client, customer):
    company = make_company()
    assert set(search(logged_client, "")) == {customer, company}


def test_search_by_last_name(logged_client, customer):
    make_company()
    assert search(logged_client, "otero") == [customer]


def test_search_by_full_name_across_fields(logged_client, customer):
    assert search(logged_client, "lucía otero") == [customer]


def test_search_by_plate_in_any_format(logged_client, vehicle):
    assert search(logged_client, "1234-abc") == [vehicle.customer]


def test_customer_with_two_matching_vehicles_appears_once(logged_client, vehicle):
    vehicle.customer.vehicles.create(plate="1234ABD", make="Renault")
    assert search(logged_client, "1234AB") == [vehicle.customer]