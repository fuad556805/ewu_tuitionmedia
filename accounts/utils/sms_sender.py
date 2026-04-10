"""
SMS Sender Utility for Bangladesh
Supports:
  1. twilio_verify  — Twilio Verify API (any number, recommended)
  2. twilio         — Twilio SMS (verified numbers only)
  3. bulksmsbd      — local BD provider
  4. sslwireless    — local BD provider
  5. console        — development only

Fallback chain: configured backend → fallback backends → console
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def _normalize_bd_phone(phone: str) -> str:
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
    """
    Twilio Verify — যেকোনো নম্বরে কাজ করে।
    OTP টা ignore করে — Twilio নিজেই OTP পাঠায়।
    verify করার সময় twilio_verify_check() call করতে হবে।
    """
    from twilio.rest import Client
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    verification = client.verify \
        .v2 \
        .services(settings.TWILIO_VERIFY_SERVICE_SID) \
        .verifications \
        .create(to=phone, channel='sms')
    logger.info("Twilio Verify sent to %s (status: %s)", phone, verification.status)


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


# ──────────────────── Twilio Verify Check ────────────────────

def twilio_verify_check(phone: str, otp: str) -> bool:
    """
    Twilio Verify দিয়ে OTP verify করে।
    True = সঠিক, False = ভুল।
    শুধু SMS_BACKEND=twilio_verify হলে call করতে হবে।
    """
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        result = client.verify \
            .v2 \
            .services(settings.TWILIO_VERIFY_SERVICE_SID) \
            .verification_checks \
            .create(to=phone, code=otp)
        return result.status == 'approved'
    except Exception as e:
        logger.error("Twilio Verify check failed: %s", e)
        return False


def is_twilio_verify_active() -> bool:
    """Primary backend twilio_verify কিনা check করে।"""
    return getattr(settings, 'SMS_BACKEND', 'console').lower() == 'twilio_verify'


# ──────────────────── Fallback chain ────────────────────

def _get_fallback_chain(primary: str) -> list:
    fallbacks = getattr(settings, 'SMS_FALLBACKS', [])
    chain = [primary] + [f for f in fallbacks if f != primary]
    if 'console' not in chain:
        chain.append('console')
    return chain


# ──────────────────── Public interface ────────────────────

def send_otp_sms(phone: str, otp: str):
    """
    OTP SMS পাঠায়।
    Primary backend fail হলে fallback chain try করে।
    """
    phone = _normalize_bd_phone(phone)
    message = (
        f"Your TuitionMedia OTP is: {otp}\n"
        f"Do not share it with anyone. Valid for 2 minutes."
    )

    primary = getattr(settings, 'SMS_BACKEND', 'console').lower()
    chain   = _get_fallback_chain(primary)

    _backend_map = {
        'twilio_verify': lambda p, m: _send_twilio_verify(p, otp),
        'twilio':        _send_twilio,
        'bulksmsbd':     _send_bulksmsbd,
        'sslwireless':   _send_sslwireless,
        'console':       _send_console,
    }

    last_error = None
    for backend_name in chain:
        sender = _backend_map.get(backend_name)
        if sender is None:
            logger.warning("Unknown SMS backend: '%s', skipping.", backend_name)
            continue
        try:
            logger.info("Trying SMS via %s to %s", backend_name, phone)
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
