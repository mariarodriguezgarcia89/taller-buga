from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from billing.models import Quote


@pytest.fixture
def accepted_quote(quote):
    quote.status = Quote.Status.ACCEPTED
    quote.save()
    return quote


def test_draft_quote_cannot_be_invoiced(quote):
    with pytest.raises(ValidationError):
        quote.create_invoice()


def test_invoice_copies_quote_data(accepted_quote):
    invoice = accepted_quote.create_invoice()

    assert invoice.quote == accepted_quote
    assert invoice.customer == accepted_quote.customer
    assert invoice.lines.count() == 2
    assert invoice.total == Decimal("168.69")


def test_quote_can_only_be_invoiced_once(accepted_quote):
    accepted_quote.create_invoice()
    with pytest.raises(ValidationError):
        accepted_quote.create_invoice()


def test_invoice_is_not_affected_by_later_quote_changes(accepted_quote):
    invoice = accepted_quote.create_invoice()

    accepted_quote.discount_percent = Decimal("50")
    accepted_quote.save()
    invoice.refresh_from_db()

    assert invoice.discount_percent == Decimal("10.00")
    assert invoice.total == Decimal("168.69")