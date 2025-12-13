import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from quiz.models import Category, Subcategory


def seed_database():
    admin_user = User.objects.filter(username='admin').first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@quizhub.com',
            password='admin123'
        )
        UserProfile.objects.create(user=admin_user, is_quiz_admin=True)
        print("Created admin user: admin@quizhub.com / admin123")
    
    if Category.objects.count() == 0:
        categories_data = [
            {
                'name': 'Academic',
                'description': 'Test your knowledge in academic subjects like Physics, Chemistry, Mathematics, and more.',
                'icon': 'book-open',
                'subcategories': [
                    {'name': 'Physics', 'description': 'Mechanics, thermodynamics, electromagnetism, and modern physics'},
                    {'name': 'Chemistry', 'description': 'Organic, inorganic, and physical chemistry concepts'},
                    {'name': 'Mathematics', 'description': 'Algebra, calculus, geometry, and statistics'},
                    {'name': 'Biology', 'description': 'Cell biology, genetics, ecology, and human anatomy'},
                    {'name': 'History', 'description': 'World history, ancient civilizations, and modern events'},
                    {'name': 'Geography', 'description': 'Countries, capitals, physical and human geography'}
                ]
            },
            {
                'name': 'Entertainment',
                'description': 'Fun quizzes about movies, music, sports, games, and pop culture.',
                'icon': 'film',
                'subcategories': [
                    {'name': 'Movies', 'description': 'Classic films, blockbusters, directors, and actors'},
                    {'name': 'Music', 'description': 'Artists, albums, genres, and music history'},
                    {'name': 'Sports', 'description': 'Football, basketball, cricket, Olympics, and more'},
                    {'name': 'Video Games', 'description': 'Gaming history, popular titles, and gaming culture'},
                    {'name': 'Television', 'description': 'TV shows, series, actors, and streaming content'}
                ]
            },
            {
                'name': 'General Knowledge',
                'description': 'Broaden your horizons with quizzes on various topics and trivia.',
                'icon': 'sun',
                'subcategories': [
                    {'name': 'Science & Nature', 'description': 'Scientific discoveries, natural phenomena, and the environment'},
                    {'name': 'Technology', 'description': 'Computers, internet, innovations, and tech companies'},
                    {'name': 'Current Affairs', 'description': 'Recent news, global events, and trending topics'},
                    {'name': 'Art & Literature', 'description': 'Famous artists, literary works, and cultural movements'},
                    {'name': 'Food & Cuisine', 'description': 'World cuisines, cooking, and culinary traditions'}
                ]
            }
        ]
        
        for cat_data in categories_data:
            category = Category.objects.create(
                name=cat_data['name'],
                description=cat_data['description'],
                icon=cat_data['icon']
            )
            
            for sub_data in cat_data['subcategories']:
                Subcategory.objects.create(
                    name=sub_data['name'],
                    description=sub_data['description'],
                    category=category
                )
        
        print("Created categories and subcategories")
    
    print("Database seeded successfully!")


if __name__ == '__main__':
    seed_database()
