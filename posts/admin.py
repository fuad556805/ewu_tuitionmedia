from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['subject', 'student', 'status', 'budget', 'created_at']
    list_filter = ['status']
    actions = ['approve_posts', 'reject_posts']

    def approve_posts(self, request, queryset):
        queryset.update(status='active')
    def reject_posts(self, request, queryset):
        queryset.update(status='rejected')
