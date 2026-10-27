
from django.urls import path

from . import views

app_name = "loyalty"

urlpatterns = [
    path("products/", views.catalogue_view, name="catalogue"),
    path("staff/products/", views.staff_products_view, name="staff_products"),
    path(
        "staff/products/add/",
        views.product_create_view,
        name="product_create",
    ),
    path(
        "staff/products/<int:pk>/edit/",
        views.product_edit_view,
        name="product_edit",
    ),
    path(
        "staff/products/<int:pk>/toggle/",
        views.product_toggle_view,
        name="product_toggle",
    ),
]
