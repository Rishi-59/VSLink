
from django import forms

from .models import Product, Reward

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
