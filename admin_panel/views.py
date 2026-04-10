from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.models import User, Notification
from posts.models import Post
from tuitions.models import Tuition, TuitionRequest
from chat.models import Message

# ------------------------------
# Decorator
# ------------------------------
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ------------------------------
# Dashboard
# ------------------------------
@admin_required
def overview(request):
    ctx = {
        'total_users': User.objects.exclude(role='admin').count(),
        'pending_profiles': User.objects.filter(profile_approved=False).count(),
        'pending_posts': Post.objects.filter(status='pending_approval').count(),
        'active_tuitions': Tuition.objects.filter(status='active').count(),
        'pending_commission': sum(
            t.commission for t in Tuition.objects.filter(
                commission_status='pending', salary__gt=0
            )
        ),
        'total_posts': Post.objects.count(),
        'total_requests': TuitionRequest.objects.count(),
        'admin_notifs': Notification.objects.filter(user=request.user).order_by('-created_at')[:10],
    }
    return render(request, 'admin_panel/overview.html', ctx)


# ------------------------------
# Profile Approvals
# ------------------------------
@admin_required
def profile_approvals(request):
    search = request.GET.get('q', '').strip()
    pending_qs = User.objects.filter(profile_approved=False)
    approved_qs = User.objects.filter(profile_approved=True).exclude(role='admin')

    if search:
        pending_qs = pending_qs.filter(
            Q(first_name__icontains=search) | Q(last_name__icontains=search)
        )
        approved_qs = approved_qs.filter(
            Q(first_name__icontains=search) | Q(last_name__icontains=search)
        )

    return render(request, 'admin_panel/profile_approvals.html', {
        'pending': pending_qs,
        'approved': approved_qs,
        'search': search,
    })


@admin_required
def approve_profile(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    action = request.POST.get('action')

    if action == 'approve':
        user.profile_approved = True
        user.save()
        Notification.objects.create(user=user, text="Profile approved!", notif_type='success', link='/profile/')
    else:
        Notification.objects.create(user=user, text="Profile rejected!", notif_type='danger', link='/profile/')

    return redirect('admin_panel:profile_approvals')


# ------------------------------
# Posts Approval
# ------------------------------
@admin_required
def posts_approval(request):
    search = request.GET.get('q', '').strip()
    pending_qs = Post.objects.filter(status='pending_approval').select_related('student')
    approved_qs = Post.objects.filter(status='active').select_related('student')

    if search:
        pending_qs = pending_qs.filter(
            Q(student__first_name__icontains=search) | Q(student__last_name__icontains=search)
        )
        approved_qs = approved_qs.filter(
            Q(student__first_name__icontains=search) | Q(student__last_name__icontains=search)
        )

    return render(request, 'admin_panel/posts_approval.html', {
        'pending': pending_qs,
        'approved': approved_qs,
        'search': search,
    })


@admin_required
def approve_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    action = request.POST.get('action')

    if action == 'approve':
        post.status = 'active'
    else:
        post.status = 'rejected'

    post.save()
    return redirect('admin_panel:posts_approval')


# ------------------------------
# All Posts (Admin - Delete)
# ------------------------------
@admin_required
def all_posts(request):
    posts = Post.objects.select_related('student').order_by('-created_at')
    return render(request, 'admin_panel/all_posts.html', {'posts': posts})


@admin_required
def delete_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=post_id)
        post.delete()
    next_url = request.POST.get('next', '')
    if next_url == 'posts_approval':
        return redirect('admin_panel:posts_approval')
    return redirect('admin_panel:all_posts')


# ------------------------------
# Requests
# ------------------------------
@admin_required
def all_requests(request):
    reqs = TuitionRequest.objects.select_related('tutor', 'student', 'post')
    return render(request, 'admin_panel/all_requests.html', {'reqs': reqs})


# ------------------------------
# Payments (FINAL FIXED)
# ------------------------------
@admin_required
def payments(request):
    all_tuitions = Tuition.objects.select_related('tutor', 'student')

    no_salary = all_tuitions.filter(salary=0)
    proof_uploaded = all_tuitions.filter(commission_status='proof_uploaded')
    pending_no_proof = all_tuitions.filter(commission_status='pending', salary__gt=0)
    paid = all_tuitions.filter(commission_status='paid')

    all_payments = all_tuitions.filter(salary__gt=0)
    total_commission = sum(t.commission for t in all_payments)
    confirmed_total = sum(t.commission for t in paid)
    pending_total = sum(t.commission for t in pending_no_proof) + sum(t.commission for t in proof_uploaded)
    active_count = all_tuitions.filter(status='active').count()

    return render(request, 'admin_panel/payments.html', {
        'no_salary': no_salary,
        'proof_uploaded': proof_uploaded,
        'pending_no_proof': pending_no_proof,
        'paid': paid,
        'all_payments': all_payments,
        'total_commission': total_commission,
        'confirmed_total': confirmed_total,
        'pending_total': pending_total,
        'active_count': active_count,
    })


@admin_required
def set_salary(request):
    if request.method == 'POST':
        tuition = get_object_or_404(Tuition, pk=request.POST.get('tuition_id'))
        amount = int(request.POST.get('amount', 0))

        tuition.salary = amount
        tuition.commission = round(amount * 0.3)
        tuition.commission_status = 'pending'
        tuition.save()

    return redirect('admin_panel:payments')


@admin_required
def confirm_payment(request, tuition_id):
    tuition = get_object_or_404(Tuition, pk=tuition_id)
    tuition.commission_status = 'paid'
    tuition.save()

    return redirect('admin_panel:payments')


# ------------------------------
# Users
# ------------------------------
@admin_required
def all_users(request):
    users = User.objects.exclude(role='admin')
    return render(request, 'admin_panel/all_users.html', {'users': users})


@admin_required
def toggle_ban(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.banned = not user.banned
    user.save()
    return redirect('admin_panel:all_users')


# ------------------------------
# User Profile
# ------------------------------
@admin_required
def user_profile(request, user_id):
    viewed_user = get_object_or_404(User, pk=user_id)

    tuitions = Tuition.objects.filter(
        student=viewed_user if viewed_user.role == 'student' else None,
        tutor=viewed_user if viewed_user.role == 'tutor' else None
    )

    return render(request, 'admin_panel/user_profile.html', {
        'viewed_user': viewed_user,
        'tuitions': tuitions
    })


# ------------------------------
# Messaging
# ------------------------------
@admin_required
def admin_inbox(request):
    from django.db.models import Q
    contacts = User.objects.exclude(id=request.user.id)

    active_user = None
    messages_list = []

    with_id = request.GET.get('with')
    if with_id:
        active_user = get_object_or_404(User, pk=with_id)
        messages_list = Message.objects.filter(
            Q(sender=request.user, receiver=active_user) |
            Q(sender=active_user, receiver=request.user)
        ).order_by('created_at')
        messages_list.filter(receiver=request.user, read=False).update(read=True)

    return render(request, 'admin_panel/admin_inbox.html', {
        'contacts': contacts,
        'active_user': active_user,
        'messages_list': messages_list,
    })


@admin_required
def admin_send_message(request):
    if request.method == 'POST':
        receiver = get_object_or_404(User, pk=request.POST.get('receiver_id'))
        text = request.POST.get('text', '').strip()
        if text:
            Message.objects.create(
                sender=request.user,
                receiver=receiver,
                text=text
            )
        return redirect(f'/admin-panel/inbox/?with={receiver.pk}')

    return redirect('admin_panel:admin_inbox')
    
