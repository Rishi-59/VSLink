import secrets
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import RegexValidator

PHONE_VALIDATOR = RegexValidator(
    regex=r"\A[0-9]{10}\Z",
    message="Enter a valid 10-digit phone number.",
)

def generate_referral_code():
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="customer_profile",
    )
    phone = models.CharField(
        max_length=10,
        blank=True,
        validators=[PHONE_VALIDATOR],
    )
    referral_code = models.CharField(
        max_length=8,
        unique=True,
        blank=True,
    )
    referrer = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="referrals",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()

        if self.pk and self.referrer_id == self.pk:
            raise ValidationError({
                "referrer": "A customer cannot refer themselves."
            })

        if self.pk:
            old_referrer_id = (
                CustomerProfile.objects
                .filter(pk=self.pk)
                .values_list("referrer_id", flat=True)
                .first()
            )

            if old_referrer_id != self.referrer_id:
                raise ValidationError({
                    "referrer": (
                        "A customer's referrer cannot be changed "
                        "after registration."
                    )
                })

    def save(self, *args, **kwargs):
        if not self.referral_code:
            while True:
                code = generate_referral_code()
                if not CustomerProfile.objects.filter(
                    referral_code=code
                ).exists():
                    self.referral_code = code
                    break

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.get_full_name() or self.user.get_username()