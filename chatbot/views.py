# import subprocess
# import ollama
# import json
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.shortcuts import render, redirect
# from .prompts import system_prompt_llama, system_prompt_qwen3
# from django.contrib.auth.models import User
# from django.contrib import messages

# # ---------- PAGE VIEWS ----------

# def landing_page(request):
#     """Landing page with login and signup buttons"""
#     return render(request, 'chatbot/landing.html')


# def login_page(request):
#     if request.method == "POST":
#         username = request.POST.get("username")
#         password = request.POST.get("password")

#         #login check
#         if username and password:
#             request.session["is_logged_in"] = True
#             request.session["username"] = username
#             return redirect("index")
#         else:
#             return render(request, 'chatbot/login.html', {"error": "Invalid credentials"})

#     return render(request, 'chatbot/login.html')


# # def signup_page(request):
# #     if request.method == "POST":
# #         username = request.POST.get("username")
# #         password = request.POST.get("password")
# #         # Normally you'd save to a database here

# #         if username and password:
# #             return redirect("login_page")
# #         else:
# #             return render(request, 'chatbot/signup.html', {"error": "Please fill all fields"})

# #     return render(request, 'chatbot/signup.html')

# def signup_page(request):
#     if request.method == "POST":
#         username = request.POST.get("username")
#         email = request.POST.get("email")
#         password = request.POST.get("password")

#         if username and email and password:
#             # Check if username already exists
#             if User.objects.filter(username=username).exists():
#                 return render(request, 'chatbot/signup.html', {"error": "Username already exists"})
            
#             # Check if email already exists
#             if User.objects.filter(email=email).exists():
#                 return render(request, 'chatbot/signup.html', {"error": "Email already registered"})
            
#             try:
#                 # Create the user
#                 User.objects.create_user(
#                     username=username,
#                     email=email,
#                     password=password
#                 )
#                 messages.success(request, 'Account created successfully! Please login.')
#                 return redirect("login_page")
#             except Exception as e:
#                 return render(request, 'chatbot/signup.html', {"error": "An error occurred. Please try again."})
#         else:
#             return render(request, 'chatbot/signup.html', {"error": "Please fill all fields"})

#     return render(request, 'chatbot/signup.html')


# def logout_view(request):
#     request.session.flush()
#     return redirect("landing_page")


# def index(request):
#     """Main chat interface (protected)"""
#     if not request.session.get("is_logged_in"):
#         return redirect("landing_page")

#     if "chat_history" not in request.session:
#         request.session["chat_history"] = []

#     return render(request, 'chatbot/index.html')


# # ---------- API ENDPOINTS ----------

# def register_view(request):
#     return JsonResponse({"status": "success", "message": "Register API placeholder"})


# def login_view(request):
#     return JsonResponse({"status": "success", "message": "Login API placeholder"})


# def history_api(request):
#     history = request.session.get("chat_history", [])
#     return JsonResponse({"status": "success", "history": history})



# @csrf_exempt
# def chatbot_response(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             user_message = data.get("message", "")

#             if not user_message.strip():
#                 return JsonResponse({"reply": "Please type a message."})

#             # Get chat history from session
#             chat_history = request.session.get("chat_history", [])
            
#             # Build messages for ollama.chat
#             messages = [
#                 {
#                     "role": "system",
#                     "content": system_prompt_qwen3
#                 }
#             ]
            
#             # Add previous conversation history
#             for exchange in chat_history:
#                 messages.append({"role": "user", "content": exchange["user"]})
#                 messages.append({"role": "assistant", "content": exchange["bot"]})
            
#             # Add current user message
#             messages.append({"role": "user", "content": user_message})
            

#             # Call ollama.chat
#             response = ollama.chat(
#                 model="qwen3:4b",
#                 messages=messages
#             )

#             reply = response['message']['content'].strip()
            
#             if not reply:
#                 reply = "I'm here to listen. Could you share more about how you're feeling?"

#             # Save to session chat history
#             chat_history.append({"user": user_message, "bot": reply})
#             request.session["chat_history"] = chat_history
#             request.session.modified = True

#             return JsonResponse({"reply": reply})
            
