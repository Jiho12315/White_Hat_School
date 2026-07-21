from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from wallets.models import Wallet
from .models import User


@receiver(post_save, sender=User)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.get_or_create(user=instance, defaults={"balance": settings.INITIAL_POINT_BALANCE})
