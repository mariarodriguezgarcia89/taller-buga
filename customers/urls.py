from django.urls import path

from . import views

app_name = "customers"

urlpatterns = [
    path("clientes/", views.CustomerListView.as_view(), name="customer_list"),
    path("clientes/nuevo/", views.CustomerCreateView.as_view(), name="customer_create"),
    path("clientes/<int:pk>/", views.CustomerDetailView.as_view(), name="customer_detail"),
    path("clientes/<int:pk>/editar/", views.CustomerUpdateView.as_view(), name="customer_update"),
    path("vehiculos/", views.VehicleListView.as_view(), name="vehicle_list"),
    path("vehiculos/<int:pk>/", views.VehicleDetailView.as_view(), name="vehicle_detail"),
]