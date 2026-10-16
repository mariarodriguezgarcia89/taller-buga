from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("presupuestos/", views.QuoteListView.as_view(), name="quote_list"),
    path("presupuestos/<int:pk>/", views.QuoteDetailView.as_view(), name="quote_detail"),
    path("presupuestos/<int:pk>/estado/", views.QuoteStatusUpdateView.as_view(), name="quote_status"),
    path("presupuestos/<int:pk>/facturar/", views.QuoteInvoiceCreateView.as_view(), name="quote_invoice"),
]