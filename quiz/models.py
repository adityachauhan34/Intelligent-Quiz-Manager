from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='book-open')
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name


class Subcategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    
    class Meta:
        verbose_name_plural = "Subcategories"
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Quiz(models.Model):
    title = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=20, choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ])
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='quizzes')
    time_limit = models.IntegerField(default=600)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural = "Quizzes"
    
    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_answer = models.CharField(max_length=1, choices=[
        ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')
    ])
    explanation = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Q{self.order + 1}: {self.question_text[:50]}..."


class QuizAttempt(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    current_question = models.IntegerField(default=0)
    time_remaining = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} ({self.status})"


class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=1, blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"{self.attempt.user.username} - Q{self.question.order + 1}: {self.selected_answer}"
