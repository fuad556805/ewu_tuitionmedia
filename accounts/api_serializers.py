import re

from rest_framework import serializers

BD_PHONE_REGEX = re.compile(r'^\+?8801[3-9]\d{8}$')


def validate_bd_phone(phone: str) -> str:
    """
    Validate a Bangladesh phone number and normalise to 01XXXXXXXXX format.
    Accepts: 01XXXXXXXXX, 8801XXXXXXXXX, +8801XXXXXXXXX
    Returns: 01XXXXXXXXX  (consistent with how the existing User model stores phones)
    """
    phone = phone.strip().replace(' ', '').replace('-', '')
    # Normalise to +8801 for validation
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
    # Always return as 01XXXXXXXXX — matches existing User.phone storage format
    # +8801XXXXXXXXX → replace '+880' with '0'
    return normalised.replace('+880', '0', 1) if normalised.startswith('+880') else phone


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
