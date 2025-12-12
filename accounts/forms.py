from django import forms
from django.contrib.auth.models import User
from .models import Profile

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget= forms.PasswordInput)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username','email','password','role']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['display_name','bio','phone']
        widgets = {
            'bio': forms.Textarea(attrs={'rows':4}),
        }
