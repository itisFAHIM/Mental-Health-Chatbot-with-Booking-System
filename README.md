# Mental Health Chatbot — Full Project (Django + PWA)

## Overview
This project is a demo mental-health counselling chatbot. It includes:
- Django backend with REST API for authentication, chat, and chat history
- SQLite database (local)
- Frontend single-page Progressive Web App (PWA) with a Gemini-like UI (login/signup, chat, history)
- Integration with Hugging Face Inference API (configurable via environment variable)

**Important:** This is a demonstration only. Not a substitute for professional mental health care.

## Quick local setup (desktop)
1. Create a Python virtualenv and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and set your Hugging Face API token:
   ```bash
   cp .env.example .env
   # Edit .env and put your HF token in HF_API_TOKEN
   ```
4. Run migrations and start server:
   ```bash
   python manage.py migrate
   python manage.py runserver 0.0.0.0:8000
   ```
## Install on Pixel 7 (PWA)
- Expose your dev server to the phone (ngrok or localtunnel) or use LAN IP.
- Open the site in Chrome on your Pixel 7 and choose "Add to Home screen".
