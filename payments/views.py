import logging
import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tuitions.models import Tuition
from . import bkash_service, nagad_service
from .models import Commission, ContactUnlock, Payment
from .serializers import (
    BkashCreateSerializer,
    BkashExecuteSerializer,
    CommissionSerializer,
    ContactUnlockSerializer,
    NagadCallbackSerializer,
    PaymentSerializer,
)

logger = logging.getLogger(__name__)

CONTACT_UNLOCK_FEE = Decimal('100.00')
COMMISSION_RATE    = Decimal('0.30')


# ──────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────

def _generate_invoice() -> str:
    return f"TM-{uuid.uuid4().hex[:12].upper()}"


def _get_callback_url(request, path: str) -> str:
    return request.build_absolute_uri(path)


def _check_duplicate_payment(payment_id: str) -> bool:
    return Payment.objects.filter(payment_id=payment_id, status='completed').exists()


def _resolve_amount_and_purpose(user, data: dict):
    """
    Returns (amount, purpose, related_object_or_None) or raises ValueError.
    """
    purpose = data['purpose']

    if purpose == 'contact_unlock':
        from accounts.models import User as UserModel
        tutor = UserModel.objects.filter(pk=data['tutor_id'], role='tutor').first()
        if not tutor:
            raise ValueError("Tutor not found.")
        if ContactUnlock.objects.filter(student=user, tutor=tutor).exists():
            raise ValueError("Contact already unlocked for this tutor.")
        return CONTACT_UNLOCK_FEE, purpose, tutor

    if purpose == 'commission':
        if user.role != 'tutor':
            raise ValueError("Only tutors can pay commission.")
        unpaid = Commission.objects.filter(tutor=user, paid=False).exclude(
            tuition__pk=data.get('tuition_id')
        )
        if unpaid.exists():
            raise ValueError("You have unpaid commissions. Please settle them before proceeding.")
        tuition = Tuition.objects.filter(pk=data['tuition_id'], tutor=user, status='completed').first()
        if not tuition:
            raise ValueError("Completed tuition not found.")
        comm, _ = Commission.objects.get_or_create(
            tuition=tuition,
            defaults={
                'tutor':  user,
                'amount': (tuition.salary * COMMISSION_RATE).quantize(Decimal('0.01')),
            }
        )
        if comm.paid:
            raise ValueError("Commission for this tuition is already paid.")
        return comm.amount, purpose, comm

    raise ValueError("Invalid purpose.")


def _finalize_payment(payment: Payment, bkash_data: dict = None, nagad_data: dict = None):
    """
    After verifying a successful payment, create related records.
    Must be called inside an atomic block.
    """
    user    = payment.user
    purpose = payment.purpose

    if purpose == 'contact_unlock':
        # Find the related tutor from raw_response stored during create
        tutor_id = payment.raw_response.get('tutor_id')
        if tutor_id:
            from accounts.models import User as UserModel
            tutor = UserModel.objects.filter(pk=tutor_id).first()
            if tutor:
                ContactUnlock.objects.get_or_create(
                    student=user,
                    tutor=tutor,
                    defaults={'payment': payment},
                )

    elif purpose == 'commission':
        commission_id = payment.raw_response.get('commission_id')
        if commission_id:
            Commission.objects.filter(pk=commission_id).update(
                paid=True,
                payment=payment,
                paid_at=timezone.now(),
            )


# ──────────────────────────────────────────
# bKash Views
# ──────────────────────────────────────────

