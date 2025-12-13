from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('browse/', views.browse, name='browse'),
    path('category/<int:category_id>/', views.category, name='category'),
    path('start/', views.start_quiz, name='start'),
    path('take/<int:attempt_id>/', views.take_quiz, name='take'),
    path('answer/<int:attempt_id>/', views.answer, name='answer'),
    path('submit/<int:attempt_id>/', views.submit_quiz, name='submit'),
    path('results/<int:attempt_id>/', views.results, name='results'),
    path('history/', views.history, name='history'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('admin-panel/users/<int:user_id>/toggle-admin/', views.toggle_admin, name='toggle_admin'),
    path('admin-panel/categories/', views.admin_categories, name='admin_categories'),
    path('admin-panel/categories/add/', views.add_category, name='add_category'),
    path('admin-panel/categories/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('admin-panel/categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    path('admin-panel/subcategories/', views.admin_subcategories, name='admin_subcategories'),
    path('admin-panel/subcategories/add/', views.add_subcategory, name='add_subcategory'),
    path('admin-panel/subcategories/<int:subcategory_id>/edit/', views.edit_subcategory, name='edit_subcategory'),
    path('admin-panel/subcategories/<int:subcategory_id>/delete/', views.delete_subcategory, name='delete_subcategory'),
    path('admin-panel/quizzes/', views.admin_quizzes, name='admin_quizzes'),
    path('admin-panel/quizzes/<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),
    path('admin-panel/attempts/', views.admin_attempts, name='admin_attempts'),
    path('admin-panel/attempts/<int:attempt_id>/', views.view_attempt, name='view_attempt'),
    path('admin-panel/attempts/<int:attempt_id>/delete/', views.delete_attempt, name='delete_attempt'),
]
