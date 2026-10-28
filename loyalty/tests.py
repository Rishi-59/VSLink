from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.db.models import Sum

from accounts.models import CustomerProfile
from loyalty.models import (
    PointsTransaction,
    Product,
    Purchase,
    Redemption,
    ReferralConfig,
    Reward,
)


User = get_user_model()


class CheckoutIdempotencyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="checkout_customer",
            password="test-password-123",
        )
        CustomerProfile.objects.create(user=self.user)

        self.product = Product.objects.create(
            name="Test Product",
            description="A product for checkout tests.",
            price=Decimal("500.00"),
            points=10,
            is_active=True,
        )

        self.client.force_login(self.user)
        self.checkout_url = reverse(
            "loyalty:checkout",
            kwargs={"pk": self.product.pk},
        )

    def test_reposting_checkout_does_not_award_points_twice(self):
        checkout_page = self.client.get(self.checkout_url)
        self.assertEqual(checkout_page.status_code, 200)

        token = str(checkout_page.context["checkout_token"])
        payload = {
            "checkout_token": token,
            "reward_id": "",
        }

        first_response = self.client.post(
            self.checkout_url,
            payload,
        )
        second_response = self.client.post(
            self.checkout_url,
            payload,
        )

        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(second_response.status_code, 302)

        self.assertEqual(
            Purchase.objects.filter(customer=self.user).count(),
            1,
        )

        self.assertEqual(
            PointsTransaction.objects.filter(
                customer=self.user,
                type=PointsTransaction.TransactionType.PURCHASE,
            ).count(),
            1,
        )

        total_points = (
            PointsTransaction.objects
            .filter(customer=self.user)
            .aggregate(total=Sum("points"))["total"]
        )
        self.assertEqual(total_points, 10)

