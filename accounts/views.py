from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import User, Notification
from tuitions.models import Tuition

from django.http import HttpResponse
from django.contrib.auth import get_user_model
import os

def create_admin(request):
    User = get_user_model()

    phone = os.environ.get("ADMIN_PHONE")
    password = os.environ.get("ADMIN_PASSWORD")

    # ❗ safety check
    if not phone or not password:
        return HttpResponse("Env variable missing")

    if not User.objects.filter(phone=phone).exists():
        User.objects.create_superuser(
            username=phone,
            phone=phone,
            password=password,
            role="admin"
        )
        return HttpResponse("Admin created")

    return HttpResponse("Admin already exists")

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    stats = [
        {'val': '1,240+', 'label': 'Active Tutors'},
        {'val': '8,900+', 'label': 'Students Matched'},
        {'val': '3,200+', 'label': 'Monthly Tuitions'},
        {'val': '12+',    'label': 'Cities Covered'},
    ]
    return render(request, 'accounts/landing.html', {'stats': stats})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = ''
    if request.method == 'POST':
        phone      = request.POST.get('phone', '').strip()
        password   = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        role       = request.POST.get('role', 'student')
        if not phone or not password or not first_name:
            error = 'First name, phone, and password are required.'
        elif User.objects.filter(phone=phone).exists():
            error = 'Phone already registered. Please log in.'
        else:
            user = User.objects.create_user(
                username=phone, phone=phone, password=password,
                first_name=first_name, last_name=last_name, role=role
            )
            Notification.objects.create(
                user=user,
                text='Welcome to TuitionMedia! Account created successfully.',
                notif_type='success'
            )
            login(request, user)
            return redirect('dashboard')
    return render(request, 'accounts/signup.html', {'error': error})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = ''
    if request.method == 'POST':
        phone    = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            User.objects.get(phone=phone)
            user = authenticate(request, username=phone, password=password)
            if user:
                if user.banned:
                    error = 'Your account has been banned. Contact support.'
                else:
                    login(request, user)
                    if user.role == 'admin':
                        return redirect('admin_panel:overview')
                    return redirect('dashboard')
            else:
                error = 'Wrong password.'
        except User.DoesNotExist:
            error = 'Phone number not registered.'
    return render(request, 'accounts/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('landing')


def forgot_password(request):
    from accounts.services.otp_service import send_otp as svc_send_otp, verify_otp as svc_verify_otp, OTPError
    from accounts.utils.sms_sender import send_otp_sms
    from django.conf import settings as dj_settings

    step = request.session.get('reset_step', 1)
    ctx  = {'step': step}
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'send_otp':
            phone = request.POST.get('phone', '').strip()
            if not User.objects.filter(phone=phone).exists():
                ctx.update({'step': 1, 'error': 'Phone number not registered.'})
                return render(request, 'accounts/forgot_password.html', ctx)
            try:
                _, raw_otp = svc_send_otp(phone, send_otp_sms)
            except OTPError as e:
                ctx.update({'step': 1, 'error': e.message})
                return render(request, 'accounts/forgot_password.html', ctx)
            request.session['reset_phone'] = phone
            request.session['reset_step']  = 2
            dev_otp = raw_otp if (dj_settings.DEBUG and getattr(dj_settings, 'SMS_BACKEND', '') == 'console') else None
            ctx.update({'step': 2, 'otp_demo': dev_otp})
        elif action == 'verify_otp':
            phone   = request.session.get('reset_phone', '')
            entered = request.POST.get('otp', '').strip()
            try:
                svc_verify_otp(phone, entered)
                request.session['reset_step'] = 3
                ctx['step'] = 3
            except OTPError as e:
                ctx.update({'step': 2, 'error': e.message})
        elif action == 'reset_password':
            new_pass = request.POST.get('new_password', '')
            confirm  = request.POST.get('confirm_password', '')
            if len(new_pass) < 6:
                ctx.update({'step': 3, 'error': 'Password must be at least 6 characters.'})
                return render(request, 'accounts/forgot_password.html', ctx)
            if new_pass != confirm:
                ctx.update({'step': 3, 'error': "Passwords don't match."})
                return render(request, 'accounts/forgot_password.html', ctx)
            phone = request.session.get('reset_phone')
            user  = User.objects.filter(phone=phone).first()
            if user:
                user.set_password(new_pass)
                user.save()
                Notification.objects.create(
                    user=user, text='Your password was reset successfully.', notif_type='success'
                )
            for k in ['reset_step', 'reset_otp', 'reset_phone']:
                request.session.pop(k, None)
            ctx['step'] = 4
    return render(request, 'accounts/forgot_password.html', ctx)


@login_required
def dashboard(request):
    user = request.user
    if user.role == 'admin':
        return redirect('admin_panel:overview')
    elif user.role == 'student':
        from posts.models import Post
        from tuitions.models import TuitionRequest
        ctx = {
            'active_posts':      Post.objects.filter(student=user, status='active').count(),
            'pending_requests':  TuitionRequest.objects.filter(student=user, status='pending').count(),
            'active_tuitions':   Tuition.objects.filter(student=user, status='active').count(),
        }
        return render(request, 'accounts/student_dashboard.html', ctx)
    else:
        from tuitions.models import TuitionRequest
        active = Tuition.objects.filter(tutor=user, status='active')
        pending_commission = sum(
            t.commission for t in active
            if t.commission_status == 'pending' and t.salary > 0
        )
        ctx = {
            'active_tuitions':   active.count(),
            'pending_commission': pending_commission,
            'student_reqs':      TuitionRequest.objects.filter(
                tutor=user, status='pending', post__isnull=True
            ),
        }
        return render(request, 'accounts/tutor_dashboard.html', ctx)


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        # Text fields — both roles
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name  = request.POST.get('last_name',  user.last_name).strip()
        user.phone      = request.POST.get('phone',      user.phone).strip()
        user.gender     = request.POST.get('gender',     user.gender)

        # Tutor extra fields
        if user.role == 'tutor':
            user.school     = request.POST.get('school',     user.school).strip()
            user.college    = request.POST.get('college',    user.college).strip()
            user.university = request.POST.get('university', user.university).strip()
            user.department = request.POST.get('department', user.department).strip()
            user.subjects   = request.POST.get('subjects',   user.subjects).strip()
            user.location   = request.POST.get('location',   user.location).strip()

        # Profile image upload
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']

        # ID document upload
        if 'id_image' in request.FILES:
            user.id_image = request.FILES['id_image']

        user.profile_approved = False  # needs admin approval
        user.save()

        # Notify admins
        for admin in User.objects.filter(role='admin'):
            Notification.objects.create(
                user=admin,
                text=f'{user.get_full_name()} updated their profile (needs approval)',
                notif_type='warn'
            )
        messages.success(request, 'Profile updated. Awaiting admin approval.')
        return redirect('profile')

    tuitions = (
        Tuition.objects.filter(student=user)
        if user.role == 'student'
        else Tuition.objects.filter(tutor=user)
    )
    return render(request, 'accounts/profile.html', {'tuitions': tuitions})


@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user)
    return render(request, 'accounts/notifications.html', {'notifs': notifs})


@login_required
def mark_notif_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.read = True
    n.save()
    return JsonResponse({'ok': True})


@login_required
def set_theme(request):
    if request.method == 'POST':
        theme = request.POST.get('theme', 'dark')
        if theme in ['dark', 'ocean', 'sunset']:
            request.user.theme = theme
            request.user.save(update_fields=['theme'])
    return JsonResponse({'ok': True})
