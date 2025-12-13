import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from .models import Category, Subcategory, Quiz, Question, QuizAttempt, UserAnswer
from .forms import QuizSettingsForm, CategoryForm, SubcategoryForm
from .openai_service import generate_quiz_questions


def is_admin(user):
    return user.is_superuser or (hasattr(user, 'profile') and user.profile.is_quiz_admin)


def index(request):
    categories = Category.objects.all()
    return render(request, 'quiz/index.html', {'categories': categories})


@login_required
def dashboard(request):
    from django.db.models import Sum, Count, Q
    from accounts.models import UserProfile
    from datetime import date, timedelta
    
    recent_attempts = QuizAttempt.objects.filter(user=request.user).order_by('-started_at')[:5]
    completed_attempts = QuizAttempt.objects.filter(user=request.user, status='completed')
    incomplete_attempts = QuizAttempt.objects.filter(user=request.user, status='in_progress')
    completed_count = completed_attempts.count()
    incomplete_count = incomplete_attempts.count()
    
    total_score = 0
    total_questions = 0
    for attempt in completed_attempts:
        total_score += attempt.score
        total_questions += attempt.total_questions
    
    avg_score = round((total_score / total_questions * 100)) if total_questions > 0 else 0
    
    profile = request.user.profile if hasattr(request.user, 'profile') else None
    if not profile:
        profile = UserProfile.objects.create(user=request.user)
    
    user_rankings = []
    all_profiles = UserProfile.objects.select_related('user').filter(
        total_points__gt=0
    ).order_by('-total_points')[:10]
    
    user_rank = None
    for idx, p in enumerate(all_profiles, 1):
        user_attempts = QuizAttempt.objects.filter(user=p.user, status='completed')
        user_completed = user_attempts.count()
        
        user_total_score = 0
        user_total_questions = 0
        for att in user_attempts:
            user_total_score += att.score
            user_total_questions += att.total_questions
        
        user_score_pct = round((user_total_score / user_total_questions * 100)) if user_total_questions > 0 else 0
        
        user_rankings.append({
            'rank': idx,
            'username': p.user.username,
            'quizzes': user_completed,
            'score_pct': user_score_pct,
            'total_points': p.total_points,
            'is_current_user': p.user.id == request.user.id
        })
        if p.user.id == request.user.id:
            user_rank = idx
    
    if user_rank is None and profile.total_points > 0:
        all_profiles_list = list(UserProfile.objects.filter(total_points__gt=0).order_by('-total_points'))
        for idx, p in enumerate(all_profiles_list, 1):
            if p.user_id == request.user.id:
                user_rank = idx
                break
    
    return render(request, 'quiz/dashboard.html', {
        'recent_attempts': recent_attempts,
        'completed_count': completed_count,
        'incomplete_count': incomplete_count,
        'avg_score': avg_score,
        'current_streak': profile.current_streak,
        'longest_streak': profile.longest_streak,
        'total_points': profile.total_points,
        'user_rank': user_rank or 'N/A',
        'rankings': user_rankings,
    })


@login_required
def browse(request):
    categories = Category.objects.all()
    return render(request, 'quiz/browse.html', {'categories': categories})


@login_required
def category(request, category_id):
    cat = get_object_or_404(Category, id=category_id)
    return render(request, 'quiz/category.html', {'category': cat})


