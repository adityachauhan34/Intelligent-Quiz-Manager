# AI Quiz Hub

## Overview

AI Quiz Hub is an AI-powered quiz application built with Django that dynamically generates quiz questions using Google's Gemini AI. Users can test their knowledge across various categories (Academic, Entertainment, General Knowledge) with configurable difficulty levels. The platform features user authentication, quiz progress tracking, streak systems, leaderboards, and comprehensive admin management capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Django 5.2** serves as the core web framework
- Uses Django's built-in ORM for database operations
- Template-based rendering with Django's template engine
- WhiteNoise middleware for static file serving

### Application Structure
The project follows Django's app-based architecture with two main apps:
- **accounts/** - Handles user authentication, registration, profiles, and preferences
- **quiz/** - Core quiz functionality including models, views, AI integration, and admin features

The main Django project configuration resides in `quiz_project/` containing settings, URL routing, and WSGI/ASGI configurations.

### AI Integration
- **Google Gemini AI** (gemini-2.5-flash model) generates unique quiz questions dynamically
- Questions are created based on topic, difficulty, and user preferences
- Fallback question generation when API is unavailable
- Integration handled in `quiz/openai_service.py`

### Data Models
- **Category** - Top-level quiz categories (Academic, Entertainment, etc.)
- **Subcategory** - Specific topics within categories (Physics, Movies, etc.)
- **Quiz** - Generated quiz instances with difficulty and time limits
- **Question** - Individual multiple-choice questions with options A-D
- **QuizAttempt** - User quiz sessions tracking progress and status
- **UserAnswer** - Individual answer records for each question
- **UserProfile** - Extended user data including preferences, avatars, streaks, and points

### Authentication System
- Django's built-in User model extended with UserProfile
- Custom signup/login forms with Tailwind styling
- Session-based authentication with remember-me functionality
- Forgot password functionality with secure token-based reset
- Admin/superuser role system for content management

### Frontend
- **Tailwind CSS** via CDN for styling
- **Feather Icons** for iconography
- Django template inheritance with `base.html` as the root template
- Dark/light theme support with localStorage persistence
- Responsive design for mobile and desktop
- **crispy-forms** with Tailwind template pack for form rendering

### Key Features
- Dynamic AI-generated quiz questions
- Difficulty-based scoring (Easy: 10pts, Medium: 15pts, Hard: 20pts)
- Streak tracking system (current and longest streaks)
- Leaderboard with top 10 rankings
- Quiz timer with countdown functionality
- Question navigation during quiz
- Comprehensive admin panel for managing categories, subcategories, users, and quiz attempts

## External Dependencies

### Third-Party Services
- **Google Gemini AI API** - Used for dynamic quiz question generation (requires `GEMINI_API_KEY` environment variable)

### Database
- **PostgreSQL** - Primary database (configured via `DATABASE_URL` environment variable)
- Django ORM handles all database operations

### Python Packages
- Django 5.2 - Web framework
- google-genai - Gemini AI client library
- whitenoise - Static file serving
- crispy-forms & crispy-tailwind - Form styling
- Pillow (implied) - Image handling for avatar uploads

### Environment Variables Required
- `DATABASE_URL` - PostgreSQL connection string
- `GEMINI_API_KEY` - Google Gemini API key for AI question generation
- `SESSION_SECRET` - Django secret key (optional, has default for development)

### CDN Dependencies
- Tailwind CSS - Styling framework
- Feather Icons - Icon library
- Google Fonts (Inter) - Typography