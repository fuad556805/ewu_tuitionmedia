import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create a superuser with username, email, phone, and password from environment variables"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # Environment Variables
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@admin.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        phone = os.environ.get('DJANGO_SUPERUSER_PHONE', '01700000000')

        if not password:
            self.stdout.write('❌ No password set! Please set DJANGO_SUPERUSER_PASSWORD in .env')
            return

        # Check if user exists
        if not User.objects.filter(username=username).exists():
            u = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            u.phone = phone   # ✅ from .env
            u.role = 'admin'  # custom role
            u.save()
            self.stdout.write(f'✅ Admin created! Username: {username}, Phone: {phone}')
        else:
            self.stdout.write('ℹ️ Admin already exists.')