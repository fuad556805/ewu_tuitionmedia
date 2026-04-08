import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@admin.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        
        if not password:
            self.stdout.write('No password set!')
            return
        
        if not User.objects.filter(username=username).exists():
            u = User.objects.create_superuser(username=username, email=email, password=password)
            u.role = 'admin'  
            u.save()
            self.stdout.write('✅ Admin created!')
        else:
            self.stdout.write('Admin already exists.')