class LoyaltyCheckoutRuleTests(TestCase):
    def make_customer(self, username, referrer=None, is_staff=False):
        user = User.objects.create_user(
            username=username,
            password="test-password-123",
            is_staff=is_staff,
        )
        profile = CustomerProfile.objects.create(
            user=user,
            referrer=referrer,
        )
        return user, profile

    def setUp(self):
        self.user, self.profile = self.make_customer("rule_customer")

        self.product = Product.objects.create(
            name="Test Product",
            description="Product for loyalty tests.",
            price=Decimal("500.00"),
            points=100,
            is_active=True,
        )

        self.checkout_url = reverse(
            "loyalty:checkout",
            kwargs={"pk": self.product.pk},
        )
        self.client.force_login(self.user)

    def checkout_token(self):
        response = self.client.get(self.checkout_url)
        self.assertEqual(response.status_code, 200)
        return str(response.context["checkout_token"])

    def add_points(self, points):
        return PointsTransaction.objects.create(
            customer=self.user,
            type=PointsTransaction.TransactionType.PURCHASE,
            points=points,
            description="Test starting balance",
        )

    def test_fixed_discount_is_applied_and_points_are_deducted(self):
        self.add_points(100)

        reward = Reward.objects.create(
            name="₹75 Off",
            points_required=50,
            discount_type=Reward.DiscountType.FIXED,
            discount_value=Decimal("75.00"),
            is_active=True,
        )

        response = self.client.post(
            self.checkout_url,
            {
                "checkout_token": self.checkout_token(),
                "reward_id": str(reward.pk),
            },
        )

        self.assertEqual(response.status_code, 302)

        purchase = Purchase.objects.get(customer=self.user)
        self.assertEqual(purchase.discount_amount, Decimal("75.00"))
        self.assertEqual(purchase.price_paid, Decimal("425.00"))

        redemption = Redemption.objects.get(purchase=purchase)
        self.assertEqual(redemption.points_used, 50)
        self.assertEqual(redemption.discount_amount, Decimal("75.00"))

        deduction = PointsTransaction.objects.get(
            customer=self.user,
            purchase=purchase,
            type=PointsTransaction.TransactionType.REDEMPTION,
        )
        self.assertEqual(deduction.points, -50)

    def test_percentage_discount_respects_maximum_cap(self):
        self.add_points(100)

        reward = Reward.objects.create(
            name="30 Percent Off",
            points_required=40,
            discount_type=Reward.DiscountType.PERCENTAGE,
            discount_value=Decimal("30.00"),
            max_discount_amount=Decimal("50.00"),
            is_active=True,
        )

        response = self.client.post(
            self.checkout_url,
            {
                "checkout_token": self.checkout_token(),
                "reward_id": str(reward.pk),
            },
        )

        self.assertEqual(response.status_code, 302)

        purchase = Purchase.objects.get(customer=self.user)
        self.assertEqual(purchase.discount_amount, Decimal("50.00"))
        self.assertEqual(purchase.price_paid, Decimal("450.00"))

    def test_insufficient_points_reject_reward_redemption(self):
        reward = Reward.objects.create(
            name="Expensive Reward",
            points_required=50,
            discount_type=Reward.DiscountType.FIXED,
            discount_value=Decimal("100.00"),
            is_active=True,
        )

        response = self.client.post(
            self.checkout_url,
            {
                "checkout_token": self.checkout_token(),
                "reward_id": str(reward.pk),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Purchase.objects.filter(customer=self.user).exists()
        )
        self.assertFalse(
            Redemption.objects.filter(customer=self.user).exists()
        )

    def test_inactive_reward_cannot_be_redeemed(self):
        reward = Reward.objects.create(
            name="Inactive Reward",
            points_required=10,
            discount_type=Reward.DiscountType.FIXED,
            discount_value=Decimal("25.00"),
            is_active=False,
        )

        response = self.client.post(
            self.checkout_url,
            {
                "checkout_token": self.checkout_token(),
                "reward_id": str(reward.pk),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Purchase.objects.filter(customer=self.user).exists()
        )
        self.assertFalse(
            Redemption.objects.filter(customer=self.user).exists()
        )

    def test_invalid_checkout_token_is_rejected(self):
        response = self.client.post(
            self.checkout_url,
            {
                "checkout_token": "not-a-valid-token",
                "reward_id": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.checkout_url)
        self.assertFalse(
            Purchase.objects.filter(customer=self.user).exists()
        )

    def test_referral_bonuses_stop_after_two_levels(self):
        older_user, older_profile = self.make_customer("older_ancestor")

        grandparent_user, grandparent_profile = self.make_customer(
            "grandparent",
            referrer=older_profile,
        )

        direct_user, direct_profile = self.make_customer(
            "direct_referrer",
            referrer=grandparent_profile,
        )

        buyer, buyer_profile = self.make_customer(
            "referral_buyer",
            referrer=direct_profile,
        )

        ReferralConfig.objects.create(
            pk=1,
            level1_percent=Decimal("50.00"),
            level2_percent=Decimal("25.00"),
        )

        self.client.force_login(buyer)

        response = self.client.post(
            self.checkout_url,
            {
                "checkout_token": self.checkout_token(),
                "reward_id": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        purchase = Purchase.objects.get(customer=buyer)

        buyer_points = PointsTransaction.objects.get(
            customer=buyer,
            purchase=purchase,
            type=PointsTransaction.TransactionType.PURCHASE,
        )
        direct_bonus = PointsTransaction.objects.get(
            customer=direct_user,
            purchase=purchase,
            type=PointsTransaction.TransactionType.DIRECT_REFERRAL,
        )
        indirect_bonus = PointsTransaction.objects.get(
            customer=grandparent_user,
            purchase=purchase,
            type=PointsTransaction.TransactionType.INDIRECT_REFERRAL,
        )

        self.assertEqual(buyer_points.points, 100)
        self.assertEqual(direct_bonus.points, 50)
        self.assertEqual(direct_bonus.level, 1)
        self.assertEqual(indirect_bonus.points, 25)
        self.assertEqual(indirect_bonus.level, 2)

        self.assertFalse(
            PointsTransaction.objects.filter(
                customer=older_user,
                purchase=purchase,
            ).exists()
        )

    def test_customer_cannot_access_staff_product_management(self):
        response = self.client.get(
            reverse("loyalty:staff_products")
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("loyalty:catalogue"),
        )