class BkashCreatePaymentView(APIView):
    """
    POST /api/payment/bkash/create/
    Body: { purpose, method, tutor_id OR tuition_id }
    Creates a bKash payment and returns the bkashURL for redirect.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = BkashCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        data   = ser.validated_data
        method = data['method']
        user   = request.user

        try:
            amount, purpose, related = _resolve_amount_and_purpose(user, data)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        invoice = _generate_invoice()

        raw = {
            'tutor_id':      data.get('tutor_id'),
            'tuition_id':    data.get('tuition_id'),
            'commission_id': related.pk if purpose == 'commission' else None,
        }

        if method == 'bkash':
            callback_url = _get_callback_url(request, '/api/payment/bkash/execute/')
            bkash_resp   = bkash_service.create_payment(
                amount=str(amount),
                invoice_number=invoice,
                callback_url=callback_url,
            )

            if 'error' in bkash_resp or bkash_resp.get('statusCode') != '0000':
                logger.error("bKash create failed: %s", bkash_resp)
                return Response(
                    {'error': bkash_resp.get('statusMessage', 'bKash payment creation failed.')},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            payment = Payment.objects.create(
                user=user,
                amount=amount,
                method='bkash',
                status='initiated',
                purpose=purpose,
                payment_id=bkash_resp['paymentID'],
                raw_response={**raw, 'invoice': invoice},
            )

            return Response({
                'payment_id':  payment.payment_id,
                'bkash_url':   bkash_resp.get('bkashURL'),
                'amount':      str(amount),
                'status':      'initiated',
            }, status=status.HTTP_201_CREATED)

        elif method == 'nagad':
            callback_url = _get_callback_url(request, '/api/payment/nagad/callback/')
            nagad_resp   = nagad_service.initiate_payment(
                order_id=invoice,
                amount=str(amount),
                callback_url=callback_url,
            )

            if 'error' in nagad_resp:
                return Response(
                    {'error': nagad_resp['error']},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            payment = Payment.objects.create(
                user=user,
                amount=amount,
                method='nagad',
                status='initiated',
                purpose=purpose,
                payment_id=invoice,
                raw_response={**raw, 'invoice': invoice, 'nagad_init': nagad_resp},
            )

            return Response({
                'payment_id':  payment.payment_id,
                'redirect_url': nagad_resp.get('callBackUrl'),
                'amount':      str(amount),
                'status':      'initiated',
            }, status=status.HTTP_201_CREATED)

        return Response({'error': 'Invalid method.'}, status=status.HTTP_400_BAD_REQUEST)


class BkashExecutePaymentView(APIView):
    """
    POST /api/payment/bkash/execute/
    Body: { payment_id }
    Executes the bKash payment after user completes on bKash page, then verifies.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = BkashExecuteSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        payment_id = ser.validated_data['payment_id']

        if _check_duplicate_payment(payment_id):
            return Response({'error': 'Payment already completed.'}, status=status.HTTP_409_CONFLICT)

        payment = Payment.objects.filter(payment_id=payment_id, user=request.user).first()
        if not payment:
            return Response({'error': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)

        exec_resp = bkash_service.execute_payment(payment_id)
        if 'error' in exec_resp:
            payment.status = 'failed'
            payment.raw_response = {**payment.raw_response, 'execute_error': exec_resp}
            payment.save()
            return Response({'error': exec_resp['error']}, status=status.HTTP_502_BAD_GATEWAY)

        query_resp = bkash_service.query_payment(payment_id)

        if bkash_service.is_successful(query_resp):
            with transaction.atomic():
                payment.status         = 'completed'
                payment.transaction_id = query_resp.get('trxID', '')
                payment.raw_response   = {**payment.raw_response, 'execute': exec_resp, 'query': query_resp}
                payment.save()
                _finalize_payment(payment, bkash_data=query_resp)

            return Response({
                'message':        'Payment successful.',
                'transaction_id': payment.transaction_id,
                'status':         'completed',
            })

        payment.status       = 'failed'
        payment.raw_response = {**payment.raw_response, 'execute': exec_resp, 'query': query_resp}
        payment.save()
        return Response(
            {'error': 'Payment verification failed.', 'bkash_status': query_resp.get('transactionStatus')},
            status=status.HTTP_402_PAYMENT_REQUIRED,
        )


class BkashPaymentStatusView(APIView):
    """
    GET /api/payment/bkash/status/?payment_id=<id>
    Query bKash for the current status of a payment.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payment_id = request.query_params.get('payment_id')
        if not payment_id:
            return Response({'error': 'payment_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.filter(payment_id=payment_id, user=request.user).first()
        if not payment:
            return Response({'error': 'Payment not found.'}, status=status.HTTP_404_NOT_FOUND)

        query_resp = bkash_service.query_payment(payment_id)
        if 'error' in query_resp:
            return Response({'error': query_resp['error']}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({
            'payment_id':         payment_id,
            'local_status':       payment.status,
            'bkash_status':       query_resp.get('transactionStatus'),
            'transaction_id':     query_resp.get('trxID'),
            'amount':             query_resp.get('amount'),
        })


# ──────────────────────────────────────────
# Nagad Views
# ──────────────────────────────────────────

class NagadInitPaymentView(APIView):
    """
    POST /api/payment/nagad/init/
    Body: { purpose, tutor_id OR tuition_id }
    Initiates Nagad payment; client must redirect user to returned URL.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['method'] = 'nagad'
        ser = BkashCreateSerializer(data=data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        try:
            amount, purpose, related = _resolve_amount_and_purpose(user, ser.validated_data)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        invoice      = _generate_invoice()
        callback_url = _get_callback_url(request, '/api/payment/nagad/callback/')

        nagad_resp = nagad_service.initiate_payment(
            order_id=invoice,
            amount=str(amount),
            callback_url=callback_url,
        )

        if 'error' in nagad_resp:
            return Response({'error': nagad_resp['error']}, status=status.HTTP_502_BAD_GATEWAY)

        raw = {
            'tutor_id':      data.get('tutor_id'),
            'tuition_id':    data.get('tuition_id'),
            'commission_id': related.pk if purpose == 'commission' else None,
            'invoice':       invoice,
            'nagad_init':    nagad_resp,
        }

        Payment.objects.create(
            user=user,
            amount=amount,
            method='nagad',
            status='initiated',
            purpose=purpose,
            payment_id=invoice,
            raw_response=raw,
        )

        return Response({
            'payment_id':   invoice,
            'redirect_url': nagad_resp.get('callBackUrl'),
            'amount':       str(amount),
            'status':       'initiated',
        }, status=status.HTTP_201_CREATED)


class NagadCallbackView(APIView):
    """
    POST /api/payment/nagad/callback/
    Nagad POSTs here after user completes payment.
    Verifies signature and updates payment status.
    """
    permission_classes = []

    def post(self, request):
        ser = NagadCallbackSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        callback_data  = ser.validated_data
        order_id       = callback_data['order_id']
        payment_ref_id = callback_data['payment_ref_id']
        cb_status      = callback_data['status']

        if not nagad_service.validate_callback_signature(request.data):
            logger.warning("Nagad callback signature validation FAILED for order %s", order_id)
            return Response({'error': 'Invalid signature.'}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.filter(payment_id=order_id).first()
        if not payment:
            return Response({'error': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)

        if payment.status == 'completed':
            return Response({'message': 'Already processed.'})

        if cb_status != 'Success':
            payment.status = 'failed'
            payment.raw_response = {**payment.raw_response, 'callback': request.data}
            payment.save()
            return Response({'error': 'Payment not successful.'}, status=status.HTTP_402_PAYMENT_REQUIRED)

        verify_resp = nagad_service.verify_payment(payment_ref_id)

        if nagad_service.is_successful(verify_resp):
            with transaction.atomic():
                payment.status         = 'completed'
                payment.transaction_id = verify_resp.get('merchantOrderId', payment_ref_id)
                payment.raw_response   = {**payment.raw_response, 'callback': request.data, 'verify': verify_resp}
                payment.save()
                _finalize_payment(payment, nagad_data=verify_resp)

            return Response({'message': 'Payment verified and recorded.'})

        payment.status       = 'failed'
        payment.raw_response = {**payment.raw_response, 'callback': request.data, 'verify': verify_resp}
        payment.save()
        return Response({'error': 'Nagad verification failed.'}, status=status.HTTP_402_PAYMENT_REQUIRED)


# ──────────────────────────────────────────
# Info Views
# ──────────────────────────────────────────

class MyPaymentsView(APIView):
    """GET /api/payment/history/ — List current user's payment history."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(user=request.user)
        return Response(PaymentSerializer(payments, many=True).data)


class MyUnlockedContactsView(APIView):
    """GET /api/payment/contacts/ — Contacts unlocked by the student."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'student':
            return Response({'error': 'Only students can view unlocked contacts.'}, status=status.HTTP_403_FORBIDDEN)
        unlocks = ContactUnlock.objects.filter(student=request.user).select_related('tutor', 'payment')
        return Response(ContactUnlockSerializer(unlocks, many=True).data)


class MyCommissionsView(APIView):
    """GET /api/payment/commissions/ — Commissions owed/paid by the tutor."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'tutor':
            return Response({'error': 'Only tutors can view commissions.'}, status=status.HTTP_403_FORBIDDEN)
        comms = Commission.objects.filter(tutor=request.user).select_related('tuition', 'payment')
        return Response(CommissionSerializer(comms, many=True).data)
