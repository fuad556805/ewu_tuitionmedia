import logging

from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Notification, OTPVerification
from accounts.services.otp_service import OTPError, send_otp, verify_otp
from accounts.utils.sms_sender import send_otp_sms
from .api_serializers import (
    ForgotPasswordSendSerializer,
    ForgotPasswordVerifySerializer,
    LoginSerializer,
    OTPStatusSerializer,
    ProfileUpdateSerializer,
    ResendOTPSerializer,
    SendOTPSerializer,
    UserProfileSerializer,
    VerifyOTPSerializer,
)

logger = logging.getLogger(__name__)
User   = get_user_model()


def _jwt_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access':  str(refresh.access_token),
        'refresh': str(refresh),
    }


# ── OTP Views ────────────────────────────────────────────────────────────────

class SendOTPView(APIView):
    """
    POST /api/auth/send-otp/
    Body: { phone }
    Sends OTP for new account signup.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        ser = SendOTPSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = ser.validated_data['phone']

        if User.objects.filter(phone=phone).exists():
            return Response(
                {'error': 'This phone number is already registered. Please log in.'},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            _, raw_otp = send_otp(phone, send_otp_sms)
        except OTPError as exc:
            return Response({'error': exc.message, 'code': exc.code}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        from django.conf import settings as dj_settings
        resp = {'message': f"OTP sent to {phone}. Valid for 2 minutes.", 'phone': phone}
        if dj_settings.DEBUG and getattr(dj_settings, 'SMS_BACKEND', '') == 'console':
            resp['dev_otp'] = raw_otp

        return Response(resp, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """
    POST /api/auth/verify-otp/
    Body: { phone, otp, first_name, last_name, password, role }
    Verifies OTP, creates account, returns JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        ser = VerifyOTPSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        data  = ser.validated_data
        phone = data['phone']
        otp   = data['otp']

        try:
            verify_otp(phone, otp)
        except OTPError as exc:
            code = exc.code
            http_status = {
                'brute_force': status.HTTP_429_TOO_MANY_REQUESTS,
                'not_found':   status.HTTP_404_NOT_FOUND,
                'expired':     status.HTTP_410_GONE,
                'invalid':     status.HTTP_401_UNAUTHORIZED,
            }.get(code, status.HTTP_400_BAD_REQUEST)
            return Response({'error': exc.message, 'code': code}, status=http_status)

        if User.objects.filter(phone=phone).exists():
            return Response(
                {'error': 'Account already exists for this phone number.'},
                status=status.HTTP_409_CONFLICT,
            )

        user = User.objects.create_user(
            username=phone,
            phone=phone,
            password=data['password'],
            first_name=data['first_name'],
            last_name=data.get('last_name', ''),
            role=data['role'],
        )

        Notification.objects.create(
            user=user,
            text='Welcome to TuitionMedia! Account created successfully.',
            notif_type='success',
            link='/dashboard/'
        )

        OTPVerification.objects.filter(phone=phone).delete()
        logger.info("New user created via OTP: phone=%s role=%s", phone, user.role)

        tokens = _jwt_tokens_for_user(user)
        return Response({
            'message':    'Account created successfully.',
            'user_id':    user.pk,
            'phone':      phone,
            'first_name': user.first_name,
            'role':       user.role,
            **tokens,
        }, status=status.HTTP_201_CREATED)


