from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from accounts.models import User
from .models import Message, ChatRequest


@login_required
def inbox(request):
    me = request.user

    if me.role == 'admin':
        # Admin sees all users
        contacts = User.objects.exclude(id=me.id)
        all_users = User.objects.exclude(id=me.id)
    else:
        # Only users with accepted ChatRequests
        contacts = User.objects.filter(
            Q(chat_sent_requests__receiver=me, chat_sent_requests__status='accepted') |
            Q(chat_received_requests__sender=me, chat_received_requests__status='accepted')
        ).distinct()

        # Users to apply chat with (profile approved and not admin)
        all_users = User.objects.filter(
            profile_approved=True
        ).exclude(id=me.id).exclude(role='admin')

    active_id = request.GET.get('with')
    active_user = None
    messages_list = []

    if active_id:
        active_user = get_object_or_404(User, pk=active_id)

        # Permission check for tutor/student
        if me.role != 'admin':
            is_allowed = ChatRequest.objects.filter(
                Q(sender=me, receiver=active_user, status='accepted') |
                Q(sender=active_user, receiver=me, status='accepted')
            ).exists()
            if not is_allowed:
                # If not accepted, redirect
                return redirect('inbox')

        # Load messages
        messages_list = Message.objects.filter(
            Q(sender=me, receiver=active_user) | Q(sender=active_user, receiver=me)
        )
        messages_list.filter(receiver=me, read=False).update(read=True)

    contact_ids = set(contacts.values_list('id', flat=True))

    return render(request, 'chat/inbox.html', {
        'contacts': contacts,
        'all_users': all_users,
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

            # Permission check for non-admin users
            if request.user.role != 'admin':
                is_allowed = ChatRequest.objects.filter(
                    Q(sender=request.user, receiver=receiver, status='accepted') |
                    Q(sender=receiver, receiver=request.user, status='accepted')
                ).exists()
                if not is_allowed:
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

    # Permission check
    if request.user.role != 'admin':
        is_allowed = ChatRequest.objects.filter(
            Q(sender=request.user, receiver=other, status='accepted') |
            Q(sender=other, receiver=request.user, status='accepted')
        ).exists()
        if not is_allowed:
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