@login_required
def start_quiz(request):
    if request.method == 'POST':
        form = QuizSettingsForm(request.POST)
        if form.is_valid():
            subcategory = get_object_or_404(Subcategory, id=form.cleaned_data['subcategory_id'])
            difficulty = form.cleaned_data['difficulty']
            num_questions = int(form.cleaned_data['num_questions'])
            
            # Clean up any abandoned "in_progress" attempts for this user
            QuizAttempt.objects.filter(
                user=request.user, 
                status='in_progress'
            ).delete()
            
            questions = generate_quiz_questions(subcategory.name, difficulty, num_questions)
            
            if not questions:
                messages.error(request, 'Unable to generate quiz questions. Please try again.')
                return render(request, 'quiz/start.html', {'form': form})
            
            quiz = Quiz.objects.create(
                title=f"{subcategory.name} Quiz - {difficulty.capitalize()}",
                difficulty=difficulty,
                subcategory=subcategory,
                time_limit=len(questions) * 60
            )
            
            for i, q in enumerate(questions):
                Question.objects.create(
                    quiz=quiz,
                    question_text=q['question'],
                    option_a=q['option_a'],
                    option_b=q['option_b'],
                    option_c=q['option_c'],
                    option_d=q['option_d'],
                    correct_answer=q['correct_answer'],
                    explanation=q.get('explanation', ''),
                    order=i
                )
            
            attempt = QuizAttempt.objects.create(
                user=request.user,
                quiz=quiz,
                total_questions=len(questions),
                time_remaining=quiz.time_limit,
                status='in_progress'
            )
            
            return redirect('quiz:take', attempt_id=attempt.id)
    else:
        form = QuizSettingsForm()
    
    category_id = request.GET.get('category_id')
    subcategory_id = request.GET.get('subcategory_id')
    
    if subcategory_id:
        form.fields['subcategory_id'].initial = subcategory_id
    
    return render(request, 'quiz/start.html', {'form': form, 'category_id': category_id})


@login_required
def take_quiz(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    
    if attempt.user != request.user:
        messages.error(request, 'Access denied.')
        return redirect('quiz:dashboard')
    
    if attempt.status == 'completed':
        return redirect('quiz:results', attempt_id=attempt.id)
    
    questions = Question.objects.filter(quiz=attempt.quiz).order_by('order')
    answered = {str(ua.question_id): ua.selected_answer for ua in attempt.answers.all()}
    answered_json = json.dumps(answered)
    
    return render(request, 'quiz/take.html', {
        'attempt': attempt,
        'questions': questions,
        'answered': answered,
        'answered_json': answered_json,
    })


@login_required
def answer(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    
    if attempt.user != request.user:
        return HttpResponseForbidden('Access denied')
    
    if attempt.status == 'completed':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'completed'})
        return redirect('quiz:results', attempt_id=attempt.id)
    
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        selected_answer = request.POST.get('answer')
        current_q = request.POST.get('current_question', 0)
        time_remaining = request.POST.get('time_remaining')
        
        if question_id and selected_answer:
            try:
                question = Question.objects.get(id=question_id, quiz=attempt.quiz)
                user_answer, created = UserAnswer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={
                        'selected_answer': selected_answer,
                        'is_correct': selected_answer == question.correct_answer
                    }
                )
            except Question.DoesNotExist:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'Invalid question'}, status=400)
                return HttpResponseForbidden('Invalid question')
        
        # Re-fetch the attempt to check if it was completed by another request (race condition fix)
        attempt.refresh_from_db()
        if attempt.status == 'completed':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'completed'})
            return redirect('quiz:results', attempt_id=attempt.id)
        
        attempt.current_question = int(current_q) if current_q else 0
        if time_remaining:
            try:
                attempt.time_remaining = int(time_remaining)
            except (ValueError, TypeError):
                pass
        attempt.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'saved'})
    
    return redirect('quiz:take', attempt_id=attempt.id)


