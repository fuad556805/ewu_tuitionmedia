import os
from django.core.management.base import BaseCommand
from accounts.models import User, Notification
from posts.models import Post
from tuitions.models import TuitionRequest, Tuition


class Command(BaseCommand):
    help = 'Seed demo data for TuitionMedia'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        # Demo tutor
        tutor, _ = User.objects.get_or_create(phone='01711111111', defaults=dict(
            username='01711111111', password='!unusable',
            first_name='Tanvir', last_name='Ahmed',
            role='tutor', location='Dhanmondi, Dhaka',
            subjects='Physics, Math, Chemistry',
            university='BUET', department='EEE',
            gender='male', profile_approved=True,
        ))
        if _:
            tutor.set_password('demo123')
        # always ensure profile image is assigned if the file exists
        if not tutor.profile_image:
            profile_file = 'profiles/Screenshot_2025-11-25_184224.png'
            id_file      = 'id_docs/ewulogo.png'
            from django.conf import settings
            if os.path.exists(os.path.join(settings.MEDIA_ROOT, profile_file)):
                tutor.profile_image = profile_file
            if os.path.exists(os.path.join(settings.MEDIA_ROOT, id_file)):
                tutor.id_image = id_file
        tutor.profile_approved = True
        tutor.save()
        self.stdout.write(f'  Tutor ready: 01711111111 / demo123')

        # Demo student
        student, _ = User.objects.get_or_create(phone='01733333333', defaults=dict(
            username='01733333333', password='!unusable',
            first_name='Ayesha', last_name='Rahman',
            role='student', gender='female', profile_approved=True,
        ))
        if _:
            student.set_password('demo123')
        if not student.profile_image:
            profile_file = 'profiles/Screenshot_2025-11-25_184224.png'
            id_file      = 'id_docs/Screenshot_2025-09-06_121122.png'
            from django.conf import settings
            if os.path.exists(os.path.join(settings.MEDIA_ROOT, profile_file)):
                student.profile_image = profile_file
            if os.path.exists(os.path.join(settings.MEDIA_ROOT, id_file)):
                student.id_image = id_file
        student.profile_approved = True
        student.save()
        self.stdout.write(f'  Student ready: 01733333333 / demo123')

        # Demo tutor 2
        t2, _ = User.objects.get_or_create(phone='01722222222', defaults=dict(
            username='01722222222', password='!unusable',
            first_name='Sadia', last_name='Islam',
            role='tutor', location='Gulshan, Dhaka',
            subjects='English, Bengali, History',
            university='DU', department='English',
            gender='female', profile_approved=True,
        ))
        if _:
            t2.set_password('demo123')
            t2.save()

        # Demo post + request + tuition (only create once)
        if not Post.objects.filter(student=student).exists():
            post = Post.objects.create(
                student=student, subject='HSC Physics & Chemistry',
                location='Dhanmondi, Dhaka', budget=4000,
                classes='Class 11-12', schedule='Weekends 3-6 PM',
                status='active'
            )
            TuitionRequest.objects.create(
                tutor=tutor, student=student,
                post=post, subject=post.subject, status='accepted'
            )
            Tuition.objects.create(
                tutor=tutor, student=student,
                subject='HSC Physics & Chemistry',
                salary=5000, commission=1500,
                commission_status='pending', month='April 2026'
            )
            Notification.objects.create(user=tutor,   text='Ayesha accepted your tuition request!', notif_type='success')
            Notification.objects.create(user=student, text='Welcome to TuitionMedia! Account ready.', notif_type='success')

        self.stdout.write(self.style.SUCCESS('\nDemo data ready!'))
        self.stdout.write('  Tutor:   01711111111 / demo123')
        self.stdout.write('  Student: 01733333333 / demo123')
