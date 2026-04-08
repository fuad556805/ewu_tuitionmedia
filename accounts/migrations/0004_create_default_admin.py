from django.db import migrations
from django.contrib.auth.hashers import make_password


ADMIN_PHONE    = '01609227183'
ADMIN_USERNAME = 'fuad_admin'
ADMIN_EMAIL    = 'admin@tuitionmedia.com'
ADMIN_PASSWORD = 'fuad1234@'


def create_default_admin(apps, schema_editor):
    User = apps.get_model('accounts', 'User')

    hashed_password = make_password(ADMIN_PASSWORD)

    user, created = User.objects.get_or_create(
        phone=ADMIN_PHONE,
        defaults={
            'username':     ADMIN_USERNAME,
            'email':        ADMIN_EMAIL,
            'password':     hashed_password,
            'role':         'admin',
            'is_staff':     True,
            'is_superuser': True,
            'is_active':    True,
        }
    )

    if not created:
        user.password     = hashed_password
        user.username     = ADMIN_USERNAME
        user.email        = ADMIN_EMAIL
        user.role         = 'admin'
        user.is_staff     = True
        user.is_superuser = True
        user.is_active    = True
        user.save()


def reverse_admin(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_otpverification'),
    ]

    operations = [
        migrations.RunPython(create_default_admin, reverse_admin),
    ]
