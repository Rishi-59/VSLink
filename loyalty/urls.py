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
    path(
        "products/<int:pk>/checkout/",
        views.checkout_view,
        name="checkout",
    ),
    path(
        "purchases/",
        views.purchase_history_view,
        name="purchase_history",
    ),
    path("staff/rewards/", views.staff_rewards_view, name="staff_rewards"),
    path("staff/rewards/add/", views.reward_create_view, name="reward_create"),
    path(
        "staff/rewards/<int:pk>/edit/",
        views.reward_edit_view,
        name="reward_edit",
    ),
    path(
        "staff/rewards/<int:pk>/toggle/",
        views.reward_toggle_view,
        name="reward_toggle",
    ),
    path(
        "staff/rewards/",
        views.staff_rewards_view,
        name="staff_rewards",
    ),
]
