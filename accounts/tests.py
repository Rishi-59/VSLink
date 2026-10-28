
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.forms import RegistrationForm
from accounts.models import CustomerProfile


User = get_user_model()


class RegistrationFormTests(TestCase):
    def setUp(self):
        self.referrer_user = User.objects.create_user(
            username="existing_customer",
            email="referrer@example.com",
            password="S3cure-Test-Pass-418!",
        )
        self.referrer_profile = CustomerProfile.objects.create(
            user=self.referrer_user,
        )

    def registration_data(self, **overrides):
        data = {
            "first_name": "Test",
            "last_name": "Customer",
            "email": "new.customer@example.com",
            "username": "new_customer",
            "password1": "S3cure-New-Pass-519!",
            "password2": "S3cure-New-Pass-519!",
            "phone": "9876543210",
            "referral_code": "",
        }
        data.update(overrides)
        return data

    def test_registration_without_referral_code_succeeds(self):
        form = RegistrationForm(data=self.registration_data())

        self.assertTrue(form.is_valid(), form.errors)

        user = form.save()
        profile = user.customer_profile

        self.assertIsNone(profile.referrer)
        self.assertEqual(len(profile.referral_code), 8)
        self.assertTrue(profile.referral_code)

    def test_valid_referral_code_links_the_new_customer(self):
        form = RegistrationForm(
            data=self.registration_data(
                referral_code=self.referrer_profile.referral_code.lower(),
            )
        )

        self.assertTrue(form.is_valid(), form.errors)

        user = form.save()

        self.assertEqual(
            user.customer_profile.referrer,
            self.referrer_profile,
        )

    def test_invalid_referral_code_is_rejected(self):
        form = RegistrationForm(
            data=self.registration_data(
                referral_code="INVALID1",
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("referral_code", form.errors)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        form = RegistrationForm(
            data=self.registration_data(
                email="REFERRER@EXAMPLE.COM",
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_referral_codes_are_unique(self):
        form = RegistrationForm(data=self.registration_data())
        self.assertTrue(form.is_valid(), form.errors)

        new_user = form.save()

        self.assertNotEqual(
            new_user.customer_profile.referral_code,
            self.referrer_profile.referral_code,
        )


class CustomerProfileReferralIntegrityTests(TestCase):
    def setUp(self):
        self.first_user = User.objects.create_user(
            username="first_customer",
            password="S3cure-Test-Pass-418!",
        )
        self.first_profile = CustomerProfile.objects.create(
            user=self.first_user,
        )

        self.second_user = User.objects.create_user(
            username="second_customer",
            password="S3cure-Test-Pass-418!",
        )
        self.second_profile = CustomerProfile.objects.create(
            user=self.second_user,
            referrer=self.first_profile,
        )

    def test_customer_cannot_refer_themselves(self):
        self.first_profile.referrer = self.first_profile

        with self.assertRaises(ValidationError):
            self.first_profile.save()

    def test_referrer_cannot_be_changed_after_registration(self):
        third_user = User.objects.create_user(
            username="third_customer",
            password="S3cure-Test-Pass-418!",
        )
        third_profile = CustomerProfile.objects.create(
            user=third_user,
        )

        self.second_profile.referrer = third_profile

        with self.assertRaises(ValidationError):
            self.second_profile.save()

        self.second_profile.refresh_from_db()
        self.assertEqual(
            self.second_profile.referrer,
            self.first_profile,
        )
