#for adding fields to the form
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
from blog.models import Category

class UserRegisterForm(UserCreationForm):
    email=forms.EmailField()
    contact_number=forms.CharField()
    
    class Meta:
        model=User
        fields=['username', 'email', 'password1', 'password2']
        
class UserUpdateForm(forms.ModelForm):
    email=forms.EmailField()
    
    class Meta:
        model=User
        fields=['username', 'email']
    
class ProfileUpdateForm(forms.ModelForm):
    contact_number=forms.CharField()

    class Meta:
        model=Profile
        fields=['contact_number', 'image']

class UserPreferencesForm(forms.Form):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),  # Fetch all categories
        widget=forms.CheckboxSelectMultiple,  # Display as checkboxes
        required=False
    )