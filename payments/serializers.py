from rest_framework import serializers
from .models import Payment, ContactUnlock, Commission


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model   = Payment
        fields  = [
            'id', 'user', 'amount', 'method', 'status',
            'purpose', 'transaction_id', 'payment_id',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class ContactUnlockSerializer(serializers.ModelSerializer):
    tutor_name    = serializers.CharField(source='tutor.get_full_name', read_only=True)
    tutor_phone   = serializers.CharField(source='tutor.phone', read_only=True)

    class Meta:
        model  = ContactUnlock
        fields = ['id', 'student', 'tutor', 'tutor_name', 'tutor_phone', 'payment', 'unlocked_at']
        read_only_fields = fields


class CommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Commission
        fields = ['id', 'tutor', 'tuition', 'amount', 'paid', 'payment', 'due_at', 'paid_at']
        read_only_fields = fields


# ── Request payload serializers ──

class BkashCreateSerializer(serializers.Serializer):
    METHOD_CHOICES = [('bkash', 'bKash'), ('nagad', 'Nagad')]

    tutor_id = serializers.IntegerField(required=False, help_text="Required for contact unlock")
    tuition_id = serializers.IntegerField(required=False, help_text="Required for commission payment")
    purpose  = serializers.ChoiceField(choices=['contact_unlock', 'commission'])
    method   = serializers.ChoiceField(choices=['bkash', 'nagad'])

    def validate(self, data):
        purpose = data.get('purpose')
        if purpose == 'contact_unlock' and not data.get('tutor_id'):
            raise serializers.ValidationError("tutor_id is required for contact unlock.")
        if purpose == 'commission' and not data.get('tuition_id'):
            raise serializers.ValidationError("tuition_id is required for commission payment.")
        return data


class BkashExecuteSerializer(serializers.Serializer):
    payment_id = serializers.CharField()


class NagadCallbackSerializer(serializers.Serializer):
    payment_ref_id = serializers.CharField()
    order_id       = serializers.CharField()
    sensitiveData  = serializers.CharField()
    signature      = serializers.CharField()
    status         = serializers.CharField()
