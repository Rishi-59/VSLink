
from django import forms

from .models import Product, Reward, ReferralConfig

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "points",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "points": forms.NumberInput(
                attrs={"class": "form-control", "min": "0"}
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }



class RewardForm(forms.ModelForm):
    class Meta:
        model = Reward
        fields = [
            "name",
            "description",
            "points_required",
            "discount_type",
            "discount_value",
            "max_discount_amount",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "points_required": forms.NumberInput(
                attrs={"class": "form-control", "min": 1}
            ),
            "discount_type": forms.Select(
                attrs={"class": "form-select"}
            ),
            "discount_value": forms.NumberInput(
                attrs={"class": "form-control", "min": "0.01", "step": "0.01"}
            ),
            "max_discount_amount": forms.NumberInput(
                attrs={"class": "form-control", "min": "0.01", "step": "0.01"}
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }
        help_texts = {
            "points_required": "Points the customer must redeem.",
            "discount_value": "Fixed INR amount or percentage, depending on the discount type.",
            "max_discount_amount": "Required for percentage discounts; limits the maximum INR discount.",
        }


class ReferralConfigForm(forms.ModelForm):
    class Meta:
        model = ReferralConfig
        fields = ["level1_percent", "level2_percent"]
        widgets = {
            "level1_percent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                    "step": 1,
                }
            ),
            "level2_percent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                    "step": 1,
                }
            ),
        }
        labels = {
            "level1_percent": "Direct referral bonus (%)",
            "level2_percent": "Second-level referral bonus (%)",
        }
        help_texts = {
            "level1_percent": "Percentage of the purchaser's earned points awarded to their direct referrer.",
            "level2_percent": "Percentage of the purchaser's earned points awarded to the referrer's referrer.",
        }

    def clean_level1_percent(self):
        value = self.cleaned_data["level1_percent"]
        if not 0 <= value <= 100:
            raise forms.ValidationError("Enter a value between 0 and 100.")
        return value

    def clean_level2_percent(self):
        value = self.cleaned_data["level2_percent"]
        if not 0 <= value <= 100:
            raise forms.ValidationError("Enter a value between 0 and 100.")
        return value
