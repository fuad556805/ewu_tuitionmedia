from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User, Notification
from .models import Post
from .forms import PostForm


@login_required
def my_posts(request):
    posts = Post.objects.filter(student=request.user)
    form = PostForm()
    return render(request, 'posts/my_posts.html', {'posts': posts, 'form': form})


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.student = request.user
            post.status = 'pending_approval'
            post.save()
            # notify admins
            for admin in User.objects.filter(role='admin'):
                Notification.objects.create(user=admin, text=f"New post by {request.user.get_full_name()}: {post.subject}", notif_type='warn', link='/admin-panel/posts-approval/')
            messages.success(request, "Post submitted for admin approval!")
        else:
            messages.error(request, "Please fix the errors.")
    return redirect('my_posts')


@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk, student=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.status = 'pending_approval'
            post.save()
            for admin in User.objects.filter(role='admin'):
                Notification.objects.create(user=admin, text=f"Post edited by {request.user.get_full_name()}: {post.subject}", notif_type='warn', link='/admin-panel/posts-approval/')
            messages.success(request, "Post updated. Awaiting admin approval.")
            return redirect('my_posts')
    else:
        form = PostForm(instance=post)
    return render(request, 'posts/edit_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk, student=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Post deleted.")
    return redirect('my_posts')


@login_required
def browse_posts(request):
    """For tutors to browse active posts"""
    qs = Post.objects.filter(status='active').exclude(student=request.user)

    q        = request.GET.get('q', '').strip()
    location = request.GET.get('location', '').strip()
    budget   = request.GET.get('budget', '').strip()
    classes  = request.GET.get('classes', '').strip()

    if q:
        qs = qs.filter(subject__icontains=q)
    if location:
        qs = qs.filter(location__icontains=location)
    if budget:
        try:
            qs = qs.filter(budget__lte=int(budget))
        except ValueError:
            pass
    if classes:
        qs = qs.filter(classes__icontains=classes)

    return render(request, 'posts/browse_posts.html', {
        'posts': qs,
        'q': q,
        'location': location,
        'budget': budget,
        'classes': classes,
        'total': Post.objects.filter(status='active').exclude(student=request.user).count(),
    })


@login_required
def browse_tutors(request):
    """For students to browse tutors"""
    qs = User.objects.filter(role='tutor', banned=False, profile_approved=True)

    q        = request.GET.get('q', '').strip()
    subject  = request.GET.get('subject', '').strip()
    location = request.GET.get('location', '').strip()
    gender   = request.GET.get('gender', '').strip()

    if q:
        qs = qs.filter(first_name__icontains=q) | qs.filter(last_name__icontains=q) | qs.filter(university__icontains=q) | qs.filter(college__icontains=q)
        qs = qs.distinct()
    if subject:
        qs = qs.filter(subjects__icontains=subject)
    if location:
        qs = qs.filter(location__icontains=location)
    if gender:
        qs = qs.filter(gender=gender)

    return render(request, 'posts/browse_tutors.html', {
        'tutors': qs,
        'q': q,
        'subject': subject,
        'location': location,
        'gender': gender,
        'total': User.objects.filter(role='tutor', banned=False, profile_approved=True).count(),
    })
