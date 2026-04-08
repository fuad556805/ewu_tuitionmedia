import logging

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import OTPVerification
from accounts.services.otp_service import OTPError, send_otp, verify_otp
from accounts.utils.sms_sender import send_otp_sms
from .api_serializers import (
    OTPStatusSerializer,
    ResendOTPSerializer,
    SendOTPSerializer,
    VerifyOTPSerializer,
)

logger = logging.getLogger(__name__)
User   = get_user_model()


class SendOTPView(APIView):
    """
    POST /api/auth/send-otp/
    Body: { phone }

    Generates a 6-digit OTP, stores it hashed, and sends an SMS.
    Creates no user account at this stage.
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
            send_otp(phone, send_otp_sms)
        except OTPError as exc:
            return Response({'error': exc.message, 'code': exc.code}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        return Response({
            'message': f"OTP sent to {phone}. Valid for 2 minutes.",
            'phone':   phone,
        }, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """
    POST /api/auth/verify-otp/
    Body: { phone, otp, first_name, last_name, password, role }

    Verifies OTP and creates the user account on success.
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

        OTPVerification.objects.filter(phone=phone).delete()

        logger.info("New user created via OTP: phone=%s role=%s", phone, user.role)

        return Response({
            'message':    'Account created successfully.',
            'user_id':    user.pk,
            'phone':      phone,
            'first_name': user.first_name,
            'role':       user.role,
        }, status=status.HTTP_201_CREATED)


class ResendOTPView(APIView):
    """
    POST /api/auth/resend-otp/
    Body: { phone }

    Re-sends the OTP. Max 3 times per hour, 60s cooldown between sends.
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
            send_otp(phone, send_otp_sms)
        except OTPError as exc:
            http_status = status.HTTP_429_TOO_MANY_REQUESTS if exc.code in ('cooldown', 'rate_limit') else status.HTTP_502_BAD_GATEWAY
            return Response({'error': exc.message, 'code': exc.code}, status=http_status)

        return Response({
            'message': f"OTP resent to {phone}. Valid for 2 minutes.",
            'phone':   phone,
        }, status=status.HTTP_200_OK)


class OTPStatusView(APIView):
    """
    GET /api/auth/otp-status/?phone=+8801XXXXXXXXX

    Returns pending OTP status for a phone (expiry time, verified flag).
    Useful for the frontend to show countdown timers.
    Does NOT expose the OTP itself.
    """
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
            'exists':        True,
            'is_verified':   record.is_verified,
            'expires_at':    record.expires_at,
            'is_expired':    timezone.now() > record.expires_at,
            'attempts':      record.attempts,
            'resend_count':  get_resend_count(phone),
            'resends_left':  max(0, MAX_RESENDS_PER_H - get_resend_count(phone)),
            'in_cooldown':   is_in_cooldown(phone),
        })