#         except Exception as e:
#             print("Error in chatbot_response:", e)
#             return JsonResponse({"reply": "I'm having trouble responding right now. Please try again."})
#     else:
#         return JsonResponse({"reply": "Invalid request method."})


# import json
# import ollama
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.shortcuts import render, redirect
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.models import User
# from django.contrib import messages
# from .prompts import system_prompt_qwen3

# # ---------- PAGE VIEWS ----------

# # def landing_page(request):
# #     """Landing page with login and signup buttons"""
# #     return render(request, 'chatbot/landing.html')


# # def signup_page(request):
# #     """Handles user registration"""
# #     if request.method == "POST":
# #         username = request.POST.get("username")
# #         email = request.POST.get("email")
# #         password = request.POST.get("password")
# #         confirm_password = request.POST.get("confirm_password")

# #         # Validation checks
# #         if not username or not email or not password or not confirm_password:
# #             messages.error(request, "All fields are required.")
# #             return redirect("signup_page")

# #         if password != confirm_password:
# #             messages.error(request, "Passwords do not match.")
# #             return redirect("signup_page")

# #         if User.objects.filter(username=username).exists():
# #             messages.error(request, "Username already exists.")
# #             return redirect("signup_page")

# #         if User.objects.filter(email=email).exists():
# #             messages.error(request, "Email already registered.")
# #             return redirect("signup_page")

# #         # Create user
# #         user = User.objects.create_user(username=username, email=email, password=password)
# #         user.save()
# #         messages.success(request, "Account created successfully! Please log in.")
# #         return redirect("login_page")

# #     return render(request, 'chatbot/signup.html')


# # def login_page(request):
# #     """Handles secure login with password verification"""
# #     if request.method == "POST":
# #         username = request.POST.get("username")
# #         password = request.POST.get("password")

# #         user = authenticate(request, username=username, password=password)

# #         if user is not None:
# #             login(request, user)
# #             messages.success(request, f"Welcome back, {user.username}!")
# #             return redirect("index")
# #         else:
# #             messages.error(request, "Invalid username or password.")
# #             return redirect("login_page")

# #     return render(request, 'chatbot/login.html')


# # def logout_view(request):
# #     """Logs user out securely"""
# #     logout(request)
# #     messages.info(request, "You have been logged out.")
# #     return redirect("landing_page")

# def signup_page(request):
#     if request.method == "POST":
#         username = request.POST.get("username")
#         email = request.POST.get("email")
#         password = request.POST.get("password")

#         if username and email and password:
#             # Check if username exists
#             if User.objects.filter(username=username).exists():
#                 messages.error(request, "Username already exists.")
#                 return redirect("signup_page")

#             # Check if email exists
#             if User.objects.filter(email=email).exists():
#                 messages.error(request, "Email already registered.")
#                 return redirect("signup_page")

#             # ✅ Create user securely
#             user = User.objects.create_user(
#                 username=username,
#                 email=email,
#                 password=password
#             )
#             user.save()

#             messages.success(request, "Account created successfully! Please log in.")
#             return redirect("login_page")  # ✅ redirect to login after signup
#         else:
#             messages.error(request, "Please fill all fields.")
#             return redirect("signup_page")

#     return render(request, "chatbot/signup.html")


# def login_page(request):
#     if request.method == "POST":
#         username = request.POST.get("username")
#         password = request.POST.get("password")

#         # ✅ Use Django authentication
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             messages.success(request, f"Welcome back, {username}!")
#             return redirect("index")  # redirect to chat page
#         else:
#             messages.error(request, "Invalid username or password.")
#             return redirect("login_page")

#     return render(request, "chatbot/login.html")


# def logout_view(request):
#     logout(request)
#     messages.info(request, "You have been logged out.")
#     return redirect("landing_page")


# def index(request):
#     """Main chatbot interface — accessible only to logged-in users"""
#     if not request.user.is_authenticated:
#         return redirect("login_page")

#     if "chat_history" not in request.session:
#         request.session["chat_history"] = []

#     return render(request, 'chatbot/index.html')


# # ---------- API ENDPOINTS ----------

# def register_view(request):
#     return JsonResponse({"status": "success", "message": "Register API placeholder"})


