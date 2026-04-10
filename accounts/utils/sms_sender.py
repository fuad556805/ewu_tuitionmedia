"""
SMS Sender Utility for Bangladesh
Supports:
  1. Twilio           — international, reliable
  2. BulkSMSBD        — local BD provider (bulk SMS)
  3. SSL Wireless     — popular local BD provider
  4. Mock/Console     — for development (logs OTP to console)

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


_BACKENDS = {
    'twilio':      _send_twilio,
    'bulksmsbd':   _send_bulksmsbd,
    'sslwireless': _send_sslwireless,
    'console':     _send_console,
}


# ──────────────────── Fallback chain ────────────────────

def _get_fallback_chain(primary: str) -> list:
    """
    Returns ordered list of backends to try.
    Primary backend first, then SMS_FALLBACKS list, then console.
    """
    fallbacks = getattr(settings, 'SMS_FALLBACKS', [])
    chain = [primary] + [f for f in fallbacks if f != primary]

    # console সবসময় শেষে থাকবে (last resort)
    if 'console' not in chain:
        chain.append('console')

    return chain


# ──────────────────── Public interface ────────────────────

def send_otp_sms(phone: str, otp: str):
    """
    Send an OTP SMS to the given phone number.
    Tries primary backend first, then fallbacks on failure.
    """
    phone = _normalize_bd_phone(phone)
    message = (
        f"Your TuitionMedia OTP is: {otp}\n"
        f"Do not share it with anyone. Valid for 2 minutes."
    )

    primary = getattr(settings, 'SMS_BACKEND', 'console').lower()
    chain   = _get_fallback_chain(primary)

    last_error = None
    for backend_name in chain:
        sender = _BACKENDS.get(backend_name)
        if sender is None:
            logger.warning("Unknown SMS backend: '%s', skipping.", backend_name)
            continue

        try:
            logger.info("Trying SMS via %s to %s", backend_name, phone)
            sender(phone, message)
            if backend_name != primary:
                logger.warning("Primary backend '%s' failed — sent via fallback '%s'", primary, backend_name)
            return  # সফল হলে বের হয়ে যাও

        except Exception as exc:
            last_error = exc
            logger.warning("SMS backend '%s' failed: %s", backend_name, exc)
            continue  # পরের backend try করো

    # সব backend fail হলে
    raise RuntimeError(
        f"All SMS backends failed. Last error: {last_error}"
    )
