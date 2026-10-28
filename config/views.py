from django.shortcuts import render


def home_view(request):
    """Render the public VSLink landing page."""
    return render(request, "home.html")