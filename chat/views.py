from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from accounts.models import User
from .models import Message, ChatRequest
from tuitions.models import TuitionRequest


def _is_connected(user_a, user_b):
    """Allow messaging if there's an accepted TuitionRequest, or if either party is an admin."""
    if user_a.role == 'admin' or user_b.role == 'admin':
        return True
    return TuitionRequest.objects.filter(
        Q(tutor=user_a, student=user_b) | Q(tutor=user_b, student=user_a),
        status='accepted'
    ).exists()


@login_required
def inbox(request):
    me = request.user

    if me.role == 'admin':
        contacts = User.objects.exclude(id=me.id)
    else:
        # Users connected via accepted TuitionRequest
        tuition_contacts = User.objects.filter(
            Q(sent_requests__student=me, sent_requests__status='accepted') |
            Q(received_requests__tutor=me, received_requests__status='accepted')
        ).distinct()

        # Admins who have messaged this user
        admin_contacts = User.objects.filter(
            role='admin'
        ).filter(
            Q(sent_messages__receiver=me) | Q(received_messages__sender=me)
        ).distinct()

        contacts = (tuition_contacts | admin_contacts).distinct()

    active_id = request.GET.get('with')
    active_user = None
    messages_list = []

    if active_id:
        active_user = get_object_or_404(User, pk=active_id)

        if not _is_connected(me, active_user):
            return redirect('inbox')

        messages_list = Message.objects.filter(
            Q(sender=me, receiver=active_user) | Q(sender=active_user, receiver=me)
        )
        messages_list.filter(receiver=me, read=False).update(read=True)

    contact_ids = set(contacts.values_list('id', flat=True))

    return render(request, 'chat/inbox.html', {
        'contacts': contacts,
        'active_user': active_user,
        'messages_list': messages_list,
        'contact_ids': contact_ids,
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
                    'time': msg.created_at.strftime('%H:%M'),
                    'sender_id': request.user.id,
                })

        return redirect(f'/chat/?with={receiver_id}')

    return redirect('inbox')


@login_required
def get_messages(request, user_id):
    other = get_object_or_404(User, pk=user_id)

    if not _is_connected(request.user, other):
        return JsonResponse({'messages': []})

    after_id = request.GET.get('after', 0)
    msgs = Message.objects.filter(
        Q(sender=request.user, receiver=other) | Q(sender=other, receiver=request.user),
        id__gt=after_id
    )
    msgs.filter(receiver=request.user, read=False).update(read=True)

    data = [{
        'id': m.id,
        'text': m.text,
        'sender_id': m.sender_id,
        'time': m.created_at.strftime('%H:%M')
    } for m in msgs]

    return JsonResponse({'messages': data})
