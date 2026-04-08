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
                Notification.objects.create(user=admin, text=f"New post by {request.user.get_full_name()}: {post.subject}", notif_type='warn')
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
                Notification.objects.create(user=admin, text=f"Post edited by {request.user.get_full_name()}: {post.subject}", notif_type='warn')
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
    posts = Post.objects.filter(status='active').exclude(student=request.user)
    return render(request, 'posts/browse_posts.html', {'posts': posts})


@login_required
def browse_tutors(request):
    """For students to browse tutors"""
    tutors = User.objects.filter(role='tutor', banned=False, profile_approved=True)
    return render(request, 'posts/browse_tutors.html', {'tutors': tutors})
