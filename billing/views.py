from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from customers.models import normalize_plate

from .models import Quote


class QuoteListView(ListView):
    model = Quote
    paginate_by = 20

    def get_queryset(self):
        queryset = Quote.objects.select_related("customer", "vehicle").prefetch_related("lines")
        if self.status:
            queryset = queryset.filter(status=self.status)
        for term in self.search_query.split():
            queryset = queryset.filter(
                Q(number__icontains=term)
                | Q(vehicle__plate__icontains=normalize_plate(term))
                | Q(customer__first_name__icontains=term)
                | Q(customer__last_name__icontains=term)
                | Q(customer__company_name__icontains=term)
            )
        return queryset

    @property
    def status(self):
        status = self.request.GET.get("status", "")
        return status if status in Quote.Status.values else ""

    @property
    def search_query(self):
        return self.request.GET.get("q", "").strip()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        counts = dict(Quote.objects.order_by().values_list("status").annotate(total=Count("id")))
        context["status_tabs"] = [("", "Todos", sum(counts.values()))] + [
            (value, label, counts.get(value, 0)) for value, label in Quote.Status.choices
        ]
        context["current_status"] = self.status
        context["query"] = self.search_query
        return context

STATUS_ACTIONS = {
    Quote.Status.SENT: ("Marcar como enviado", "btn-outline-primary", "bi-send"),
    Quote.Status.ACCEPTED: ("Aceptar", "btn-success", "bi-check-lg"),
    Quote.Status.REJECTED: ("Rechazar", "btn-outline-danger", "bi-x-lg"),
}


class QuoteDetailView(DetailView):
    model = Quote

    def get_queryset(self):
        return Quote.objects.select_related("customer", "vehicle", "insurer").prefetch_related("lines")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quote = self.object
        context["actions"] = [
            (status, *STATUS_ACTIONS[status]) for status in quote.ALLOWED_TRANSITIONS[quote.status]
        ]
        context["invoice"] = getattr(quote, "invoice", None)
        return context


class QuoteStatusUpdateView(View):
    """Change a quote's status. POST only."""

    def post(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk)
        try:
            quote.change_status(request.POST.get("status", ""))
        except ValidationError as error:
            messages.error(request, error.messages[0])
        else:
            messages.success(request, f"Presupuesto {quote.number}: {quote.get_status_display().lower()}.")
        return redirect(quote)


class QuoteInvoiceCreateView(View):
    """Create the invoice for an accepted quote. POST only."""

    def post(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk)
        try:
            invoice = quote.create_invoice()
        except ValidationError as error:
            messages.error(request, error.messages[0])
        else:
            messages.success(request, f"Factura {invoice.number} creada.")
        return redirect(quote)