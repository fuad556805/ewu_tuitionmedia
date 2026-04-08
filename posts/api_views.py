import logging

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Notification, User
from .models import Post
from .api_serializers import PostCreateSerializer, PostSerializer, PostUpdateSerializer

logger = logging.getLogger(__name__)


class TuitionListView(APIView):
    """
    GET /api/tuition/list/
    Public list of active tuition posts. Supports ?subject= and ?location= filters.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Post.objects.filter(status='active').select_related('student')

        subject  = request.query_params.get('subject')
        location = request.query_params.get('location')
        if subject:
            qs = qs.filter(subject__icontains=subject)
        if location:
            qs = qs.filter(location__icontains=location)

        return Response(PostSerializer(qs, many=True).data)


class TuitionCreateView(APIView):
    """
    POST /api/tuition/create/
    Students only. Creates a tuition post (sent to admin for approval).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'student':
            return Response({'error': 'Only students can create tuition posts.'}, status=status.HTTP_403_FORBIDDEN)

        ser = PostCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        post = ser.save(student=request.user, status='pending_approval')

        for admin in User.objects.filter(role='admin'):
            Notification.objects.create(
                user=admin,
                text=f"New post by {request.user.get_full_name()}: {post.subject}",
                notif_type='warn',
            )

        logger.info("Post created: id=%s by user=%s", post.pk, request.user.pk)
        return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)


class TuitionUpdateView(APIView):
    """
    PUT /api/tuition/update/<pk>/
    Students can update their own posts (resets to pending_approval).
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        return self._update(request, pk)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial=False):
        if request.user.role != 'student':
            return Response({'error': 'Only students can update tuition posts.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            post = Post.objects.get(pk=pk, student=request.user)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        if post.status == 'closed':
            return Response({'error': 'Closed posts cannot be edited.'}, status=status.HTTP_400_BAD_REQUEST)

        ser = PostUpdateSerializer(post, data=request.data, partial=partial)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        post = ser.save(status='pending_approval')

        for admin in User.objects.filter(role='admin'):
            Notification.objects.create(
                user=admin,
                text=f"Post edited by {request.user.get_full_name()}: {post.subject}",
                notif_type='warn',
            )

        return Response(PostSerializer(post).data)


class TuitionDetailView(APIView):
    """GET /api/tuition/<pk>/ — single post detail."""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        if post.status != 'active' and (not request.user.is_authenticated or (request.user.pk != post.student_id and request.user.role != 'admin')):
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(PostSerializer(post).data)


class MyPostsView(APIView):
    """GET /api/tuition/my/ — list the authenticated student's own posts."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'student':
            return Response({'error': 'Only students have posts.'}, status=status.HTTP_403_FORBIDDEN)
        posts = Post.objects.filter(student=request.user)
        return Response(PostSerializer(posts, many=True).data)


class TuitionDeleteView(APIView):
    """DELETE /api/tuition/<pk>/delete/ — owner can delete their post."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            post = Post.objects.get(pk=pk, student=request.user)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        post.delete()
        return Response({'message': 'Post deleted.'}, status=status.HTTP_204_NO_CONTENT)
