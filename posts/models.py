'''E:\cse347Project\tuitionmedia\posts\models.py'''
from django.db import models
from accounts.models import User

class Post(models.Model):
    STATUS = [('pending_approval','Pending Approval'),('active','Active'),('rejected','Rejected'),('closed','Closed')]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    subject = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    budget = models.PositiveIntegerField(help_text="BDT per month")
    classes = models.CharField(max_length=100, blank=True)
    schedule = models.CharField(max_length=200, blank=True)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending_approval')
    request_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} by {self.student}"
