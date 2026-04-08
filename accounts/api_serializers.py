import re

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

BD_PHONE_REGEX = re.compile(r'^\+?8801[3-9]\d{8}$')


def validate_bd_phone(phone: str) -> str:
    phone = phone.strip().replace(' ', '').replace('-', '')
    if phone.startswith('01') and len(phone) == 11:
        normalised = '+880' + phone[1:]
    elif phone.startswith('8801') and len(phone) == 13:
        normalised = '+' + phone
    elif phone.startswith('+8801') and len(phone) == 14:
        normalised = phone
    else:
        normalised = phone

    if not BD_PHONE_REGEX.match(normalised):
        raise serializers.ValidationError(
            "Enter a valid Bangladesh phone number (e.g. 01XXXXXXXXX)."
        )
    return normalised.replace('+880', '0', 1) if normalised.startswith('+880') else phone


# ── OTP Serializers ──────────────────────────────────────────────────────────

class SendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)

    def validate_phone(self, value):
        return validate_bd_phone(value)


class VerifyOTPSerializer(serializers.Serializer):
    ROLE_CHOICES = ['student', 'tutor']

    phone      = serializers.CharField(max_length=20)
    otp        = serializers.CharField(min_length=6, max_length=6)
    first_name = serializers.CharField(max_length=150)
    last_name  = serializers.CharField(max_length=150, required=False, default='')
    password   = serializers.CharField(min_length=8, write_only=True)
    role       = serializers.ChoiceField(choices=ROLE_CHOICES, default='student')

    def validate_phone(self, value):
        return validate_bd_phone(value)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain digits only.")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters.")
        return value


class ResendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)

    def validate_phone(self, value):
        return validate_bd_phone(value)


class OTPStatusSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)

    def validate_phone(self, value):
        return validate_bd_phone(value)


# ── Auth Serializers ─────────────────────────────────────────────────────────

class LoginSerializer(serializers.Serializer):
    phone    = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)

    def validate_phone(self, value):
        return validate_bd_phone(value)


class ForgotPasswordSendSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)

    def validate_phone(self, value):
        return validate_bd_phone(value)


class ForgotPasswordVerifySerializer(serializers.Serializer):
    phone    = serializers.CharField(max_length=20)
    otp      = serializers.CharField(min_length=6, max_length=6)
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_phone(self, value):
        return validate_bd_phone(value)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain digits only.")
        return value


# ── Profile Serializers ───────────────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = [
            'id', 'phone', 'first_name', 'last_name', 'email', 'role',
            'gender', 'profile_image', 'id_image',
            'school', 'college', 'university', 'department', 'subjects', 'location',
            'profile_approved', 'banned', 'theme',
        ]
        read_only_fields = ['id', 'phone', 'role', 'profile_approved', 'banned']


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = [
            'first_name', 'last_name', 'email', 'gender',
            'profile_image', 'id_image',
            'school', 'college', 'university', 'department', 'subjects', 'location',
            'theme',
        ]

    def validate_theme(self, value):
        if value not in ['dark', 'ocean', 'sunset']:
            raise serializers.ValidationError("Invalid theme. Choose dark, ocean, or sunset.")
        return value
