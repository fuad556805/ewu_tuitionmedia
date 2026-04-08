import json
import base64
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_vapid_private_key():
    b64 = getattr(settings, 'VAPID_PRIVATE_KEY_B64', '')
    if not b64:
        return None
    padding = '=' * (4 - len(b64) % 4)
    return base64.urlsafe_b64decode(b64 + padding).decode()


def send_push_notification(user, title, body, url='/notifications/'):
    from accounts.models import PushSubscription
    from pywebpush import webpush, WebPushException

    private_key = _get_vapid_private_key()
    public_key  = getattr(settings, 'VAPID_PUBLIC_KEY', '')
    email       = getattr(settings, 'VAPID_CLAIMS_EMAIL', 'admin@tuitionmedia.com')

    if not private_key or not public_key:
        return

    subs = PushSubscription.objects.filter(user=user)
    dead = []

    for sub in subs:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=json.dumps({'title': title, 'body': body, 'url': url}),
                vapid_private_key=private_key,
                vapid_claims={'sub': f'mailto:{email}'},
            )
        except WebPushException as e:
            logger.warning("Push failed for sub %s: %s", sub.id, e)
            if '410' in str(e) or '404' in str(e):
                dead.append(sub.id)
        except Exception as e:
            logger.warning("Push error for sub %s: %s", sub.id, e)

    if dead:
        PushSubscription.objects.filter(id__in=dead).delete()
