from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [('student', 'Student'), ('tutor', 'Tutor'), ('admin', 'Admin')]
    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female'), ('other', 'Other')]

    role     = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone    = models.CharField(max_length=15, unique=True)
    gender   = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)

    # Profile image
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)

    # Tutor-specific academic info
    school     = models.CharField(max_length=200, blank=True)
    college    = models.CharField(max_length=200, blank=True)
    university = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=200, blank=True)
    subjects   = models.CharField(max_length=500, blank=True, help_text="Comma separated")
    location   = models.CharField(max_length=200, blank=True)

    # ID document image (NID / Student ID)
    id_image = models.ImageField(upload_to='id_docs/', null=True, blank=True)

    # Admin control
    profile_approved = models.BooleanField(default=True)
    banned           = models.BooleanField(default=False)
    theme            = models.CharField(max_length=20, default='dark')

    USERNAME_FIELD   = 'phone'
    REQUIRED_FIELDS  = ['username', 'email']

    def get_subjects_list(self):
        return [s.strip() for s in self.subjects.split(',') if s.strip()]

    def profile_image_url(self):
        if self.profile_image:
            return self.profile_image.url
        return None

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"


class OTPVerification(models.Model):
    """
    Stores a hashed OTP for phone-based signup verification.
    One record per phone number; overwritten on each new OTP send.
    The actual user account is created only after OTP is verified.
    """
    phone       = models.CharField(max_length=20, unique=True, db_index=True)
    otp_hash    = models.CharField(max_length=128)
    expires_at  = models.DateTimeField()
    attempts    = models.PositiveSmallIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'OTP Verification'
        verbose_name_plural = 'OTP Verifications'

    def __str__(self):
        status = 'verified' if self.is_verified else 'pending'
        return f"OTP({self.phone}) — {status}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('success', 'success'), ('danger', 'danger'),
        ('warn', 'warn'), ('accent', 'accent'), ('info', 'info'),
    ]
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    text       = models.TextField()
    notif_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='accent')
    read       = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notif for {self.user}: {self.text[:40]}"