@login_required
def submit_quiz(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    
    if attempt.user != request.user:
        messages.error(request, 'Access denied.')
        return redirect('quiz:dashboard')
    
    if attempt.status == 'completed':
        return redirect('quiz:results', attempt_id=attempt.id)
    
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        selected_answer = request.POST.get('answer')
        
        if question_id and selected_answer:
            try:
                question = Question.objects.get(id=question_id, quiz=attempt.quiz)
                UserAnswer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={
                        'selected_answer': selected_answer,
                        'is_correct': selected_answer == question.correct_answer
                    }
                )
            except Question.DoesNotExist:
                pass
        
        correct_count = UserAnswer.objects.filter(attempt=attempt, is_correct=True).count()
        
        attempt.score = correct_count
        attempt.status = 'completed'
        attempt.completed_at = timezone.now()
        attempt.save()
        
        from accounts.models import UserProfile
        from datetime import date
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        today = date.today()
        
        if attempt.quiz.difficulty == 'easy':
            points_per_correct = 10
        elif attempt.quiz.difficulty == 'medium':
            points_per_correct = 15
        else:
            points_per_correct = 20
        points_earned = correct_count * points_per_correct
        profile.total_points += points_earned
        
        if profile.last_quiz_date:
            days_diff = (today - profile.last_quiz_date).days
            if days_diff == 0:
                pass
            elif days_diff == 1:
                profile.current_streak += 1
            else:
                profile.current_streak = 1
        else:
            profile.current_streak = 1
        
        if profile.current_streak > profile.longest_streak:
            profile.longest_streak = profile.current_streak
        
        profile.last_quiz_date = today
        profile.save()
    
    return redirect('quiz:results', attempt_id=attempt.id)


