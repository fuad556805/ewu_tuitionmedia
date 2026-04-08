from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[('student','Student'),('tutor','Tutor')])

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'password', 'role']

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Phone already registered.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['phone']
        user.set_password(self.cleaned_data['password'])
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    phone = forms.CharField(max_length=15)
    password = forms.CharField(widget=forms.PasswordInput)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'education', 'location', 'subjects']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.profile_approved = False  # needs admin approval
        if commit:
            user.save()
        return user


class ForgotPasswordForm(forms.Form):
    phone = forms.CharField(max_length=15)

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Phone not registered.")
        return phone


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, min_length=6)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cd = super().clean()
        if cd.get('new_password') != cd.get('confirm_password'):
            raise forms.ValidationError("Passwords don't match.")
        return cd


class ThemeForm(forms.Form):
    theme = forms.ChoiceField(choices=[('dark','dark'),('ocean','ocean'),('sunset','sunset')])