class ResendOTPView(APIView):
    """
    POST /api/auth/resend-otp/
    Body: { phone }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        ser = ResendOTPSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = ser.validated_data['phone']

        if User.objects.filter(phone=phone).exists():
            return Response(
                {'error': 'This phone number is already registered.'},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            _, raw_otp = send_otp(phone, send_otp_sms)
        except OTPError as exc:
            http_status = status.HTTP_429_TOO_MANY_REQUESTS if exc.code in ('cooldown', 'rate_limit') else status.HTTP_502_BAD_GATEWAY
            return Response({'error': exc.message, 'code': exc.code}, status=http_status)

        from django.conf import settings as dj_settings
        resp = {'message': f"OTP resent to {phone}. Valid for 2 minutes.", 'phone': phone}
        if dj_settings.DEBUG and getattr(dj_settings, 'SMS_BACKEND', '') == 'console':
            resp['dev_otp'] = raw_otp

        return Response(resp, status=status.HTTP_200_OK)


class OTPStatusView(APIView):
    """GET /api/auth/otp-status/?phone=01XXXXXXXXX"""
    permission_classes = [AllowAny]

    def get(self, request):
        ser = OTPStatusSerializer(data=request.query_params)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = ser.validated_data['phone']

        try:
            record = OTPVerification.objects.get(phone=phone)
        except OTPVerification.DoesNotExist:
            return Response({'exists': False}, status=status.HTTP_200_OK)

        from accounts.services.otp_service import get_resend_count, is_in_cooldown, MAX_RESENDS_PER_H
        from django.utils import timezone

        return Response({
            'exists':       True,
            'is_verified':  record.is_verified,
            'expires_at':   record.expires_at,
            'is_expired':   timezone.now() > record.expires_at,
            'attempts':     record.attempts,
            'resend_count': get_resend_count(phone),
            'resends_left': max(0, MAX_RESENDS_PER_H - get_resend_count(phone)),
            'in_cooldown':  is_in_cooldown(phone),
        })


# ── Login & Token ─────────────────────────────────────────────────────────────

class LoginView(APIView):
    """
    POST /api/auth/login/
    Body: { phone, password }
    Returns JWT access + refresh tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        phone    = ser.validated_data['phone']
        password = ser.validated_data['password']

        try:
            user_obj = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({'error': 'Phone number not registered.'}, status=status.HTTP_404_NOT_FOUND)

        if user_obj.banned:
            return Response({'error': 'Your account has been banned. Contact support.'}, status=status.HTTP_403_FORBIDDEN)

        user = authenticate(request, username=phone, password=password)
        if not user:
            return Response({'error': 'Incorrect password.'}, status=status.HTTP_401_UNAUTHORIZED)

        tokens = _jwt_tokens_for_user(user)
        logger.info("User logged in via API: phone=%s role=%s", phone, user.role)

        return Response({
            'message':    'Login successful.',
            'user_id':    user.pk,
            'phone':      user.phone,
            'first_name': user.first_name,
            'last_name':  user.last_name,
            'role':       user.role,
            **tokens,
        })


