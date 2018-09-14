# Django
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm  # , AuthenticationForm


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


class RegistrationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.EmailInput(
                attrs={
                    'placeholder': 'Enter email address',
                    'class': 'form-control'
                }),
            'password1': forms.PasswordInput(
                attrs={
                    'placeholder': 'Enter your password',
                    'class': 'form-control'
                }),
            'password2': forms.PasswordInput(
                attrs={
                    'placeholder': 'Enter the same password again',
                    'class': 'form-control'
                })}

    def clean_email(self):
        data = self.cleaned_data['username']
        return data