# def login_view(request):
#     return JsonResponse({"status": "success", "message": "Login API placeholder"})


# def history_api(request):
#     history = request.session.get("chat_history", [])
#     return JsonResponse({"status": "success", "history": history})


# @csrf_exempt
# def chatbot_response(request):
#     """Handles chatbot interactions"""
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             user_message = data.get("message", "")

#             if not user_message.strip():
#                 return JsonResponse({"reply": "Please type a message."})

#             # Get chat history
#             chat_history = request.session.get("chat_history", [])

#             # Build messages for ollama.chat
#             messages_list = [{"role": "system", "content": system_prompt_qwen3}]
#             for exchange in chat_history:
#                 messages_list.append({"role": "user", "content": exchange["user"]})
#                 messages_list.append({"role": "assistant", "content": exchange["bot"]})

#             messages_list.append({"role": "user", "content": user_message})

#             # Generate response
#             response = ollama.chat(model="qwen3:4b", messages=messages_list)
#             reply = response['message']['content'].strip()

#             if not reply:
#                 reply = "I'm here to listen. Could you share more about how you're feeling?"

#             # Store chat
#             chat_history.append({"user": user_message, "bot": reply})
#             request.session["chat_history"] = chat_history
#             request.session.modified = True

#             return JsonResponse({"reply": reply})
#         except Exception as e:
#             print("Error in chatbot_response:", e)
#             return JsonResponse({"reply": "I'm having trouble responding right now. Please try again."})
#     else:
#         return JsonResponse({"reply": "Invalid request method."})
import json
import ollama
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .prompts import system_prompt_qwen3


# ---------- PAGE VIEWS ----------

def landing_page(request):
    """Landing page with login and signup buttons"""
    return render(request, 'chatbot/landing.html')


def signup_page(request):
    """Handles secure user registration"""
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # ✅ Validation
        if not username or not email or not password or not confirm_password:
            messages.error(request, "All fields are required.")
            return redirect("signup_page")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup_page")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("signup_page")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("signup_page")

        # ✅ Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login_page")

    return render(request, "chatbot/signup.html")


def login_page(request):
    """Handles user login with password verification"""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("index")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login_page")

    return render(request, "chatbot/login.html")


def logout_view(request):
    """Logs the user out"""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("landing_page")


def index(request):
    """Main chatbot interface — accessible only to logged-in users"""
    if not request.user.is_authenticated:
        return redirect("login_page")

    if "chat_history" not in request.session:
        request.session["chat_history"] = []

    return render(request, "chatbot/index.html")


# ---------- API ENDPOINTS ----------

def register_view(request):
    return JsonResponse({"status": "success", "message": "Register API placeholder"})


def login_view(request):
    return JsonResponse({"status": "success", "message": "Login API placeholder"})


def history_api(request):
    history = request.session.get("chat_history", [])
    return JsonResponse({"status": "success", "history": history})


@csrf_exempt
def chatbot_response(request):
    """Handles chatbot messages"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")

            if not user_message.strip():
                return JsonResponse({"reply": "Please type a message."})

            # Retrieve chat history
            chat_history = request.session.get("chat_history", [])

            # Build context for Ollama
            messages_list = [{"role": "system", "content": system_prompt_qwen3}]
            for exchange in chat_history:
                messages_list.append({"role": "user", "content": exchange["user"]})
                messages_list.append({"role": "assistant", "content": exchange["bot"]})
            messages_list.append({"role": "user", "content": user_message})

            # Generate chatbot reply
            response = ollama.chat(model="qwen3:4b", messages=messages_list)
            reply = response['message']['content'].strip()

            if not reply:
                reply = "I'm here to listen. Could you share more about how you're feeling?"

            # Save to chat history
            chat_history.append({"user": user_message, "bot": reply})
            request.session["chat_history"] = chat_history
            request.session.modified = True

            return JsonResponse({"reply": reply})
        except Exception as e:
            print("Error in chatbot_response:", e)
            return JsonResponse({"reply": "I'm having trouble responding right now. Please try again."})
    else:
        return JsonResponse({"reply": "Invalid request method."})
