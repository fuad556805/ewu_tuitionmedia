from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['subject', 'location', 'budget', 'classes', 'schedule', 'details']
        widgets = {
            'details': forms.Textarea(attrs={'rows': 3}),
        }
