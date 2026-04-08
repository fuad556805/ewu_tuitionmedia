"""
Signals for automatic commission creation when a tuition is marked completed.
"""
from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver

from tuitions.models import Tuition
from .models import Commission

COMMISSION_RATE = Decimal('0.30')


@receiver(post_save, sender=Tuition)
def auto_create_commission(sender, instance, created, **kwargs):
    """
    When a Tuition is marked 'completed', auto-create a Commission record
    for 30% of the monthly salary if one doesn't already exist.
    """
    if instance.status == 'completed':
        Commission.objects.get_or_create(
            tuition=instance,
            defaults={
                'tutor':  instance.tutor,
                'amount': (Decimal(instance.salary) * COMMISSION_RATE).quantize(Decimal('0.01')),
                'paid':   False,
            },
        )
