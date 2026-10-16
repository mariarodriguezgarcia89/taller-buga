from django.shortcuts import render

from billing.models import Invoice, Quote
from customers.models import Customer, Vehicle


def dashboard(request):
    context = {
        "customer_count": Customer.objects.count(),
        "vehicle_count": Vehicle.objects.count(),
        "open_quote_count": Quote.objects.filter(
            status__in=[Quote.Status.DRAFT, Quote.Status.SENT]
        ).count(),
        "unpaid_invoice_count": Invoice.objects.filter(status=Invoice.Status.PENDING).count(),
    }
    return render(request, "core/dashboard.html", context)