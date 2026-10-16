from django.urls import reverse

from billing.models import Quote

LIST_URL = reverse("billing:quote_list")


def listed_quotes(client, **params):
    response = client.get(LIST_URL, params)
    assert response.status_code == 200
    return list(response.context["quote_list"])


def test_quote_list_filters_by_status(logged_client, quote):
    accepted = Quote.objects.create(
        customer=quote.customer, vehicle=quote.vehicle, status=Quote.Status.ACCEPTED
    )
    assert listed_quotes(logged_client, status="accepted") == [accepted]
    assert listed_quotes(logged_client, status="draft") == [quote]


def test_unknown_status_is_ignored(logged_client, quote):
    assert listed_quotes(logged_client, status="whatever") == [quote]


def test_quote_list_search_by_plate(logged_client, quote):
    assert listed_quotes(logged_client, q="1234-abc") == [quote]