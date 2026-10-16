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

def test_customer_detail_shows_vehicles(logged_client, vehicle):
    response = logged_client.get(vehicle.customer.get_absolute_url())
    assert response.status_code == 200
    assert "1234ABC" in response.content.decode()


def test_customer_detail_returns_404_for_unknown_customer(logged_client):
    response = logged_client.get(reverse("customers:customer_detail", args=[999999]))
    assert response.status_code == 404

def customer_form_data(**overrides):
    data = {
        "customer_type": "individual",
        "first_name": "Xoán",
        "last_name": "Pereira Lago",
        "company_name": "",
        "tax_id": "12345678-z",
        "phone": "600987654",
        "email": "",
        "address": "",
        "postal_code": "",
        "city": "Vigo",
        "insurer": "",
    }
    data.update(overrides)
    return data


def test_create_customer_redirects_to_detail(logged_client, db):
    response = logged_client.post(reverse("customers:customer_create"), customer_form_data())
    customer = Customer.objects.get(last_name="Pereira Lago")
    assert response.status_code == 302
    assert response.url == customer.get_absolute_url()
    assert customer.tax_id == "12345678Z"


def test_company_without_name_is_not_created(logged_client, db):
    data = customer_form_data(customer_type="company", first_name="", last_name="")
    response = logged_client.post(reverse("customers:customer_create"), data)
    assert response.status_code == 200
    assert "company_name" in response.context["form"].errors
    assert not Customer.objects.exists()


def test_update_customer(logged_client, customer):
    url = reverse("customers:customer_update", args=[customer.pk])
    data = customer_form_data(first_name="Lucía", last_name="Otero Fernández", phone="611222333")
    logged_client.post(url, data)
    customer.refresh_from_db()
    assert customer.phone == "611222333"