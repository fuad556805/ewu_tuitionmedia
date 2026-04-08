from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='accounts.Notification')
def send_push_on_notification(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from accounts.push_utils import send_push_notification
        send_push_notification(
            user=instance.user,
            title='TuitionMedia',
            body=instance.text,
            url='/notifications/',
        )
    except Exception:
        pass