@login_required
def results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    
    if attempt.user != request.user and not is_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('quiz:dashboard')
    
    questions = Question.objects.filter(quiz=attempt.quiz).order_by('order')
    user_answers = {ua.question_id: ua for ua in attempt.answers.all()}
    
    results_data = []
    for q in questions:
        ua = user_answers.get(q.id)
        results_data.append({
            'question': q,
            'user_answer': ua.selected_answer if ua else None,
            'is_correct': ua.is_correct if ua else False,
            'explanation': q.explanation
        })
    
    percentage = round((attempt.score / attempt.total_questions) * 100) if attempt.total_questions > 0 else 0
    
    time_taken = "N/A"
    if attempt.completed_at and attempt.started_at:
        duration = attempt.completed_at - attempt.started_at
        total_seconds = int(duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        time_taken = f"{minutes}m {seconds}s"
    
    return render(request, 'quiz/results.html', {
        'attempt': attempt,
        'results_data': results_data,
        'percentage': percentage,
        'time_taken': time_taken,
    })


@login_required
def history(request):
    attempts = QuizAttempt.objects.filter(user=request.user).order_by('-started_at')
    return render(request, 'quiz/history.html', {'attempts': attempts})


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_users = User.objects.count()
    total_categories = Category.objects.count()
    total_quizzes = Quiz.objects.count()
    total_attempts = QuizAttempt.objects.filter(status='completed').count()
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    return render(request, 'quiz/admin/dashboard.html', {
        'total_users': total_users,
        'total_categories': total_categories,
        'total_quizzes': total_quizzes,
        'total_attempts': total_attempts,
        'recent_users': recent_users,
    })


@login_required
@user_passes_test(is_admin)
def admin_users(request):
    users = User.objects.order_by('-date_joined')
    return render(request, 'quiz/admin/users.html', {'users': users})


@login_required
@user_passes_test(is_admin)
def toggle_admin(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user == request.user:
            messages.error(request, 'You cannot change your own admin status.')
        else:
            profile, created = user.profile if hasattr(user, 'profile') else (None, False)
            if not profile:
                from accounts.models import UserProfile
                profile = UserProfile.objects.create(user=user)
            profile.is_quiz_admin = not profile.is_quiz_admin
            profile.save()
            messages.success(request, f'Admin status updated for {user.username}.')
    return redirect('quiz:admin_users')


@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    from accounts.forms import UserForm
    target_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {target_user.username} updated successfully.')
            return redirect('quiz:admin_users')
    else:
        form = UserForm(instance=target_user)
    
    return render(request, 'quiz/admin/edit_user.html', {
        'form': form,
        'target_user': target_user,
    })


@login_required
@user_passes_test(is_admin)
def admin_categories(request):
    categories = Category.objects.all()
    return render(request, 'quiz/admin/categories.html', {'categories': categories})


@login_required
@user_passes_test(is_admin)
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully.')
            return redirect('quiz:admin_categories')
    else:
        form = CategoryForm()
    return render(request, 'quiz/admin/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required
@user_passes_test(is_admin)
def edit_category(request, category_id):
    cat = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('quiz:admin_categories')
    else:
        form = CategoryForm(instance=cat)
    return render(request, 'quiz/admin/category_form.html', {'form': form, 'title': 'Edit Category'})


@login_required
@user_passes_test(is_admin)
def delete_category(request, category_id):
    if request.method == 'POST':
        cat = get_object_or_404(Category, id=category_id)
        cat.delete()
        messages.success(request, 'Category deleted.')
    return redirect('quiz:admin_categories')


@login_required
@user_passes_test(is_admin)
def admin_subcategories(request):
    subcategories = Subcategory.objects.select_related('category').order_by('category__name', 'name')
    return render(request, 'quiz/admin/subcategories.html', {'subcategories': subcategories})


@login_required
@user_passes_test(is_admin)
def add_subcategory(request):
    if request.method == 'POST':
        form = SubcategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subcategory added successfully.')
            return redirect('quiz:admin_subcategories')
    else:
        form = SubcategoryForm()
    return render(request, 'quiz/admin/subcategory_form.html', {'form': form, 'title': 'Add Subcategory'})


@login_required
@user_passes_test(is_admin)
def edit_subcategory(request, subcategory_id):
    sub = get_object_or_404(Subcategory, id=subcategory_id)
    if request.method == 'POST':
        form = SubcategoryForm(request.POST, instance=sub)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subcategory updated successfully.')
            return redirect('quiz:admin_subcategories')
    else:
        form = SubcategoryForm(instance=sub)
    return render(request, 'quiz/admin/subcategory_form.html', {'form': form, 'title': 'Edit Subcategory'})


@login_required
@user_passes_test(is_admin)
def delete_subcategory(request, subcategory_id):
    if request.method == 'POST':
        sub = get_object_or_404(Subcategory, id=subcategory_id)
        sub.delete()
        messages.success(request, 'Subcategory deleted.')
    return redirect('quiz:admin_subcategories')


@login_required
@user_passes_test(is_admin)
def admin_quizzes(request):
    quizzes = Quiz.objects.select_related('subcategory', 'subcategory__category').order_by('-created_at')
    return render(request, 'quiz/admin/quizzes.html', {'quizzes': quizzes})


@login_required
@user_passes_test(is_admin)
def delete_quiz(request, quiz_id):
    if request.method == 'POST':
        quiz = get_object_or_404(Quiz, id=quiz_id)
        quiz.delete()
        messages.success(request, 'Quiz deleted successfully.')
    return redirect('quiz:admin_quizzes')


@login_required
@user_passes_test(is_admin)
def admin_attempts(request):
    attempts = QuizAttempt.objects.select_related('user', 'quiz', 'quiz__subcategory').order_by('-started_at')
    return render(request, 'quiz/admin/attempts.html', {'attempts': attempts})


@login_required
@user_passes_test(is_admin)
def view_attempt(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    questions = Question.objects.filter(quiz=attempt.quiz).order_by('order')
    user_answers = {ua.question_id: ua for ua in attempt.answers.all()}
    
    results_data = []
    for q in questions:
        ua = user_answers.get(q.id)
        results_data.append({
            'question': q,
            'user_answer': ua.selected_answer if ua else None,
            'is_correct': ua.is_correct if ua else False,
            'explanation': q.explanation
        })
    
    percentage = round((attempt.score / attempt.total_questions) * 100) if attempt.total_questions > 0 else 0
    
    return render(request, 'quiz/admin/attempt_detail.html', {
        'attempt': attempt,
        'results_data': results_data,
        'percentage': percentage,
    })


@login_required
@user_passes_test(is_admin)
def delete_attempt(request, attempt_id):
    if request.method == 'POST':
        attempt = get_object_or_404(QuizAttempt, id=attempt_id)
        if attempt.status == 'in_progress':
            messages.warning(request, f'Deleted in-progress attempt by {attempt.user.username}.')
        else:
            messages.success(request, 'Attempt deleted successfully.')
        attempt.delete()
    return redirect('quiz:admin_attempts')
