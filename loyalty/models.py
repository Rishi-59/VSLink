from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    points = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Reward(models.Model):
    class DiscountType(models.TextChoices):
        FIXED = "FIXED", "Fixed INR discount"
        PERCENTAGE = "PERCENTAGE", "Percentage discount"

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    points_required = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    discount_type = models.CharField(
        max_length=10,
        choices=DiscountType.choices,
        default=DiscountType.FIXED,
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()

        if (
            self.discount_type == self.DiscountType.PERCENTAGE
            and self.discount_value > 100
        ):
            raise ValidationError({
                "discount_value": "Percentage cannot exceed 100."
            })

        if (
            self.discount_type == self.DiscountType.PERCENTAGE
            and self.max_discount_amount is None
        ):
            raise ValidationError({
                "max_discount_amount": (
                    "A maximum discount amount is required "
                    "for percentage rewards."
                )
            })

    def __str__(self):
        return self.name


class Purchase(models.Model):
    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="purchases",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="purchases",
    )
    product_name = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_paid = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    points_earned = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.COMPLETED,
    )
    purchased_at = models.DateTimeField(auto_now_add=True)
    checkout_token = models.UUIDField(
        unique=True,
        null=True,
        blank=True,
        editable=False,
    )

    def __str__(self):
        return f"Purchase #{self.pk}"


class Redemption(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="redemptions",
    )
    reward = models.ForeignKey(
        Reward,
        on_delete=models.PROTECT,
        related_name="redemptions",
    )
    purchase = models.OneToOneField(
        Purchase,
        on_delete=models.PROTECT,
        related_name="redemption",
    )
    points_used = models.PositiveIntegerField()
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    redeemed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Redemption #{self.pk}"


class PointsTransaction(models.Model):
    class TransactionType(models.TextChoices):
        PURCHASE = "PURCHASE", "Purchase points"
        DIRECT_REFERRAL = "DIRECT_REFERRAL", "Direct referral bonus"
        INDIRECT_REFERRAL = "INDIRECT_REFERRAL", "Indirect referral bonus"
        REDEMPTION = "REDEMPTION", "Reward redemption"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="points_transactions",
    )
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="points_transactions",
    )
    redemption = models.ForeignKey(
        Redemption,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="points_transactions",
    )
    type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )
    level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(2)],
    )
    points = models.IntegerField()
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer}: {self.points} points"


class ReferralConfig(models.Model):
    level1_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    level2_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=25,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Referral configuration"