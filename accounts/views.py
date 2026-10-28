
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST

from django.db.models import Sum

from .forms import RegistrationForm, StyledAuthenticationForm
from .models import CustomerProfile
from loyalty.models import PointsTransaction, Purchase, Reward

def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    form = RegistrationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your VSLink account is ready.")
        return redirect("accounts:profile")

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    form = StyledAuthenticationForm(
        request,
        data=request.POST or None,
    )

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("accounts:profile")

    return render(
        request,
        "accounts/login.html",
        {"form": form},
    )


@login_required
def profile_view(request):
    profile = get_object_or_404(
        CustomerProfile.objects.select_related("user", "referrer__user"),
        user=request.user,
    )

    balance = (
        PointsTransaction.objects
        .filter(customer=request.user)
        .aggregate(total=Sum("points"))["total"]
        or 0
    )

    purchases = Purchase.objects.filter(
        customer=request.user
    ).order_by("-purchased_at")

    recent_purchases = purchases[:5]

    purchase_count = purchases.count()
    referral_count = profile.referrals.count()

    eligible_rewards_count = Reward.objects.filter(
        is_active=True,
        points_required__lte=balance,
    ).count()

    recent_transactions = (
        PointsTransaction.objects
        .filter(customer=request.user)
        .select_related("purchase")
        .order_by("-created_at")[:5]
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile,
            "balance": balance,
            "recent_purchases": recent_purchases,
            "recent_transactions": recent_transactions,
            "purchase_count": purchase_count,
            "referral_count": referral_count,
            "eligible_rewards_count": eligible_rewards_count,
        },
    )


@require_POST
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("accounts:login")


def build_referral_branch(profile):
    """Build a nested tree of this profile and its descendants."""
    children = (
        profile.referrals
        .select_related("user")
        .order_by("created_at")
    )

    return {
        "profile": profile,
        "children": [
            build_referral_branch(child)
            for child in children
        ],
    }


@login_required
def referral_tree_view(request):
    current_profile = get_object_or_404(
        CustomerProfile.objects.select_related("user", "referrer__user"),
        user=request.user,
    )

    selected_profile = current_profile

    # Staff may inspect another customer's tree.
    if request.user.is_staff:
        customer_id = request.GET.get("customer_id")

        if customer_id:
            selected_profile = get_object_or_404(
                CustomerProfile.objects.select_related(
                    "user", "referrer__user"
                ),
                pk=customer_id,
            )

    # Build the chain of ancestors, from oldest ancestor to direct referrer.
    ancestors = []
    ancestor = selected_profile.referrer

    while ancestor:
        ancestors.append(ancestor)
        ancestor = ancestor.referrer

    ancestors.reverse()

    tree = build_referral_branch(selected_profile)

    customer_profiles = []
    if request.user.is_staff:
        customer_profiles = (
            CustomerProfile.objects
            .select_related("user")
            .order_by("user__username")
        )

    return render(
        request,
        "accounts/referral_tree.html",
        {
            "selected_profile": selected_profile,
            "ancestors": ancestors,
            "tree": tree,
            "customer_profiles": customer_profiles,
            "own_profile_id": current_profile.pk,
        },
    )
