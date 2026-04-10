from django.conf import settings as django_settings


def vapid_key(request):
    return {
        'VAPID_PUBLIC_KEY': getattr(django_settings, 'VAPID_PUBLIC_KEY', ''),
    }


def unread_notif_count(request):
    if request.user.is_authenticated:
        count = request.user.notifications.filter(read=False).count()
        return {'unread_notif_count': count}
    return {'unread_notif_count': 0}
