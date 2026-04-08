from rest_framework import serializers
from .models import Message, ChatRequest


class MessageSerializer(serializers.ModelSerializer):
    sender_name   = serializers.CharField(source='sender.get_full_name', read_only=True)
    receiver_name = serializers.CharField(source='receiver.get_full_name', read_only=True)

    class Meta:
        model  = Message
        fields = ['id', 'sender', 'sender_name', 'receiver', 'receiver_name', 'text', 'read', 'created_at']
        read_only_fields = ['id', 'sender', 'sender_name', 'receiver_name', 'read', 'created_at']


class SendMessageSerializer(serializers.Serializer):
    receiver_id = serializers.IntegerField()
    text        = serializers.CharField(max_length=2000)

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        return value.strip()


class ChatRequestSerializer(serializers.ModelSerializer):
    sender_name   = serializers.CharField(source='sender.get_full_name', read_only=True)
    receiver_name = serializers.CharField(source='receiver.get_full_name', read_only=True)

    class Meta:
        model  = ChatRequest
        fields = ['id', 'sender', 'sender_name', 'receiver', 'receiver_name', 'status', 'created_at']
        read_only_fields = fields
