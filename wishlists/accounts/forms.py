# Django
from django import forms
from django.contrib.auth.models import User


class LoginForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('email', 'password')
        widgets = {
            'email': forms.EmailInput(
                attrs={
                    'placeholder': 'Enter email address',
                    'class': 'form-control'
                }
            ),
            'password': forms.PasswordInput(
                attrs={
                    'placeholder': 'Enter password',
                    'class': 'form-control'
                }
            ),
        }