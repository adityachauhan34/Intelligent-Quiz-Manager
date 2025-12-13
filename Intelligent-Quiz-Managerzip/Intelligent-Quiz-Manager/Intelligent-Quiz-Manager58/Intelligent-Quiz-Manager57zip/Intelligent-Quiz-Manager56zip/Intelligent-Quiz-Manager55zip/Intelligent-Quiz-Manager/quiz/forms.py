from django import forms
from .models import Category, Subcategory


class QuizSettingsForm(forms.Form):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    NUM_QUESTIONS_CHOICES = [
        ('5', '5 Questions'),
        ('10', '10 Questions'),
        ('15', '15 Questions'),
        ('20', '20 Questions'),
    ]
    
    subcategory_id = forms.ChoiceField(label='Select Topic')
    difficulty = forms.ChoiceField(choices=DIFFICULTY_CHOICES, label='Difficulty Level')
    num_questions = forms.ChoiceField(choices=NUM_QUESTIONS_CHOICES, initial='10', label='Number of Questions')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        subcategories = []
        for cat in Category.objects.all():
            for sub in cat.subcategories.all():
                subcategories.append((sub.id, f"{cat.name} - {sub.name}"))
        self.fields['subcategory_id'].choices = subcategories
        
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'


class SubcategoryForm(forms.ModelForm):
    class Meta:
        model = Subcategory
        fields = ['name', 'description', 'category']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
