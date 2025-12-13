import os
import json
import logging
from google import genai
from google.genai import types

# IMPORTANT: Using Gemini API for quiz generation
# Note that the newest Gemini model series is "gemini-2.5-flash"
# do not change this unless explicitly requested by the user

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)


def generate_quiz_questions(subcategory_name, difficulty, num_questions=10):
    if not client:
        logging.warning("Gemini API key not configured, using fallback questions")
        return generate_fallback_questions(subcategory_name, difficulty, num_questions)
    
    try:
        prompt = f"""Generate {num_questions} multiple-choice quiz questions about {subcategory_name} at {difficulty} difficulty level.

Return a JSON object with this exact structure:
{{
    "questions": [
        {{
            "question": "The question text",
            "option_a": "First option",
            "option_b": "Second option", 
            "option_c": "Third option",
            "option_d": "Fourth option",
            "correct_answer": "A",
            "explanation": "Brief explanation of why this answer is correct"
        }}
    ]
}}

Make the questions educational and engaging. Ensure only one answer is correct.
For {difficulty} difficulty:
- Easy: Basic concepts, straightforward questions
- Medium: Requires some knowledge and thinking
- Hard: Advanced concepts, requires deep understanding"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        result = json.loads(response.text)
        return result.get("questions", [])
    
    except Exception as e:
        logging.error(f"Error generating questions: {e}")
        return generate_fallback_questions(subcategory_name, difficulty, num_questions)


def generate_fallback_questions(subcategory_name, difficulty, num_questions):
    questions = []
    for i in range(num_questions):
        questions.append({
            "question": f"Sample question {i+1} about {subcategory_name} ({difficulty} difficulty)",
            "option_a": "Option A",
            "option_b": "Option B",
            "option_c": "Option C",
            "option_d": "Option D",
            "correct_answer": "A",
            "explanation": f"This is a sample explanation for question {i+1}. Please configure Gemini API key for real questions."
        })
    return questions
