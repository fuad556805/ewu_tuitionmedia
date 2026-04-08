from django.conf import settings as django_settings


def vapid_key(request):
    return {
        'VAPID_PUBLIC_KEY': getattr(django_settings, 'VAPID_PUBLIC_KEY', ''),
    }
