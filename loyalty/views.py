
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from django.db import transaction
from django.db.models import Sum
from django.http import Http404

from .forms import ProductForm
from accounts.models import CustomerProfile
from .models import (
    Product,
    Purchase,
    PointsTransaction,
    Reward,
    Redemption,
    ReferralConfig,
)

from decimal import Decimal, ROUND_DOWN


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
    balance = (
        PointsTransaction.objects
        .filter(customer=request.user)
        .aggregate(total=Sum("points"))["total"]
        or 0
    )

    return render(
        request,
        "loyalty/catalogue.html",
        {"products": products, "balance": balance},
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

def get_points_balance(user):
    return (
        PointsTransaction.objects
        .filter(customer=user)
        .aggregate(total=Sum("points"))["total"]
        or 0
    )


def calculate_discount(reward, price):
    if reward.discount_type == Reward.DiscountType.FIXED:
        discount = reward.discount_value
    else:
        discount = price * reward.discount_value / Decimal("100")
        discount = min(discount, reward.max_discount_amount)

    return min(discount, price).quantize(
        Decimal("0.01"),
        rounding=ROUND_DOWN,
    )


@login_required
def checkout_view(request, pk):
    if request.method == "POST":
        return complete_purchase(request, pk)

    product = get_object_or_404(Product, pk=pk, is_active=True)
    balance = get_points_balance(request.user)

    rewards = Reward.objects.filter(
        is_active=True,
        points_required__lte=balance,
    ).order_by("points_required")

    return render(
        request,
        "loyalty/checkout.html",
        {
            "product": product,
            "balance": balance,
            "rewards": rewards,
        },
    )


@login_required
@require_POST
def complete_purchase(request, pk):
    try:
        with transaction.atomic():
            product = (
                Product.objects
                .select_for_update()
                .get(pk=pk, is_active=True)
            )

            profile = CustomerProfile.objects.get(user=request.user)

            reward = None
            discount = Decimal("0.00")

            reward_id = request.POST.get("reward_id", "").strip()

            if reward_id:
                try:
                    reward = Reward.objects.get(
                        pk=reward_id,
                        is_active=True,
                    )
                except (Reward.DoesNotExist, ValueError):
                    messages.error(request, "That reward is not available.")
                    return redirect("loyalty:checkout", pk=pk)

                balance = get_points_balance(request.user)

                if balance < reward.points_required:
                    messages.error(
                        request,
                        "You don't have enough points for that reward.",
                    )
                    return redirect("loyalty:checkout", pk=pk)

                discount = calculate_discount(reward, product.price)

            price_paid = product.price - discount

            purchase = Purchase.objects.create(
                customer=request.user,
                product=product,
                product_name=product.name,
                base_price=product.price,
                price_paid=price_paid,
                discount_amount=discount,
                points_earned=product.points,
                status=Purchase.Status.COMPLETED,
            )

            PointsTransaction.objects.create(
                customer=request.user,
                purchase=purchase,
                type=PointsTransaction.TransactionType.PURCHASE,
                points=product.points,
                description=f"Points earned from {product.name}",
            )

            # Referral rewards: direct referrer and one level above.
            config, _ = ReferralConfig.objects.get_or_create(pk=1)

            direct_referrer = profile.referrer

            if direct_referrer:
                direct_points = int(
                    (
                        Decimal(product.points)
                        * config.level1_percent
                        / Decimal("100")
                    ).quantize(Decimal("1"), rounding=ROUND_DOWN)
                )

                if direct_points > 0:
                    PointsTransaction.objects.create(
                        customer=direct_referrer.user,
                        purchase=purchase,
                        type=PointsTransaction.TransactionType.DIRECT_REFERRAL,
                        level=1,
                        points=direct_points,
                        description=(
                            f"Direct referral bonus from {product.name}"
                        ),
                    )

                indirect_referrer = direct_referrer.referrer

                if indirect_referrer:
                    indirect_points = int(
                        (
                            Decimal(product.points)
                            * config.level2_percent
                            / Decimal("100")
                        ).quantize(Decimal("1"), rounding=ROUND_DOWN)
                    )

                    if indirect_points > 0:
                        PointsTransaction.objects.create(
                            customer=indirect_referrer.user,
                            purchase=purchase,
                            type=(
                                PointsTransaction.TransactionType
                                .INDIRECT_REFERRAL
                            ),
                            level=2,
                            points=indirect_points,
                            description=(
                                f"Second-level referral bonus from "
                                f"{product.name}"
                            ),
                        )

            if reward:
                Redemption.objects.create(
                    customer=request.user,
                    reward=reward,
                    purchase=purchase,
                    points_used=reward.points_required,
                    discount_amount=discount,
                )

                PointsTransaction.objects.create(
                    customer=request.user,
                    purchase=purchase,
                    redemption=purchase.redemption,
                    type=PointsTransaction.TransactionType.REDEMPTION,
                    points=-reward.points_required,
                    description=f"Redeemed reward: {reward.name}",
                )

        messages.success(
            request,
            f"Purchase completed! You earned {product.points} points.",
        )
        return redirect("loyalty:purchase_history")

    except Product.DoesNotExist:
        raise Http404("This product is unavailable.")
    except CustomerProfile.DoesNotExist:
        messages.error(
            request,
            "Your customer profile is missing. Please contact support.",
        )
        return redirect("loyalty:catalogue")


@login_required
def purchase_history_view(request):
    purchases = (
        Purchase.objects
        .filter(customer=request.user)
        .select_related("product")
        .order_by("-purchased_at")
    )

    transactions = (
        PointsTransaction.objects
        .filter(customer=request.user)
        .select_related("purchase")
        .order_by("-created_at")[:50]
    )

    return render(
        request,
        "loyalty/purchase_history.html",
        {
            "purchases": purchases,
            "transactions": transactions,
            "balance": get_points_balance(request.user),
        },
    )