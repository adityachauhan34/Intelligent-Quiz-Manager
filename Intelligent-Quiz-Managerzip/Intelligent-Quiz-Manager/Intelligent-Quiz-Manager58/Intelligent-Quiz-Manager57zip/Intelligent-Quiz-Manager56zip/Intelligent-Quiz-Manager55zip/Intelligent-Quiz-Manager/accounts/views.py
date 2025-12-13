import os
import secrets
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SignUpForm, LoginForm, UserForm, ProfileForm, ForgotPasswordForm, ResetPasswordForm
from .models import UserProfile

password_reset_tokens = {}


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('quiz:dashboard')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('quiz:dashboard')
    else:
        form = SignUpForm()
    
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('quiz:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            remember = form.cleaned_data.get('remember_me')
            if not remember:
                request.session.set_expiry(0)
            display_name = user.get_full_name() or user.username
            messages.success(request, f'Welcome back, {display_name}!')
            next_url = request.GET.get('next', 'quiz:dashboard')
            return redirect(next_url)
    else:
        form = LoginForm(request)
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('quiz:index')


@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            if 'avatar_file' in request.FILES:
                if profile.avatar_file:
                    old_path = profile.avatar_file.path
                    if os.path.exists(old_path):
                        os.remove(old_path)
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)
    
    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    })


@login_required
def remove_avatar(request):
    if request.method == 'POST':
        profile = request.user.profile
        if profile.avatar_file:
            if profile.avatar_file.path and os.path.exists(profile.avatar_file.path):
                os.remove(profile.avatar_file.path)
            profile.avatar_file = None
        profile.avatar = None
        profile.save()
        messages.success(request, 'Avatar removed successfully!')
    return redirect('accounts:profile')


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect('quiz:dashboard')
    
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            token = secrets.token_urlsafe(32)
            password_reset_tokens[token] = email
            return redirect('accounts:reset_password', token=token)
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'accounts/forgot_password.html', {'form': form})


def reset_password_view(request, token):
    if request.user.is_authenticated:
        return redirect('quiz:dashboard')
    
    email = password_reset_tokens.get(token)
    if not email:
        messages.error(request, 'Invalid or expired reset link.')
        return redirect('accounts:forgot_password')
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('accounts:forgot_password')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            del password_reset_tokens[token]
            messages.success(request, 'Password reset successfully! Please log in with your new password.')
            return redirect('accounts:login')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'accounts/reset_password.html', {'form': form, 'email': email})
