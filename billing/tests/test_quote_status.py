import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from billing.models import Invoice, Quote


def test_draft_quote_can_be_sent(quote):
    quote.change_status(Quote.Status.SENT)
    quote.refresh_from_db()
    assert quote.status == Quote.Status.SENT


def test_accepted_quote_cannot_go_back_to_draft(quote):
    quote.change_status(Quote.Status.ACCEPTED)
    with pytest.raises(ValidationError):
        quote.change_status(Quote.Status.DRAFT)


def test_quote_detail_shows_total(logged_client, quote):
    response = logged_client.get(quote.get_absolute_url())
    assert response.status_code == 200
    assert "168,69" in response.content.decode()


def test_status_change_via_post(logged_client, quote):
    logged_client.post(reverse("billing:quote_status", args=[quote.pk]), {"status": "accepted"})
    quote.refresh_from_db()
    assert quote.status == Quote.Status.ACCEPTED


def test_status_change_rejects_get(logged_client, quote):
    response = logged_client.get(reverse("billing:quote_status", args=[quote.pk]))
    assert response.status_code == 405
    quote.refresh_from_db()
    assert quote.status == Quote.Status.DRAFT


def test_convert_accepted_quote_into_invoice(logged_client, quote):
    quote.change_status(Quote.Status.ACCEPTED)
    response = logged_client.post(reverse("billing:quote_invoice", args=[quote.pk]))
    assert response.status_code == 302
    assert Invoice.objects.filter(quote=quote).exists()