
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


from .models import CustomerProfile

User = get_user_model()


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=15, required=False)
    referral_code = forms.CharField(
        max_length=8,
        required=False,
        help_text="Optional: enter your referrer's code.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "username",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )
        return email

    def clean_referral_code(self):
        code = self.cleaned_data.get("referral_code", "").strip().upper()

        if not code:
            return None

        if not CustomerProfile.objects.filter(
            referral_code=code
        ).exists():
            raise forms.ValidationError(
                "That referral code is invalid. Check it or leave it blank."
            )

        return code

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()

            referrer = None
            code = self.cleaned_data.get("referral_code")
            if code:
                referrer = CustomerProfile.objects.get(referral_code=code)

            CustomerProfile.objects.create(
                user=user,
                phone=self.cleaned_data.get("phone", "").strip(),
                referrer=referrer,
            )

        return user

class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"