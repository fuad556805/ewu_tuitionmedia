from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from accounts.models import User
from .models import Message, ChatRequest
from tuitions.models import TuitionRequest


def _is_connected(user_a, user_b):
    """Allow messaging if there's an accepted TuitionRequest, or if either party is admin."""
    if user_a.role == 'admin' or user_b.role == 'admin':
        return True
    return TuitionRequest.objects.filter(
        Q(tutor=user_a, student=user_b) | Q(tutor=user_b, student=user_a),
        status='accepted'
    ).exists()


def _get_contacts(me):
    if me.role == 'admin':
        return User.objects.exclude(id=me.id)
    tuition_contacts = User.objects.filter(
        Q(sent_requests__student=me, sent_requests__status='accepted') |
        Q(received_requests__tutor=me, received_requests__status='accepted')
    ).distinct()
    admin_contacts = User.objects.filter(
        role='admin'
    ).filter(
        Q(sent_messages__receiver=me) | Q(received_messages__sender=me)
    ).distinct()
    return (tuition_contacts | admin_contacts).distinct()


@login_required
def inbox(request):
    me = request.user
    contacts = _get_contacts(me)

    unread_counts = {}
    total_unread = 0
    for u in contacts:
        cnt = Message.objects.filter(sender=u, receiver=me, read=False).count()
        unread_counts[u.pk] = cnt
        total_unread += cnt

    contacts_data = [{'user': u, 'unread': unread_counts.get(u.pk, 0)} for u in contacts]

    return render(request, 'chat/inbox.html', {
        'contacts_data': contacts_data,
        'total_unread': total_unread,
        'with_id': request.GET.get('with', ''),
    })


@login_required
def send_message(request):
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        text = request.POST.get('text', '').strip()
        if receiver_id and text:
            receiver = get_object_or_404(User, pk=receiver_id)

            if not _is_connected(request.user, receiver):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'ok': False, 'error': 'You cannot message this user yet.'})
                return redirect('inbox')

            msg = Message.objects.create(sender=request.user, receiver=receiver, text=text)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': True,
                    'id': msg.id,
                    'text': msg.text,
                    'time': msg.created_at.strftime('%b %d · %H:%M'),
                    'sender_id': request.user.id,
                })

        return redirect(f'/chat/?with={receiver_id}')
    return redirect('inbox')


@login_required
def get_messages(request, user_id):
    """Lightweight polling endpoint: returns only new messages (after=id)."""
    other = get_object_or_404(User, pk=user_id)

    if not _is_connected(request.user, other):
        return JsonResponse({'messages': []})

    after_id = request.GET.get('after', 0)
    msgs = Message.objects.filter(
        Q(sender=request.user, receiver=other) | Q(sender=other, receiver=request.user),
        id__gt=after_id
    ).order_by('id')
    msgs.filter(receiver=request.user, read=False).update(read=True)

    data = [{
        'id': m.id,
        'text': m.text,
        'sender_id': m.sender_id,
        'time': m.created_at.strftime('%b %d · %H:%M'),
    } for m in msgs]

    return JsonResponse({'messages': data})


@login_required
def load_conversation(request, user_id):
    """Full conversation loader: returns user info + all messages for AJAX loading."""
    other = get_object_or_404(User, pk=user_id)
    me = request.user

    connected = _is_connected(me, other)

    if not connected:
        return JsonResponse({'ok': False, 'error': 'Not connected'}, status=403)

    msgs = Message.objects.filter(
        Q(sender=me, receiver=other) | Q(sender=other, receiver=me)
    ).order_by('id')
    msgs.filter(receiver=me, read=False).update(read=True)

    avatar_url = other.profile_image.url if other.profile_image else ''
    from django.urls import reverse
    try:
        profile_url = reverse('public_profile', args=[other.pk])
    except Exception:
        profile_url = '#'

    user_data = {
        'name': other.get_full_name(),
        'role': other.role,
        'avatar_url': avatar_url,
        'profile_url': profile_url,
    }

    msg_data = [{
        'id': m.id,
        'text': m.text,
        'sender_id': m.sender_id,
        'time': m.created_at.strftime('%b %d · %H:%M'),
    } for m in msgs]

    return JsonResponse({'ok': True, 'user': user_data, 'messages': msg_data})


@login_required
def unread_counts(request):
    """Returns per-contact unread message counts for sidebar badge polling."""
    me = request.user
    contacts = _get_contacts(me)
    counts = {}
    total = 0
    for u in contacts:
        cnt = Message.objects.filter(sender=u, receiver=me, read=False).count()
        if cnt:
            counts[str(u.pk)] = cnt
            total += cnt
    return JsonResponse({'counts': counts, 'total': total})
