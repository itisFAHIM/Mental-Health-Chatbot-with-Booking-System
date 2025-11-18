from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class PatientSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name*'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name*'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email*'}))
    profile_picture = forms.ImageField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username*'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False) # Get user object without saving to DB
        
        # --- THIS IS THE FIX ---
        # Manually assign the extra fields from the form
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')
        # --- END FIX ---
        
        if commit:
            user.save() # Now save the user with all fields
            Profile.objects.create(
                user=user,
                role='patient',
                profile_picture=self.cleaned_data.get('profile_picture')
            )
        return user

class DoctorSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name*'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name*'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email*'}))
    specialty = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'placeholder': 'Specialty (e.g., Clinical Psychologist)*'}))
    
    profile_picture = forms.ImageField(required=True)
    degree_document = forms.FileField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username*'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # --- THIS IS THE FIX ---
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')
        # --- END FIX ---
        
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                role='doctor',
                is_approved=False,
                specialty=self.cleaned_data.get('specialty'),
                profile_picture=self.cleaned_data.get('profile_picture'),
                degree_document=self.cleaned_data.get('degree_document')
            )
        return user

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('specialty', 'profile_picture')