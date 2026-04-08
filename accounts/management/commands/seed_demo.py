from django.core.management.base import BaseCommand
from accounts.models import User, Notification
from posts.models import Post
from tuitions.models import TuitionRequest, Tuition


class Command(BaseCommand):
    help = 'Seed demo data for TuitionMedia'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        # Admin
        if not User.objects.filter(phone='01000000000').exists():
            admin = User.objects.create_superuser(
                username='admin', phone='01000000000',
                password='admin123', email='admin@tuitionmedia.com',
                first_name='Super', last_name='Admin', role='admin'
            )
            self.stdout.write(f'  Created admin: 01000000000 / admin123')

        # Demo tutor
        if not User.objects.filter(phone='01711111111').exists():
            tutor = User.objects.create_user(
                username='01711111111', phone='01711111111',
                password='demo123', first_name='Tanvir', last_name='Ahmed',
                role='tutor', education='BUET - EEE',
                location='Dhanmondi, Dhaka',
                subjects='Physics, Math, Chemistry'
            )
            self.stdout.write(f'  Created tutor: 01711111111 / demo123')
        else:
            tutor = User.objects.get(phone='01711111111')

        # Demo student
        if not User.objects.filter(phone='01733333333').exists():
            student = User.objects.create_user(
                username='01733333333', phone='01733333333',
                password='demo123', first_name='Ayesha', last_name='Rahman',
                role='student'
            )
            self.stdout.write(f'  Created student: 01733333333 / demo123')
        else:
            student = User.objects.get(phone='01733333333')

        # Demo tutor 2
        if not User.objects.filter(phone='01722222222').exists():
            User.objects.create_user(
                username='01722222222', phone='01722222222',
                password='demo123', first_name='Sadia', last_name='Islam',
                role='tutor', education='DU - English',
                location='Gulshan, Dhaka', subjects='English, Bengali, History'
            )

        # Demo post
        if not Post.objects.filter(student=student).exists():
            post = Post.objects.create(
                student=student, subject='HSC Physics & Chemistry',
                location='Dhanmondi, Dhaka', budget=4000,
                classes='Class 11-12', schedule='Weekends 3-6 PM',
                status='active'
            )

            # Demo request
            req = TuitionRequest.objects.create(
                tutor=tutor, student=student,
                post=post, subject=post.subject, status='accepted'
            )

            # Demo tuition
            Tuition.objects.create(
                tutor=tutor, student=student,
                subject='HSC Physics & Chemistry',
                salary=5000, commission=1500,
                commission_status='pending', month='April 2026'
            )

            # Notifications
            Notification.objects.create(user=tutor, text='Ayesha accepted your tuition request!', notif_type='success')
            Notification.objects.create(user=student, text='Welcome to TuitionMedia! Account ready.', notif_type='success')

        self.stdout.write(self.style.SUCCESS('\nDemo data seeded successfully!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  Admin:   01000000000 / admin123')
        self.stdout.write('  Tutor:   01711111111 / demo123')
        self.stdout.write('  Student: 01733333333 / demo123')