class TokenRefreshView(APIView):
    """
    POST /api/auth/token/refresh/
    Body: { refresh }
    Returns a new access token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh = RefreshToken(refresh_token)
            return Response({'access': str(refresh.access_token)})
        except Exception:
            return Response({'error': 'Invalid or expired refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)


# ── Forgot Password (OTP-based) ───────────────────────────────────────────────

class ForgotPasswordSendOTPView(APIView):
    """
    POST /api/auth/forgot-password/send/
    Body: { phone }
    Sends OTP to the registered phone for password reset.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        ser = ForgotPasswordSendSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = ser.validated_data['phone']

        if not User.objects.filter(phone=phone).exists():
            return Response({'error': 'Phone number not registered.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            _, raw_otp = send_otp(phone, send_otp_sms)
        except OTPError as exc:
            return Response({'error': exc.message, 'code': exc.code}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        from django.conf import settings as dj_settings
        resp = {'message': f"OTP sent to {phone}. Valid for 2 minutes.", 'phone': phone}
        if dj_settings.DEBUG and getattr(dj_settings, 'SMS_BACKEND', '') == 'console':
            resp['dev_otp'] = raw_otp

        return Response(resp)


class ForgotPasswordResetView(APIView):
    """
    POST /api/auth/forgot-password/reset/
    Body: { phone, otp, password }
    Verifies OTP and resets password. Returns JWT tokens on success.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        ser = ForgotPasswordVerifySerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        data     = ser.validated_data
        phone    = data['phone']
        otp      = data['otp']
        password = data['password']

        try:
            verify_otp(phone, otp)
        except OTPError as exc:
            code = exc.code
            http_status = {
                'brute_force': status.HTTP_429_TOO_MANY_REQUESTS,
                'not_found':   status.HTTP_404_NOT_FOUND,
                'expired':     status.HTTP_410_GONE,
                'invalid':     status.HTTP_401_UNAUTHORIZED,
            }.get(code, status.HTTP_400_BAD_REQUEST)
            return Response({'error': exc.message, 'code': code}, status=http_status)

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(password)
        user.save(update_fields=['password'])

        Notification.objects.create(
            user=user, text='Your password was reset successfully.', notif_type='success',
            link='/dashboard/'
        )

        OTPVerification.objects.filter(phone=phone).delete()
        tokens = _jwt_tokens_for_user(user)

        return Response({'message': 'Password reset successfully.', **tokens})


# ── Profile / Me ─────────────────────────────────────────────────────────────

class MeView(APIView):
    """
    GET /api/auth/me/
    Returns the authenticated user's profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ser = UserProfileSerializer(request.user, context={'request': request})
        return Response(ser.data)


class ProfileUpdateView(APIView):
    """
    PUT/PATCH /api/auth/profile/
    Updates user profile fields. Any update resets profile_approved to False.
    """
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def put(self, request):
        return self._update(request)

    def patch(self, request):
        return self._update(request, partial=True)

    def _update(self, request, partial=False):
        ser = ProfileUpdateSerializer(request.user, data=request.data, partial=partial, context={'request': request})
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        user = ser.save()

        if user.role != 'admin':
            user.profile_approved = False
            user.save(update_fields=['profile_approved'])

            for admin in User.objects.filter(role='admin'):
                Notification.objects.create(
                    user=admin,
                    text=f'{user.get_full_name()} updated their profile (needs approval)',
                    notif_type='warn',
                    link='/admin-panel/profile-approvals/'
                )

        return Response(UserProfileSerializer(user, context={'request': request}).data)


# ── Home Stats ────────────────────────────────────────────────────────────────

class HomeStatsView(APIView):
    """
    GET /api/home/stats/
    Returns platform statistics for the landing page.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from posts.models import Post

        total_tutors   = User.objects.filter(role='tutor', banned=False).count()
        total_students = User.objects.filter(role='student', banned=False).count()
        total_users    = User.objects.filter(banned=False).exclude(role='admin').count()
        total_posts    = Post.objects.filter(status='active').count()

        featured_tutors = User.objects.filter(
            role='tutor',
            banned=False,
            profile_approved=True,
        ).values('id', 'first_name', 'last_name', 'subjects', 'location', 'profile_image')[:6]

        featured_list = []
        for t in featured_tutors:
            img = t['profile_image']
            featured_list.append({
                'id':          t['id'],
                'name':        f"{t['first_name']} {t['last_name']}".strip(),
                'subjects':    t['subjects'],
                'location':    t['location'],
                'profile_image': request.build_absolute_uri(f"/media/{img}") if img else None,
            })

        return Response({
            'total_tutors':   total_tutors,
            'total_students': total_students,
            'total_users':    total_users,
            'active_posts':   total_posts,
            'featured_tutors': featured_list,
        })


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationsListView(APIView):
    """GET /api/auth/notifications/ — List current user's notifications."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifs = Notification.objects.filter(user=request.user)[:50]
        data = [{
            'id':         n.pk,
            'text':       n.text,
            'type':       n.notif_type,
            'read':       n.read,
            'created_at': n.created_at,
        } for n in notifs]
        return Response({'notifications': data, 'unread': sum(1 for n in notifs if not n.read)})


class MarkNotificationReadView(APIView):
    """POST /api/auth/notifications/<pk>/read/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            n = Notification.objects.get(pk=pk, user=request.user)
            n.read = True
            n.save(update_fields=['read'])
            return Response({'ok': True})
        except Notification.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
