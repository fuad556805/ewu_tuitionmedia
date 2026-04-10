import logging

from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Notification, User
from .models import Message, ChatRequest
from .api_serializers import MessageSerializer, SendMessageSerializer, ChatRequestSerializer

logger = logging.getLogger(__name__)


def _chat_allowed(user1, user2):
    """Check if a ChatRequest exists and is accepted between the two users."""
    return ChatRequest.objects.filter(
        Q(sender=user1, receiver=user2) | Q(sender=user2, receiver=user1),
        status='accepted'
    ).exists()


class SendMessageView(APIView):
    """
    POST /api/chat/send/
    Body: { receiver_id, text }
    Sends a message. Requires an accepted ChatRequest (admin users are exempt).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = SendMessageSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        receiver_id = ser.validated_data['receiver_id']
        text        = ser.validated_data['text']

        try:
            receiver = User.objects.get(pk=receiver_id)
        except User.DoesNotExist:
            return Response({'error': 'Receiver not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.pk == receiver.pk:
            return Response({'error': 'You cannot message yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.role != 'admin' and receiver.role != 'admin':
            if not _chat_allowed(request.user, receiver):
                return Response(
                    {'error': 'Chat not allowed. A chat request must be accepted first.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        msg = Message.objects.create(sender=request.user, receiver=receiver, text=text)

        Notification.objects.create(
            user=receiver,
            text=f"New message from {request.user.get_full_name()}",
            notif_type='info',
            link='/chat/'
        )

        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)


class MessagesView(APIView):
    """
    GET /api/chat/messages/?with=<user_id>&after=<message_id>
    Returns messages between the authenticated user and the given user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        other_id = request.query_params.get('with')
        after_id = request.query_params.get('after', 0)

        if not other_id:
            return Response({'error': "'with' query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            other = User.objects.get(pk=other_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role != 'admin' and other.role != 'admin':
            if not _chat_allowed(request.user, other):
                return Response({'error': 'Chat not allowed.', 'messages': []}, status=status.HTTP_403_FORBIDDEN)

        msgs = Message.objects.filter(
            Q(sender=request.user, receiver=other) | Q(sender=other, receiver=request.user),
            pk__gt=int(after_id)
        ).select_related('sender', 'receiver')

        msgs.filter(receiver=request.user, read=False).update(read=True)

        return Response({'messages': MessageSerializer(msgs, many=True).data})


class InboxSummaryView(APIView):
    """
    GET /api/chat/inbox/
    Returns a list of users the authenticated user has active chats with.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        me = request.user

        if me.role == 'admin':
            contacts = User.objects.exclude(pk=me.pk).values(
                'id', 'first_name', 'last_name', 'role', 'profile_image'
            )
        else:
            contacts = User.objects.filter(
                Q(chat_sent_requests__receiver=me, chat_sent_requests__status='accepted') |
                Q(chat_received_requests__sender=me, chat_received_requests__status='accepted')
            ).distinct().values('id', 'first_name', 'last_name', 'role', 'profile_image')

        return Response({'contacts': list(contacts)})


class ChatRequestListView(APIView):
    """
    GET /api/chat/requests/ — list pending incoming chat requests.
    POST /api/chat/requests/ — send a chat request to another user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reqs = ChatRequest.objects.filter(receiver=request.user, status='pending').select_related('sender')
        return Response(ChatRequestSerializer(reqs, many=True).data)

    def post(self, request):
        receiver_id = request.data.get('receiver_id')
        if not receiver_id:
            return Response({'error': 'receiver_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            receiver = User.objects.get(pk=receiver_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.pk == receiver.pk:
            return Response({'error': 'Cannot send a chat request to yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        req, created = ChatRequest.objects.get_or_create(
            sender=request.user, receiver=receiver,
            defaults={'status': 'pending'}
        )

        if not created:
            return Response({'error': f'Chat request already exists (status: {req.status}).'}, status=status.HTTP_409_CONFLICT)

        Notification.objects.create(
            user=receiver,
            text=f"{request.user.get_full_name()} sent you a chat request.",
            notif_type='info',
            link='/chat/'
        )

        return Response(ChatRequestSerializer(req).data, status=status.HTTP_201_CREATED)


class ChatRequestRespondView(APIView):
    """
    POST /api/chat/requests/<pk>/respond/
    Body: { action: "accept" | "reject" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            req = ChatRequest.objects.get(pk=pk, receiver=request.user)
        except ChatRequest.DoesNotExist:
            return Response({'error': 'Chat request not found.'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')
        if action not in ('accept', 'reject'):
            return Response({'error': "action must be 'accept' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)

        req.status = 'accepted' if action == 'accept' else 'rejected'
        req.save(update_fields=['status'])

        Notification.objects.create(
            user=req.sender,
            text=f"{request.user.get_full_name()} {req.status} your chat request.",
            notif_type='success' if req.status == 'accepted' else 'danger',
            link='/chat/'
        )

        return Response(ChatRequestSerializer(req).data)
