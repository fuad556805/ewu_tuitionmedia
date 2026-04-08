"""
bKash Tokenized Checkout Integration
Docs: https://developer.bka.sh/docs/tokenized-checkout-process-overview
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL     = settings.BKASH_BASE_URL
APP_KEY      = settings.BKASH_APP_KEY
APP_SECRET   = settings.BKASH_APP_SECRET
USERNAME     = settings.BKASH_USERNAME
PASSWORD     = settings.BKASH_PASSWORD

_token_cache = {'id_token': None, 'refresh_token': None}


def _headers(token: str) -> dict:
    return {
        'Content-Type':  'application/json',
        'Accept':        'application/json',
        'authorization': token,
        'x-app-key':     APP_KEY,
    }


def grant_token() -> str | None:
    """Obtain a new id_token from bKash. Returns id_token on success."""
    url  = f"{BASE_URL}/tokenized/checkout/token/grant"
    body = {
        'app_key':    APP_KEY,
        'app_secret': APP_SECRET,
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept':       'application/json',
        'username':     USERNAME,
        'password':     PASSWORD,
    }
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        _token_cache['id_token']      = data.get('id_token')
        _token_cache['refresh_token'] = data.get('refresh_token')
        logger.info("bKash token granted successfully.")
        return _token_cache['id_token']
    except Exception as exc:
        logger.error("bKash grant_token failed: %s", exc)
        return None


def _get_token() -> str | None:
    if _token_cache['id_token']:
        return _token_cache['id_token']
    return grant_token()


def create_payment(amount: str, invoice_number: str, callback_url: str) -> dict:
    """
    Step 1 – Create Payment.
    Returns the full bKash API response dict.
    On success contains: paymentID, bkashURL, statusCode == '0000'
    """
    token = _get_token()
    if not token:
        return {'error': 'Could not obtain bKash token'}

    url  = f"{BASE_URL}/tokenized/checkout/create"
    body = {
        'mode':                   '0011',
        'payerReference':         invoice_number,
        'callbackURL':            callback_url,
        'amount':                 str(amount),
        'currency':               'BDT',
        'intent':                 'sale',
        'merchantInvoiceNumber':  invoice_number,
    }
    try:
        resp = requests.post(url, json=body, headers=_headers(token), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        logger.info("bKash create_payment response: %s", data)
        return data
    except Exception as exc:
        logger.error("bKash create_payment failed: %s", exc)
        return {'error': str(exc)}


def execute_payment(payment_id: str) -> dict:
    """
    Step 2 – Execute Payment after user completes on bKash page.
    On success statusCode == '0000', transactionStatus == 'Completed'
    """
    token = _get_token()
    if not token:
        return {'error': 'Could not obtain bKash token'}

    url  = f"{BASE_URL}/tokenized/checkout/execute"
    body = {'paymentID': payment_id}
    try:
        resp = requests.post(url, json=body, headers=_headers(token), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        logger.info("bKash execute_payment response: %s", data)
        return data
    except Exception as exc:
        logger.error("bKash execute_payment failed: %s", exc)
        return {'error': str(exc)}


def query_payment(payment_id: str) -> dict:
    """
    Step 3 – Query / verify a payment by paymentID.
    Use this to double-check status after execute.
    """
    token = _get_token()
    if not token:
        return {'error': 'Could not obtain bKash token'}

    url  = f"{BASE_URL}/tokenized/checkout/payment/status"
    body = {'paymentID': payment_id}
    try:
        resp = requests.post(url, json=body, headers=_headers(token), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        logger.info("bKash query_payment response: %s", data)
        return data
    except Exception as exc:
        logger.error("bKash query_payment failed: %s", exc)
        return {'error': str(exc)}


def is_successful(response: dict) -> bool:
    """Returns True if bKash response indicates a successful completed payment."""
    return (
        response.get('statusCode') == '0000'
        and response.get('transactionStatus') == 'Completed'
    )
