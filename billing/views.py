from django.db.models import Count, Q
from django.views.generic import ListView

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