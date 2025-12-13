from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def avatar_upload_path(instance, filename):
    return f'avatars/{instance.user.id}/{filename}'


class UserProfile(models.Model):
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_quiz_admin = models.BooleanField(default=False)
    avatar = models.URLField(max_length=500, blank=True, null=True)
    avatar_file = models.ImageField(upload_to=avatar_upload_path, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    preferred_difficulty = models.CharField(max_length=20, choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ], default='medium')
    preferred_category = models.ForeignKey(
        'quiz.Category', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='preferred_by_users'
    )
    questions_per_quiz = models.IntegerField(default=10, choices=[
        (5, '5 Questions'),
        (10, '10 Questions'),
        (15, '15 Questions'),
        (20, '20 Questions'),
    ])
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    email_notifications = models.BooleanField(default=True)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_quiz_date = models.DateField(null=True, blank=True)
    total_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_avatar_url(self):
        if self.avatar_file:
            return self.avatar_file.url
        if self.avatar:
            return self.avatar
        return f"https://ui-avatars.com/api/?name={self.user.username}&background=3b82f6&color=fff&size=128"
