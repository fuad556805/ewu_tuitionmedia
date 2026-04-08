"""
Nagad Payment Integration
Docs: https://nagad.com.bd/api-documentation
Uses RSA encryption for request signing and signature verification.
"""
import base64
import hashlib
import json
import logging
import time
import uuid

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from django.conf import settings

logger = logging.getLogger(__name__)

MERCHANT_ID    = settings.NAGAD_MERCHANT_ID
MERCHANT_KEY   = settings.NAGAD_MERCHANT_KEY       # Merchant private key (PEM)
NAGAD_PUB_KEY  = settings.NAGAD_PUBLIC_KEY         # Nagad public key (PEM)
BASE_URL       = settings.NAGAD_BASE_URL            # sandbox or live


# ──────────────────── Crypto helpers ────────────────────

def _load_private_key():
    pem = MERCHANT_KEY.encode() if isinstance(MERCHANT_KEY, str) else MERCHANT_KEY
    return serialization.load_pem_private_key(pem, password=None)


def _load_nagad_public_key():
    pem = NAGAD_PUB_KEY.encode() if isinstance(NAGAD_PUB_KEY, str) else NAGAD_PUB_KEY
    return serialization.load_pem_public_key(pem)


def _encrypt_with_nagad_public_key(plaintext: str) -> str:
    """Encrypt data with Nagad's public key (RSA-OAEP)."""
    pub_key    = _load_nagad_public_key()
    ciphertext = pub_key.encrypt(plaintext.encode(), padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA1()),
        algorithm=hashes.SHA1(),
        label=None,
    ))
    return base64.b64encode(ciphertext).decode()


def _sign_with_merchant_key(data: str) -> str:
    """Sign data with merchant's RSA private key (PKCS1v15 + SHA256)."""
    priv_key  = _load_private_key()
    signature = priv_key.sign(data.encode(), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(signature).decode()


def _verify_nagad_signature(data: str, signature_b64: str) -> bool:
    """Verify Nagad's callback signature using Nagad's public key."""
    try:
        pub_key   = _load_nagad_public_key()
        signature = base64.b64decode(signature_b64)
        pub_key.verify(signature, data.encode(), padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception as exc:
        logger.error("Nagad signature verification failed: %s", exc)
        return False


# ──────────────────── API helpers ────────────────────

def _headers() -> dict:
    return {
        'Content-Type':  'application/json',
        'Accept':        'application/json',
        'X-KM-Api-Version': 'v-0.2.0',
        'X-KM-IP-V4':    '127.0.0.1',
        'X-KM-Client-Type': 'PC_WEB',
    }


def _datetime_str() -> str:
    return time.strftime('%Y%m%d%H%M%S')


# ──────────────────── Public API ────────────────────

def initiate_payment(order_id: str, amount: str, callback_url: str) -> dict:
    """
    Step 1 – Initiate a Nagad payment.
    Returns dict with 'callBackUrl' on success (user must be redirected there).
    """
    datetime_str = _datetime_str()
    challenge    = str(uuid.uuid4())

    sensitive_data = {
        'merchantId':      MERCHANT_ID,
        'datetime':        datetime_str,
        'orderId':         order_id,
        'challenge':       challenge,
    }

    encrypted_data = _encrypt_with_nagad_public_key(json.dumps(sensitive_data))
    signature      = _sign_with_merchant_key(json.dumps(sensitive_data))

    url  = f"{BASE_URL}/remote-payment-gateway-1.0/api/dfs/check-out/initialize/{MERCHANT_ID}/{order_id}"
    body = {
        'dateTime':         datetime_str,
        'sensitiveData':    encrypted_data,
        'signature':        signature,
        'merchantCallbackURL': callback_url,
        'additionalMerchantInfo': {
            'sMSTagline':  'Payment via TuitionMedia',
            'a2IReference': f"REF-{order_id}",
        },
    }

    try:
        resp = requests.post(url, json=body, headers=_headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        logger.info("Nagad initiate_payment response: %s", data)

        if data.get('status') != 'Success':
            return {'error': data.get('message', 'Initiation failed'), 'raw': data}

        payment_ref_id  = data.get('paymentReferenceId')
        challenge_back  = data.get('challenge')

        payment_data = {
            'merchantId':         MERCHANT_ID,
            'orderId':            order_id,
            'challenge':          challenge_back,
            'amount':             str(amount),
            'currencyCode':       '050',
            'orderDatetime':      datetime_str,
            'paymentRefId':       payment_ref_id,
        }

        enc_payment    = _encrypt_with_nagad_public_key(json.dumps(payment_data))
        payment_sig    = _sign_with_merchant_key(json.dumps(payment_data))

        complete_url  = f"{BASE_URL}/remote-payment-gateway-1.0/api/dfs/check-out/complete/{MERCHANT_ID}/{order_id}"
        complete_body = {
            'sensitiveData': enc_payment,
            'signature':     payment_sig,
            'merchantCallbackURL': callback_url,
        }

        c_resp = requests.post(complete_url, json=complete_body, headers=_headers(), timeout=15)
        c_resp.raise_for_status()
        c_data = c_resp.json()
        logger.info("Nagad complete-initiation response: %s", c_data)
        return c_data

    except Exception as exc:
        logger.error("Nagad initiate_payment error: %s", exc)
        return {'error': str(exc)}


def verify_payment(payment_ref_id: str) -> dict:
    """
    Verify a Nagad payment using the paymentReferenceId from callback.
    Returns full verification response.
    """
    url = f"{BASE_URL}/remote-payment-gateway-1.0/api/dfs/verify/payment/{payment_ref_id}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        logger.info("Nagad verify_payment response: %s", data)
        return data
    except Exception as exc:
        logger.error("Nagad verify_payment error: %s", exc)
        return {'error': str(exc)}


def validate_callback_signature(callback_data: dict) -> bool:
    """
    Validate the signature in Nagad's callback to prevent tampering.
    callback_data should contain 'sensitiveData' and 'signature'.
    """
    sensitive_data = callback_data.get('sensitiveData', '')
    signature      = callback_data.get('signature', '')
    if not sensitive_data or not signature:
        return False
    return _verify_nagad_signature(sensitive_data, signature)


def is_successful(response: dict) -> bool:
    """Returns True if Nagad response indicates a completed payment."""
    return response.get('status') == 'Success' and response.get('paymentStatus') == 'Completed'
