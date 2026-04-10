"""
SMS Sender Utility for Bangladesh
Supports:
  1. Twilio Verify    — international, any number (recommended)
  2. Twilio SMS       — international, verified numbers only
  3. BulkSMSBD        — local BD provider
  4. SSL Wireless     — local BD provider
  5. Console          — development only

Fallback chain: configured backend → fallback backends → console
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

def _send_twilio_verify(phone: str, otp: str):
    """Twilio Verify — works with any number, no verified caller ID needed."""
    from twilio.rest import Client
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    # Verification পাঠাও
    verification = client.verify \
        .v2 \
        .services(settings.TWILIO_VERIFY_SERVICE_SID) \
        .verifications \
        .create(to=phone, channel='sms')

    logger.info("Twilio Verify sent to %s (status: %s)", phone, verification.status)


def _send_twilio(phone: str, message: str):
    """Twilio SMS — শুধু verified numbers এ কাজ করে (trial account)."""
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
            'senderid': getattr(settings, 'BULKSMSBD_SENDER_ID', ''),
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


# ──────────────────── Special handler for Twilio Verify ────────────────────

def _is_verify_backend(name: str) -> bool:
    return name == 'twilio_verify'


# ──────────────────── Fallback chain ────────────────────

def _get_fallback_chain(primary: str) -> list:
    fallbacks = getattr(settings, 'SMS_FALLBACKS', [])
    chain = [primary] + [f for f in fallbacks if f != primary]
    if 'console' not in chain:
        chain.append('console')
    return chain


# ──────────────────── Public interface ────────────────────

def send_otp_sms(phone: str, otp: str):
    phone = _normalize_bd_phone(phone)
    message = (
        f"Your TuitionMedia OTP is: {otp}\n"
        f"Do not share it with anyone. Valid for 2 minutes."
    )

    primary = getattr(settings, 'SMS_BACKEND', 'console').lower()
    chain   = _get_fallback_chain(primary)

    last_error = None
    for backend_name in chain:

        try:
            logger.info("Trying SMS via %s to %s", backend_name, phone)

            # Twilio Verify আলাদাভাবে handle করে — OTP নিজেই generate করে
            if _is_verify_backend(backend_name):
                _send_twilio_verify(phone, otp)
            else:
                sender = {
                    'twilio':      _send_twilio,
                    'bulksmsbd':   _send_bulksmsbd,
                    'sslwireless': _send_sslwireless,
                    'console':     _send_console,
                }.get(backend_name)

                if sender is None:
                    logger.warning("Unknown SMS backend: '%s', skipping.", backend_name)
                    continue

                sender(phone, message)

            if backend_name != primary:
                logger.warning(
                    "Primary backend '%s' failed — sent via fallback '%s'",
                    primary, backend_name
                )
            return

        except Exception as exc:
            last_error = exc
            logger.warning("SMS backend '%s' failed: %s", backend_name, exc)
            continue

    raise RuntimeError(f"All SMS backends failed. Last error: {last_error}")
