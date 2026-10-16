from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("presupuestos/", views.QuoteListView.as_view(), name="quote_list"),
]