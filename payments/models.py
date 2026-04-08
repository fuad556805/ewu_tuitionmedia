from django.db import models
from accounts.models import User
from tuitions.models import Tuition


class Payment(models.Model):
    METHOD_CHOICES = [('bkash', 'bKash'), ('nagad', 'Nagad')]
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('pending',   'Pending'),
        ('completed', 'Completed'),
        ('failed',    'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    PURPOSE_CHOICES = [
        ('contact_unlock', 'Contact Unlock'),
        ('commission',     'Commission'),
    ]

    user           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    method         = models.CharField(max_length=10, choices=METHOD_CHOICES)
    status         = models.CharField(max_length=15, choices=STATUS_CHOICES, default='initiated')
    purpose        = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_id     = models.CharField(max_length=100, blank=True, unique=True)
    raw_response   = models.JSONField(default=dict, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_id']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.user} | {self.method} | {self.amount} BDT | {self.status}"


class ContactUnlock(models.Model):
    student     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlocked_contacts')
    tutor       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlocked_by')
    payment     = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, related_name='contact_unlock')
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'tutor']

    def __str__(self):
        return f"{self.student} unlocked {self.tutor}"


class Commission(models.Model):
    tutor   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commissions')
    tuition = models.OneToOneField(Tuition, on_delete=models.CASCADE, related_name='commission_record')
    amount  = models.DecimalField(max_digits=10, decimal_places=2)
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='commission')
    paid    = models.BooleanField(default=False)
    due_at  = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-due_at']

    def __str__(self):
        status = 'Paid' if self.paid else 'Unpaid'
        return f"Commission {self.tutor} | {self.amount} BDT | {status}"
