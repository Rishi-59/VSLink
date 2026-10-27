
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, StyledAuthenticationForm
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import RegistrationForm



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
    profile = request.user.customer_profile

    return render(
        request,
        "accounts/profile.html",
        {"profile": profile},
    )


@require_POST
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("accounts:login")
