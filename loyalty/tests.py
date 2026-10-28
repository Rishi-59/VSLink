from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.db.models import Sum

from accounts.models import CustomerProfile
from loyalty.models import PointsTransaction, Product, Purchase


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