from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'


class LoginForm(forms.Form):
    username_or_email = forms.CharField(
        label='Username or Email',
        max_length=254,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your username or email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'})
    )
    remember_me = forms.BooleanField(required=False, initial=False)
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs['class'] = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
    
    def clean(self):
        username_or_email = self.cleaned_data.get('username_or_email')
        password = self.cleaned_data.get('password')
        
        if username_or_email and password:
            from django.contrib.auth import authenticate
            user = User.objects.filter(email=username_or_email).first()
            if user:
                username = user.username
            else:
                username = username_or_email
            
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError('Invalid username/email or password.')
            elif not self.user_cache.is_active:
                raise forms.ValidationError('This account is inactive.')
        
        return self.cleaned_data
    
    def get_user(self):
        return self.user_cache


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
        self.fields['username'].widget.attrs['placeholder'] = 'Enter your username'
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter your first name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter your last name'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter your email'
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This username is already taken.')
        return username


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar_file', 'avatar', 'bio', 'preferred_difficulty', 'preferred_category', 
                  'questions_per_quiz', 'email_notifications']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'avatar_file': forms.FileInput(attrs={'accept': 'image/*'}),
        }
    
    def clean_avatar_file(self):
        avatar = self.cleaned_data.get('avatar_file')
        if avatar:
            if avatar.size > 2 * 1024 * 1024:
                raise forms.ValidationError('Avatar file size must be less than 2MB.')
        return avatar
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'email_notifications':
                field.widget.attrs['class'] = 'h-5 w-5 text-primary-600 rounded focus:ring-primary-500'
            elif field_name == 'avatar_file':
                field.widget.attrs['class'] = 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100'
            else:
                field.widget.attrs['class'] = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
        
        self.fields['avatar_file'].label = 'Upload Avatar'
        self.fields['avatar'].widget.attrs['placeholder'] = 'Or enter image URL (e.g., https://example.com/avatar.jpg)'
        self.fields['bio'].widget.attrs['placeholder'] = 'Tell us about yourself...'


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your registered email'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['class'] = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('No account found with this email address.')
        return email


class ResetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter new password'})
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('Passwords do not match.')
            if len(password1) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')
        return cleaned_data
