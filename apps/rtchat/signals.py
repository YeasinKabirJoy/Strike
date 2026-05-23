from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.timezone import now

from .models import GroupMessage


@receiver(post_save, sender=GroupMessage)
def update_group_timestamp(sender, instance, **kwargs):
    instance.group.updated_at = now()  # Update the `updated_at` field
    instance.group.save()
