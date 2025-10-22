import subprocess
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render


# ========== BASIC FRONTEND PAGES ==========

def index(request):
    return render(request, 'index.html')


def login_page(request):
    return render(request, 'login.html')


def signup_page(request):
    return render(request, 'signup.html')


# ========== AUTH API PLACEHOLDERS (for now) ==========

def register_view(request):
    return JsonResponse({"status": "success", "message": "Register API placeholder"})


def login_view(request):
    return JsonResponse({"status": "success", "message": "Login API placeholder"})


def history_api(request):
    return JsonResponse({"status": "success", "history": []})


# ========== MAIN CHATBOT API (using local Ollama model) ==========

@csrf_exempt
def chatbot_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")

            if not user_message.strip():
                return JsonResponse({"reply": "Please type a message."})

            system_prompt = "You are a kind and empathetic mental health assistant."
            full_prompt = f"{system_prompt}\nUser: {user_message}\nAssistant:"

            # Run local Ollama llama3.2 model
            process = subprocess.Popen(
                ["ollama", "run", "llama3.2"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            output, error = process.communicate(full_prompt)

            if error:
                print("Ollama Error:", error)

            reply = output.strip().split("Assistant:")[-1].strip() if "Assistant:" in output else output.strip()
            if not reply:
                reply = "I'm here to listen. Could you share more about how you're feeling?"

            return JsonResponse({"reply": reply})

        except Exception as e:
            print("Error in chatbot_response:", e)
            return JsonResponse({"reply": f"An error occurred: {e}"})
    else:
        return JsonResponse({"reply": "Invalid request method."})
