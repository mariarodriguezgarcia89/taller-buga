from decimal import Decimal

from django.utils import timezone

from billing.models import Invoice, Quote, QuoteLine


def test_quote_totals(quote):
    assert quote.subtotal == Decimal("154.90")
    assert quote.discount_amount == Decimal("15.49")
    assert quote.taxable_base == Decimal("139.41")
    assert quote.vat_amount == Decimal("29.28")
    assert quote.total == Decimal("168.69")


def test_line_amount_rounds_half_up():
    line = QuoteLine(quantity=Decimal("0.50"), unit_price=Decimal("0.25"))
    assert line.amount == Decimal("0.13")  # 0.125 -> 0.13, not 0.12


def test_quote_without_lines_totals_zero(customer, vehicle):
    quote = Quote.objects.create(customer=customer, vehicle=vehicle)
    assert quote.total == Decimal("0")


def test_numbering_is_correlative_per_document_type(customer, vehicle):
    year = timezone.localdate().year
    first = Quote.objects.create(customer=customer, vehicle=vehicle)
    second = Quote.objects.create(customer=customer, vehicle=vehicle)
    invoice = Invoice.objects.create(customer=customer, vehicle=vehicle)

    assert first.number == f"P-{year}-0001"
    assert second.number == f"P-{year}-0002"
    assert invoice.number == f"F-{year}-0001"