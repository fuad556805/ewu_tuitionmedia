"""
SMS Sender Utility for Bangladesh
Supports:
  1. Twilio           — international, reliable
  2. BulkSMSBD        — local BD provider (bulk SMS)
  3. SSL Wireless     — popular local BD provider
  4. Mock/Console     — for development (logs OTP to console)
Configured via SMS_BACKEND setting or SMS_BACKEND env var.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def _normalize_bd_phone(phone: str) -> str:
    """Convert BD phone to E.164 format (+8801XXXXXXXXX)."""
    phone = phone.strip().replace(' ', '').replace('-', '')
    if phone.startswith('+880'):
        return phone
    if phone.startswith('880'):
        return '+' + phone
    if phone.startswith('01'):
        return '+880' + phone[1:]
    return phone


# ──────────────────── Backends ────────────────────

def _send_twilio(phone: str, message: str):
    from twilio.rest import Client
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    msg = client.messages.create(
        body=message,
        from_=settings.TWILIO_FROM_NUMBER,
        to=phone,
    )
    logger.info("Twilio SMS sent to %s (SID: %s)", phone, msg.sid)


def _send_bulksmsbd(phone: str, message: str):
    import requests
    resp = requests.post(
        'https://bulksmsbd.net/api/smsapi',
        data={
            'api_key':  settings.BULKSMSBD_API_KEY,
            'type':     'text',
            'number':   phone,
            'senderid': settings.BULKSMSBD_SENDER_ID,
            'message':  message,
        },
        timeout=10,
    )
    data = resp.json()
    if data.get('response_code') != 202:
        raise RuntimeError(f"BulkSMSBD error: {data}")
    logger.info("BulkSMSBD SMS sent to %s", phone)


def _send_sslwireless(phone: str, message: str):
    import requests
    resp = requests.post(
        'https://sms.sslwireless.com/pushapi/dynamic/server.php',
        data={
            'user':   settings.SSLWIRELESS_USERNAME,
            'pass':   settings.SSLWIRELESS_PASSWORD,
            'sid':    settings.SSLWIRELESS_SID,
            'sms':    message,
            'mobile': phone,
            'msg_id': phone[-6:],
        },
        timeout=10,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"SSL Wireless HTTP error: {resp.status_code}")
    logger.info("SSL Wireless SMS sent to %s", phone)


def _send_console(phone: str, message: str):
    logger.warning("[DEV SMS] To: %s | Message: %s", phone, message)
    print(f"\n{'='*50}\n[OTP SMS] To: {phone}\n{message}\n{'='*50}\n")


_BACKENDS = {
    'twilio':      _send_twilio,
    'bulksmsbd':   _send_bulksmsbd,
    'sslwireless': _send_sslwireless,
    'console':     _send_console,
}

# ──────────────────── Public interface ────────────────────

def send_otp_sms(phone: str, otp: str):
    """
    Send an OTP SMS to the given phone number.
    Uses the backend configured in settings.SMS_BACKEND.
    Args:
        phone: any BD phone format (01X, 801X, +801X)
        otp:   6-digit OTP string
    """
    # Normalize to E.164 for all backends
    phone = _normalize_bd_phone(phone)

    message = (
        f"Your TuitionMedia OTP is: {otp}\n"
        f"Do not share it with anyone. Valid for 2 minutes."
    )

    # Read fresh from settings (not module-level cache)
    backend = getattr(settings, 'SMS_BACKEND', 'console').lower()
    sender  = _BACKENDS.get(backend)

    if sender is None:
        raise ValueError(
            f"Unknown SMS_BACKEND: '{backend}'. "
            f"Choose from: {list(_BACKENDS.keys())}"
        )

    logger.info("Sending OTP via %s to %s", backend, phone)
    sender(phone, message)
