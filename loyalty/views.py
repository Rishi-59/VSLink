
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProductForm
from .models import Product


def staff_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "You are not authorized to access that page.")
            return redirect("loyalty:catalogue")
        return view_func(request, *args, **kwargs)

    return wrapper


@login_required
def catalogue_view(request):
    products = Product.objects.filter(is_active=True).order_by("name")
    return render(
        request,
        "loyalty/catalogue.html",
        {"products": products},
    )


@staff_required
def staff_products_view(request):
    products = Product.objects.all().order_by("name")
    return render(
        request,
        "loyalty/staff_products.html",
        {"products": products},
    )


@staff_required
def product_create_view(request):
    form = ProductForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product created successfully.")
        return redirect("loyalty:staff_products")

    return render(
        request,
        "loyalty/product_form.html",
        {"form": form, "page_title": "Add product"},
    )


@staff_required
def product_edit_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product updated successfully.")
        return redirect("loyalty:staff_products")

    return render(
        request,
        "loyalty/product_form.html",
        {"form": form, "page_title": "Edit product"},
    )


@staff_required
@require_POST
def product_toggle_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save(update_fields=["is_active", "updated_at"])

    messages.success(
        request,
        f"{product.name} is now "
        f"{'active' if product.is_active else 'inactive'}.",
    )
    return redirect("loyalty:staff_products")
