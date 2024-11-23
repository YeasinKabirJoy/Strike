from allauth.account.forms import LoginForm,SignupForm
from django import forms
from .models import Profile

class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login'].widget = forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['password'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })


class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })

        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['name', 'image', 'email', 'location', 'bio']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={
                'id':'image-input',
                'class': 'form-control',
                'accept': 'image/*',  # Accepts only image files
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={
                'id':'bio-input',
                'class': 'form-control',
                'style': 'height: 150px;',  # Set the desired height
            }),
        }