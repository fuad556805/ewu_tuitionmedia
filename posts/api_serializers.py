from rest_framework import serializers
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)

    class Meta:
        model  = Post
        fields = [
            'id', 'student', 'student_name', 'subject', 'location',
            'budget', 'classes', 'schedule', 'details',
            'status', 'request_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'student', 'student_name', 'status', 'request_count', 'created_at', 'updated_at']


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Post
        fields = ['subject', 'location', 'budget', 'classes', 'schedule', 'details']

    def validate_budget(self, value):
        if value <= 0:
            raise serializers.ValidationError("Budget must be a positive number.")
        return value


class PostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Post
        fields = ['subject', 'location', 'budget', 'classes', 'schedule', 'details']

    def validate_budget(self, value):
        if value <= 0:
            raise serializers.ValidationError("Budget must be a positive number.")
        return value
