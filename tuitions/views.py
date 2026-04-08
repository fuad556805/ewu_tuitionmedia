from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from accounts.models import User, Notification
from .models import TuitionRequest, Tuition
from posts.models import Post


@login_required
def send_request(request, tutor_id):
    """Student sends direct request to tutor"""
    tutor = get_object_or_404(User, pk=tutor_id, role='tutor')
    if request.method == 'POST':
        subject = request.POST.get('subject', tutor.subjects or 'General Tuition')
        obj, created = TuitionRequest.objects.get_or_create(
            tutor=tutor, student=request.user, post=None,
            defaults={'subject': subject, 'status': 'pending'}
        )
        if created:
            Notification.objects.create(
                user=tutor,
                text=f"{request.user.get_full_name()} sent you a tuition request!",
                notif_type='accent'
            )
            messages.success(request, f"Request sent to {tutor.get_full_name()}!")
        else:
            messages.info(request, "Request already sent.")
    return redirect('browse_tutors')


@login_required
def apply_to_post(request, post_id):
    """Tutor applies to a student post"""
    post = get_object_or_404(Post, pk=post_id, status='active')
    if request.method == 'POST':
        obj, created = TuitionRequest.objects.get_or_create(
            tutor=request.user, student=post.student, post=post,
            defaults={'subject': post.subject, 'status': 'pending'}
        )
        if created:
            post.request_count += 1
            post.save(update_fields=['request_count'])
            Notification.objects.create(
                user=post.student,
                text=f"{request.user.get_full_name()} applied to your post: {post.subject}",
                notif_type='accent'
            )
            messages.success(request, f"Applied to {post.subject}!")
        else:
            messages.info(request, "Already applied.")
    return redirect('browse_posts')


@login_required
def accept_request(request, req_id):
    """Student accepts a tutor request"""
    req = get_object_or_404(TuitionRequest, pk=req_id, student=request.user, status='pending')
    if request.method == 'POST':
        req.status = 'accepted'
        req.save()
        month = timezone.now().strftime('%B %Y')
        Tuition.objects.create(
            tutor=req.tutor, student=request.user,
            subject=req.subject, month=month,
            salary=0, commission=0, commission_status='pending'
        )
        Notification.objects.create(
            user=req.tutor,
            text=f"{request.user.get_full_name()} accepted your request for {req.subject}!",
            notif_type='success'
        )
        # notify admins
        for admin in User.objects.filter(role='admin'):
            Notification.objects.create(
                user=admin,
                text=f"New tuition confirmed: {req.tutor.get_full_name()} + {request.user.get_full_name()}",
                notif_type='accent'
            )
        messages.success(request, "Request accepted! Tuition started.")
    return redirect('dashboard')


@login_required
def reject_request(request, req_id):
    req = get_object_or_404(TuitionRequest, pk=req_id, student=request.user, status='pending')
    if request.method == 'POST':
        req.status = 'rejected'
        req.save()
        Notification.objects.create(
            user=req.tutor,
            text=f"{request.user.get_full_name()} rejected your request for {req.subject}.",
            notif_type='danger'
        )
        messages.warning(request, "Request rejected.")
    return redirect('dashboard')


@login_required
def my_tuitions(request):
    """Tutor's tuition list"""
    tuitions = Tuition.objects.filter(tutor=request.user)
    return render(request, 'tuitions/my_tuitions.html', {'tuitions': tuitions})


@login_required
def payments(request):
    """Tutor payment & commission page"""
    tuitions = Tuition.objects.filter(tutor=request.user)
    pending = tuitions.filter(commission_status='pending', salary__gt=0)
    proof_uploaded = tuitions.filter(commission_status='proof_uploaded')
    paid = tuitions.filter(commission_status='paid')
    return render(request, 'tuitions/payments.html', {
        'pending': pending,
        'proof_uploaded': proof_uploaded,
        'paid': paid,
        'tuitions': tuitions,
    })


@login_required
def submit_proof(request, tuition_id):
    tuition = get_object_or_404(Tuition, pk=tuition_id, tutor=request.user)
    if request.method == 'POST':
        if 'proof_image' in request.FILES:
            tuition.proof_image = request.FILES['proof_image']
        tuition.commission_status = 'proof_uploaded'
        tuition.save()
        for admin in User.objects.filter(role='admin'):
            Notification.objects.create(
                user=admin,
                text=f"{request.user.get_full_name()} submitted commission proof for {tuition.student.get_full_name()} (BDT {tuition.commission})",
                notif_type='warn'
            )
        messages.success(request, "Proof submitted! Admin will verify.")
    return redirect('payments')
