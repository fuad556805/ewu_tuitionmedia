from django.contrib import admin
from .models import TuitionRequest, Tuition

@admin.register(TuitionRequest)
class TuitionRequestAdmin(admin.ModelAdmin):
    list_display = ['tutor', 'student', 'subject', 'status', 'created_at']
    list_filter = ['status']

@admin.register(Tuition)
class TuitionAdmin(admin.ModelAdmin):
    list_display = ['tutor', 'student', 'subject', 'salary', 'commission', 'commission_status', 'status']
    list_filter = ['commission_status', 'status']
