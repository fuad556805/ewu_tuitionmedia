from django.db import models
from accounts.models import User
from posts.models import Post


class TuitionRequest(models.Model):
    STATUS = [('pending','Pending'),('accepted','Accepted'),('rejected','Rejected')]
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True, related_name='requests')
    subject = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['tutor', 'student', 'post']

    def __str__(self):
        return f"{self.tutor} → {self.student} ({self.status})"


class Tuition(models.Model):
    STATUS = [('active','Active'),('completed','Completed'),('cancelled','Cancelled')]
    COMM_STATUS = [('pending','Pending'),('proof_uploaded','Proof Uploaded'),('paid','Paid')]
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tuitions_as_tutor')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tuitions_as_student')
    subject = models.CharField(max_length=200)
    salary = models.PositiveIntegerField(default=0)
    commission = models.PositiveIntegerField(default=0)
    commission_status = models.CharField(max_length=20, choices=COMM_STATUS, default='pending')
    month = models.CharField(max_length=50)
    status = models.CharField(max_length=15, choices=STATUS, default='active')
    proof_image = models.ImageField(upload_to='proofs/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tutor} teaches {self.student} — {self.subject}"
