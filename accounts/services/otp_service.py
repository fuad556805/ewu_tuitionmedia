"""
OTP Service — generation, hashing, verification, rate limiting.
Uses Django's cache backend (memory/Redis/memcached) for rate limiting.
OTPs are stored hashed in the DB using PBKDF2.
"""
import hashlib
import hmac
import random
import string
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone

from accounts.models import OTPVerification

OTP_LENGTH        = 6
OTP_EXPIRY_MINS   = 2
MAX_RESENDS_PER_H = 3
MAX_VERIFY_ATTEMPTS = 5
RESEND_COOLDOWN_S   = 60     # minimum seconds between any two sends
RATE_LIMIT_WINDOW_S = 3600   # 1 hour window for resend count


# ──────────────────── Helpers ────────────────────

def _generate_otp() -> str:
    """Generate a cryptographically random 6-digit OTP."""
    return ''.join(random.SystemRandom().choices(string.digits, k=OTP_LENGTH))


def _hash_otp(otp: str, phone: str) -> str:
    """PBKDF2-HMAC-SHA256 hash of OTP salted with the phone number."""
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        otp.encode(),
        phone.encode(),
        iterations=260_000,
    )
    return dk.hex()


def _constant_time_compare(val1: str, val2: str) -> bool:
    return hmac.compare_digest(val1.encode(), val2.encode())


# ──────────────────── Rate limiting (cache-backed) ────────────────────

def _resend_count_key(phone: str) -> str:
    return f"otp:resend_count:{phone}"


def _cooldown_key(phone: str) -> str:
    return f"otp:cooldown:{phone}"


def _brute_force_key(phone: str) -> str:
    return f"otp:verify_attempts:{phone}"


def get_resend_count(phone: str) -> int:
    return cache.get(_resend_count_key(phone), 0)


def increment_resend_count(phone: str) -> int:
    key = _resend_count_key(phone)
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=RATE_LIMIT_WINDOW_S)
        count = 1
    return count


def set_cooldown(phone: str):
    cache.set(_cooldown_key(phone), True, timeout=RESEND_COOLDOWN_S)


def is_in_cooldown(phone: str) -> bool:
    return bool(cache.get(_cooldown_key(phone)))


def get_verify_attempts(phone: str) -> int:
    return cache.get(_brute_force_key(phone), 0)


def increment_verify_attempts(phone: str) -> int:
    key = _brute_force_key(phone)
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=RATE_LIMIT_WINDOW_S)
        count = 1
    return count


def reset_verify_attempts(phone: str):
    cache.delete(_brute_force_key(phone))


# ──────────────────── Public API ────────────────────

class OTPError(Exception):
    """Raised when OTP operation cannot proceed."""
    def __init__(self, message: str, code: str = 'otp_error'):
        self.message = message
        self.code    = code
        super().__init__(message)


def send_otp(phone: str, sms_sender) -> tuple:
    """
    Generate and send an OTP for the given phone number.
    Creates or updates an OTPVerification record.
    Enforces cooldown and hourly resend limits.

    Args:
        phone:      normalised Bangladesh phone number
        sms_sender: callable(phone, otp) → None

    Returns:
        OTPVerification instance

    Raises:
        OTPError on rate-limit or send failure
    """
    if is_in_cooldown(phone):
        raise OTPError(
            f"Please wait {RESEND_COOLDOWN_S} seconds before requesting another OTP.",
            code='cooldown',
        )

    resend_count = get_resend_count(phone)
    if resend_count >= MAX_RESENDS_PER_H:
        raise OTPError(
            "Too many OTP requests. Please try again after 1 hour.",
            code='rate_limit',
        )

    otp      = _generate_otp()
    otp_hash = _hash_otp(otp, phone)
    expires  = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINS)

    record, _ = OTPVerification.objects.update_or_create(
        phone=phone,
        defaults={
            'otp_hash':    otp_hash,
            'expires_at':  expires,
            'attempts':    0,
            'is_verified': False,
        },
    )

    try:
        sms_sender(phone, otp)
    except Exception as exc:
        raise OTPError(f"Failed to send SMS: {exc}", code='sms_error') from exc

    increment_resend_count(phone)
    set_cooldown(phone)
    reset_verify_attempts(phone)
    # Returns (record, raw_otp) — caller may expose raw_otp in dev/console mode only
    return record, otp


def verify_otp(phone: str, otp: str) -> OTPVerification:
    """
    Verify the OTP for the given phone number.

    Returns:
        OTPVerification instance (is_verified=True) on success

    Raises:
        OTPError with meaningful codes on failure
    """
    if get_verify_attempts(phone) >= MAX_VERIFY_ATTEMPTS:
        raise OTPError(
            "Too many incorrect attempts. Please request a new OTP.",
            code='brute_force',
        )

    try:
        record = OTPVerification.objects.get(phone=phone, is_verified=False)
    except OTPVerification.DoesNotExist:
        raise OTPError("No pending OTP found for this number.", code='not_found')

    if timezone.now() > record.expires_at:
        raise OTPError("OTP has expired. Please request a new one.", code='expired')

    otp_hash = _hash_otp(otp, phone)
    if not _constant_time_compare(otp_hash, record.otp_hash):
        record.attempts += 1
        record.save(update_fields=['attempts'])
        increment_verify_attempts(phone)
        raise OTPError("Incorrect OTP. Please try again.", code='invalid')

    record.is_verified = True
    record.save(update_fields=['is_verified', 'attempts'])
    reset_verify_attempts(phone)
    return record
