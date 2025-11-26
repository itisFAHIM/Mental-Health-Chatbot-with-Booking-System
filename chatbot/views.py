# import subprocess
# import ollama
# import json
# import uuid
# import datetime
# from django.utils import timezone
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.shortcuts import render, redirect, get_object_or_404
# from .prompts import system_prompt_llama, system_prompt_gemma 
# from django.contrib.auth.models import User
# from django.contrib import messages
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.decorators import login_required, user_passes_test
# from .models import ChatHistory, Profile, Article, Appointment
# from django.db.models import Subquery, OuterRef, F
# from .forms import PatientSignUpForm, DoctorSignUpForm, ProfileUpdateForm
# from django.core.validators import validate_email
# from django.core.exceptions import ValidationError

# # ---------- PAGE VIEWS ----------

# def landing_page(request):
#     """
#     Renders the landing page.
#     """
#     articles = Article.objects.all()[:3]
    
#     available_doctors = User.objects.filter(
#         profile__role='doctor', 
#         profile__is_approved=True, 
#         profile__is_available=True
#     )[:3]
    
#     context = {
#         'articles': articles,
#         'available_doctors': available_doctors
#     }
#     return render(request, 'chatbot/landing.html', context)


# def login_page(request):
#     if request.method == "POST":
#         username_or_email = request.POST.get("username")
#         password = request.POST.get("password")
        
#         if not username_or_email or not password:
#             return render(request, 'chatbot/login.html', {"error": "Please enter all fields"})

#         auth_username = None
#         try:
#             validate_email(username_or_email)
#             try:
#                 user_obj = User.objects.get(email=username_or_email)
#                 auth_username = user_obj.username
#             except User.DoesNotExist:
#                 auth_username = None
#         except ValidationError:
#             auth_username = username_or_email

#         if auth_username is None:
#             return render(request, 'chatbot/login.html', {"error": "Invalid username or email"})

#         user = authenticate(request, username=auth_username, password=password)
        
#         if user is not None:
#             try:
#                 profile = user.profile
#                 if profile.role == 'doctor' and not profile.is_approved:
#                     return redirect('waiting_approval')
#             except Profile.DoesNotExist:
#                 Profile.objects.create(user=user, role='patient')

#             login(request, user)
#             return redirect("landing_page")
#         else:
#             return render(request, 'chatbot/login.html', {"error": "Invalid username or password"})

#     return render(request, 'chatbot/login.html')


# # --- SIGNUP FLOW ---
# def signup_chooser_view(request):
#     return render(request, 'chatbot/signup_chooser.html')

# def patient_signup_view(request):
#     if request.method == 'POST':
#         form = PatientSignUpForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Account created successfully! Please login.')
#             return redirect('login_page')
#     else:
#         form = PatientSignUpForm()
#     return render(request, 'chatbot/patient_signup.html', {'form': form})

# def doctor_signup_view(request):
#     if request.method == 'POST':
#         form = DoctorSignUpForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return redirect('waiting_approval') # Send to waiting page
#     else:
#         form = DoctorSignUpForm()
#     return render(request, 'chatbot/doctor_signup.html', {'form': form})

# def waiting_approval_view(request):
#     return render(request, 'chatbot/waiting_approval.html')


# def logout_view(request):
#     logout(request)
#     return redirect("landing_page")


# @login_required(login_url='landing_page') 
# def index(request):
#     return render(request, 'chatbot/index.html')


# @login_required(login_url='login_page')
# def profile_view(request):
#     try:
#         profile = request.user.profile
#     except Profile.DoesNotExist:
#         profile = Profile.objects.create(user=request.user)

#     if request.method == 'POST':
#         if 'toggle_availability' in request.POST:
#              profile.is_available = not profile.is_available
#              profile.save()
#              messages.success(request, 'Your availability has been updated.')
#              return redirect('profile_page')

#         form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Your profile has been updated!')
#             return redirect('profile_page')
#     else:
#         form = ProfileUpdateForm(instance=profile)

#     return render(request, 'chatbot/profile.html', {
#         'form': form,
#         'profile': profile
#     })


# # ---------- API ENDPOINTS ----------
# def register_view(request):
#     return JsonResponse({"status": "success", "message": "Register API placeholder"})
# def login_view(request):
#     return JsonResponse({"status": "success", "message": "Login API placeholder"})
# @login_required
# def conversation_list_api(request):
#     first_message = ChatHistory.objects.filter(conversation_id=OuterRef('conversation_id'), user=request.user).order_by('timestamp').values('message')[:1]
#     conversations = ChatHistory.objects.filter(user=request.user).values('conversation_id', first_message_text=Subquery(first_message)).distinct().order_by('-timestamp')
#     conv_list = [{"id": str(conv['conversation_id']), "title": (conv['first_message_text'] or "New Chat")[:40] + "..."} for conv in conversations]
#     return JsonResponse({"conversations": conv_list})
# @login_required
# def conversation_detail_api(request, conversation_id):
#     if not ChatHistory.objects.filter(user=request.user, conversation_id=conversation_id).exists():
#         return JsonResponse({"error": "Not found or not authorized"}, status=404)
#     messages = ChatHistory.objects.filter(user=request.user, conversation_id=conversation_id).order_by('timestamp')
#     history_list = [{"user": item.message, "bot": item.reply} for item in messages]
#     return JsonResponse({"status": "success", "history": history_list})
# @csrf_exempt
# @login_required 
# def chatbot_response(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             user_message = data.get("message", "").strip()
#             conversation_id_str = data.get("conversation_id")
            
#             if not user_message:
#                 return JsonResponse({"reply": "Please type a message."})

#             # Get or create conversation ID
#             if conversation_id_str:
#                 conv_id = uuid.UUID(conversation_id_str)
#                 # Verify ownership
#                 if ChatHistory.objects.filter(conversation_id=conv_id).exists():
#                     if not ChatHistory.objects.filter(user=request.user, conversation_id=conv_id).exists():
#                         return JsonResponse({"reply": "Error: Conversation not found."}, status=404)
#             else:
#                 conv_id = uuid.uuid4()
            
#             # Load ONLY this conversation's history (limited to recent messages)
#             db_history = ChatHistory.objects.filter(
#                 user=request.user,
#                 conversation_id=conv_id
#             ).order_by('-timestamp')[:10]  # Last 10 exchanges only
            
#             # Build message context
#             messages = [{"role": "system", "content": system_prompt_gemma}]
            
#             # Add history in correct order (oldest first)
#             for exchange in reversed(list(db_history)):
#                 messages.append({"role": "user", "content": exchange.message})
#                 messages.append({"role": "assistant", "content": exchange.reply})
            
#             # Add current message
#             messages.append({"role": "user", "content": user_message})
#             MODEL="gemma3:4b"

#             # Call model

#             response = ollama.chat(model=MODEL, messages=messages)
#             reply = response['message']['content'].strip()
            
#             if not reply:
#                 reply = "I'm here to listen. Could you share more about how you're feeling?"

#             # Save to database
#             ChatHistory.objects.create(
#                 user=request.user,
#                 conversation_id=conv_id,
#                 message=user_message,
#                 reply=reply
#             )
            
#             return JsonResponse({"reply": reply, "conversation_id": str(conv_id)})
            
#         except Exception as e:
#             print("Error in chatbot_response:", e)
#             return JsonResponse({"reply": "I'm having trouble responding right now. Please try again."})
#     else:
#         return JsonResponse({"reply": "Invalid request method."})


# # --- SESSION & DOCTOR VIEWS ---

# @login_required(login_url='login_page')
# def online_session_page(request):
#     doctors = User.objects.filter(profile__role='doctor', profile__is_approved=True)
#     context = {
#         "doctors": doctors
#     }
#     return render(request, 'chatbot/online_session.html', context)


# @login_required(login_url='login_page')
# def doctor_detail_page(request, doctor_id):
#     doctor = get_object_or_404(User, id=doctor_id, profile__role='doctor', profile__is_approved=True)
#     context = {
#         "doctor": doctor
#     }
#     return render(request, 'chatbot/doctor_detail.html', context)


# # --- ARTICLE VIEWS ---
# @login_required(login_url='login_page')
# def article_feed_page(request):
#     is_doctor = False
#     try:
#         is_doctor = request.user.profile.role == 'doctor' and request.user.profile.is_approved
#     except Profile.DoesNotExist:
#         Profile.objects.create(user=request.user)

#     if request.method == "POST":
#         if is_doctor:
#             headline = request.POST.get("headline")
#             content = request.POST.get("content")
#             image = request.FILES.get("image")
#             if headline and content:
#                 Article.objects.create(author=request.user, headline=headline, content=content, image=image)
#                 return redirect('article_feed_page')

#     articles = Article.objects.all() 
#     context = {
#         "articles": articles,
#         "is_doctor": is_doctor
#     }
#     return render(request, 'chatbot/articles.html', context)


# @login_required(login_url='login_page')
# def article_detail_view(request, article_id):
#     article = get_object_or_404(Article, id=article_id)
#     context = {
#         'article': article
#     }
#     return render(request, 'chatbot/article_detail.html', context)


# # --- HELPER & PATIENT SEARCH ---
# def is_approved_doctor(user):
#     try:
#         return user.is_authenticated and user.profile.role == 'doctor' and user.profile.is_approved
#     except Profile.DoesNotExist:
#         return False

# @user_passes_test(is_approved_doctor, login_url='landing_page')
# def search_patients_view(request):
#     patient_found = None
#     error_message = None
#     if request.method == 'POST':
#         patient_id_str = request.POST.get('patient_id', '').strip()
#         try:
#             patient_id = int(patient_id_str.lstrip('PID-').lstrip('0'))
#         except ValueError:
#             error_message = "Invalid ID format. Please enter numbers only."
#             patient_id = None

#         if patient_id:
#             try:
#                 patient_found = User.objects.get(id=patient_id, profile__role='patient')
#             except User.DoesNotExist:
#                 error_message = f"No patient found with ID: {patient_id_str}"

#     return render(request, 'chatbot/search_patients.html', {
#         'patient_found': patient_found,
#         'error_message': error_message
#     })


# @user_passes_test(is_approved_doctor, login_url='login_page')
# def toggle_availability_view(request):
#     if request.method == 'POST':
#         try:
#             profile = request.user.profile
#             profile.is_available = not profile.is_available
#             profile.save()
#         except Profile.DoesNotExist:
#             pass
#     return redirect('profile_page')


# # --- APPOINTMENT VIEWS ---

# @login_required(login_url='login_page')
# def book_appointment_view(request, doctor_id):
#     doctor = get_object_or_404(User, id=doctor_id, profile__role='doctor', profile__is_approved=True)
    
#     if request.method == 'POST':
#         timeslot_str = request.POST.get('timeslot')
#         if not timeslot_str:
#             messages.error(request, 'Please select a valid time slot.')
#             return redirect('book_appointment', doctor_id=doctor.id)

#         try:
#             start_time = datetime.datetime.fromisoformat(timeslot_str)
            
#             Appointment.objects.create(
#                 patient=request.user,
#                 doctor=doctor,
#                 start_time=start_time,
#                 end_time=start_time + datetime.timedelta(hours=1),
#                 status='pending'
#             )
            
#             return redirect('booking_pending')
            
#         except Exception as e:
#             if 'UNIQUE constraint failed' in str(e):
#                 messages.error(request, 'This time slot was just booked. Please select another.')
#             else:
#                 messages.error(request, f'An error occurred: {e}')
#             return redirect('book_appointment', doctor_id=doctor.id)

#     today = timezone.localdate()
#     booked_slots_qs = Appointment.objects.filter(
#         doctor=doctor, 
#         start_time__gte=today
#     ).values_list('start_time', flat=True)
#     booked_slots = set(booked_slots_qs)

#     available_days = []
#     for i in range(7):
#         day = today + datetime.timedelta(days=i)
#         slots_for_day = []
#         for hour in range(9, 17):
#             slot_time = timezone.make_aware(
#                 datetime.datetime(day.year, day.month, day.day, hour, 0, 0)
#             )
#             if slot_time > timezone.now() and slot_time not in booked_slots:
#                 slots_for_day.append({
#                     'time_obj': slot_time,
#                     'time_str': slot_time.strftime('%I:%M %p')
#                 })
        
#         if slots_for_day:
#             available_days.append({
#                 'date': day,
#                 'day_name': day.strftime('%A, %B %d'),
#                 'slots': slots_for_day
#             })
    
#     context = {
#         'doctor': doctor,
#         'available_days': available_days
#     }
#     return render(request, 'chatbot/book_appointment.html', context)


# @login_required(login_url='login_page')
# def booking_pending_view(request):
#     """
#     Shows the "waiting for confirmation" message to the patient.
#     """
#     return render(request, 'chatbot/booking_pending.html')


# @login_required(login_url='login_page')
# def my_appointments_view(request):
#     """
#     Dashboard for patients and doctors. Doctors can add/clear meet links here.
#     """
#     context = {}
    
#     if request.method == 'POST' and request.user.profile.role == 'doctor':
#         try:
#             appt_id = request.POST.get('appointment_id')
#             appointment = get_object_or_404(Appointment, id=appt_id, doctor=request.user)

#             if 'save_link' in request.POST:
#                 link = request.POST.get('meeting_link')
#                 appointment.meeting_link = link
#                 appointment.save()
#                 messages.success(request, 'Meeting link updated!')
            
#             elif 'clear_link' in request.POST:
#                 appointment.meeting_link = None
#                 appointment.save()
#                 messages.success(request, 'Meeting link cleared.')
            
#             return redirect('my_appointments')
        
#         except Exception as e:
#             messages.error(request, f"Error updating link: {e}")

#     if request.method == 'POST' and request.user.profile.role == 'patient':
#         try:
#             appt_id = request.POST.get('appointment_id')
#             appointment = get_object_or_404(Appointment, id=appt_id, patient=request.user)
            
#             if 'submit_feedback' in request.POST:
#                 rating = request.POST.get('rating')
#                 feedback_text = request.POST.get('feedback_text')
                
#                 appointment.rating = int(rating)
#                 appointment.feedback_text = feedback_text
#                 appointment.save()
#                 messages.success(request, 'Your feedback has been submitted. Thank you!')
#                 return redirect('my_appointments')
#         except Exception as e:
#              messages.error(request, f"Error submitting feedback: {e}")

#     if request.user.profile.role == 'doctor':
#         context['pending_appointments'] = Appointment.objects.filter(doctor=request.user, status='pending')
#         context['confirmed_appointments'] = Appointment.objects.filter(doctor=request.user, status='confirmed')
#         context['completed_appointments'] = Appointment.objects.filter(doctor=request.user, status='completed')
#     else:
#         context['pending_appointments'] = Appointment.objects.filter(patient=request.user, status='pending')
#         context['confirmed_appointments'] = Appointment.objects.filter(patient=request.user, status='confirmed')
#         context['completed_appointments'] = Appointment.objects.filter(patient=request.user, status='completed')
#         context['declined_appointments'] = Appointment.objects.filter(patient=request.user, status='declined')
        
#     return render(request, 'chatbot/my_appointments.html', context)


# @user_passes_test(is_approved_doctor, login_url='landing_page')
# def approve_appointment_view(request, appointment_id):
#     """
#     Allows a doctor to approve a pending appointment.
#     """
#     appointment = get_object_or_404(Appointment, id=appointment_id)
    
#     if appointment.doctor == request.user:
#         appointment.status = 'confirmed'
#         appointment.save()
#         messages.success(request, 'Appointment confirmed! Please add a meeting link.')
#     else:
#         messages.error(request, 'You are not authorized to approve this appointment.')
        
#     return redirect('my_appointments')

# @user_passes_test(is_approved_doctor, login_url='landing_page')
# def decline_appointment_view(request, appointment_id):
#     """
#     Allows a doctor to decline a pending appointment.
#     """
#     appointment = get_object_or_404(Appointment, id=appointment_id)
    
#     if appointment.doctor == request.user:
#         appointment.status = 'declined'
#         appointment.save()
#         messages.success(request, 'Appointment declined.')
#     else:
#         messages.error(request, 'You are not authorized to decline this appointment.')
        
#     return redirect('my_appointments')

# @user_passes_test(is_approved_doctor, login_url='landing_page')
# def complete_appointment_view(request, appointment_id):
#     """
#     Allows a doctor to mark an appointment as complete.
#     """
#     appointment = get_object_or_404(Appointment, id=appointment_id)
#     if appointment.doctor == request.user:
#         appointment.status = 'completed'
#         appointment.save()
#         messages.success(request, 'Appointment marked as complete. Patient can now leave feedback.')
#     else:
#         messages.error(request, 'You are not authorized to complete this appointment.')
#     return redirect('my_appointments')

import subprocess
import ollama
import json
import uuid
import datetime
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from .prompts import system_prompt_llama, system_prompt_gemma 
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import ChatHistory, Profile, Article, Appointment
from django.db.models import Subquery, OuterRef, F
from .forms import PatientSignUpForm, DoctorSignUpForm, ProfileUpdateForm
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

# All PAGE VIEWS 

def landing_page(request):
    
    articles = Article.objects.all()[:3]
    
    available_doctors = User.objects.filter(
        profile__role='doctor', 
        profile__is_approved=True, 
        profile__is_available=True
    )[:3]
    
    context = {
        'articles': articles,
        'available_doctors': available_doctors
    }
    return render(request, 'chatbot/landing.html', context)


def login_page(request):
    if request.method == "POST":
        username_or_email = request.POST.get("username")
        password = request.POST.get("password")
        
        if not username_or_email or not password:
            return render(request, 'chatbot/login.html', {"error": "Please enter all fields"})

        auth_username = None
        try:
            validate_email(username_or_email)
            try:
                user_obj = User.objects.get(email=username_or_email)
                auth_username = user_obj.username
            except User.DoesNotExist:
                auth_username = None
        except ValidationError:
            auth_username = username_or_email

        if auth_username is None:
            return render(request, 'chatbot/login.html', {"error": "Invalid username or email"})

        user = authenticate(request, username=auth_username, password=password)
        
        if user is not None:
            try:
                profile = user.profile
                if profile.role == 'doctor' and not profile.is_approved:
                    return redirect('waiting_approval')
            except Profile.DoesNotExist:
                Profile.objects.create(user=user, role='patient')

            login(request, user)
            return redirect("landing_page")
        else:
            return render(request, 'chatbot/login.html', {"error": "Invalid username or password"})

    return render(request, 'chatbot/login.html')


# --- SIGNUP System ---
def signup_chooser_view(request):
    return render(request, 'chatbot/signup_chooser.html')

def patient_signup_view(request):
    if request.method == 'POST':
        form = PatientSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login_page')
    else:
        form = PatientSignUpForm()
    return render(request, 'chatbot/patient_signup.html', {'form': form})

def doctor_signup_view(request):
    if request.method == 'POST':
        form = DoctorSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('waiting_approval')
    else:
        form = DoctorSignUpForm()
    return render(request, 'chatbot/doctor_signup.html', {'form': form})

def waiting_approval_view(request):
    return render(request, 'chatbot/waiting_approval.html')


def logout_view(request):
    logout(request)
    return redirect("landing_page")


@login_required(login_url='landing_page') 
def index(request):
    return render(request, 'chatbot/index.html')


@login_required(login_url='login_page')
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        if 'toggle_availability' in request.POST:
             profile.is_available = not profile.is_available
             profile.save()
             messages.success(request, 'Your availability has been updated.')
             return redirect('profile_page')

        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile_page')
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'chatbot/profile.html', {
        'form': form,
        'profile': profile
    })


# - API 
def register_view(request):
    return JsonResponse({"status": "success", "message": "Register API placeholder"})
def login_view(request):
    return JsonResponse({"status": "success", "message": "Login API placeholder"})

@login_required
def conversation_list_api(request):
    first_message = ChatHistory.objects.filter(conversation_id=OuterRef('conversation_id'), user=request.user).order_by('timestamp').values('message')[:1]
    conversations = ChatHistory.objects.filter(user=request.user).values('conversation_id', first_message_text=Subquery(first_message)).distinct().order_by('-timestamp')
    conv_list = [{"id": str(conv['conversation_id']), "title": (conv['first_message_text'] or "New Chat")[:40] + "..."} for conv in conversations]
    return JsonResponse({"conversations": conv_list})

@login_required
def conversation_detail_api(request, conversation_id):
    if not ChatHistory.objects.filter(user=request.user, conversation_id=conversation_id).exists():
        return JsonResponse({"error": "Not found or not authorized"}, status=404)
    messages = ChatHistory.objects.filter(user=request.user, conversation_id=conversation_id).order_by('timestamp')
    history_list = [{"user": item.message, "bot": item.reply} for item in messages]
    return JsonResponse({"status": "success", "history": history_list})

@csrf_exempt
@login_required 
def chatbot_response(request):
    # Calling Model
    LLM_MODEL = "gemma3:4b" 
    SYSTEM_PROMPT = system_prompt_gemma

    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"reply": "Error: You must be logged in to chat."})
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()
            conversation_id_str = data.get("conversation_id")
            if not user_message:
                return JsonResponse({"reply": "Please type a message."})

            if conversation_id_str:
                 conv_id = uuid.UUID(conversation_id_str)
                 if ChatHistory.objects.filter(conversation_id=conv_id).exists() and not ChatHistory.objects.filter(user=request.user, conversation_id=conv_id).exists():
                     return JsonResponse({"reply": "Error: Conversation not found."}, status=404)
            else:
                 conv_id = uuid.uuid4()
            
            db_history = ChatHistory.objects.filter(user=request.user).order_by('timestamp')
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for exchange in db_history:
                messages.append({"role": "user", "content": exchange.message})
                messages.append({"role": "assistant", "content": exchange.reply})
            messages.append({"role": "user", "content": user_message})

            response = ollama.chat(model=LLM_MODEL, messages=messages)
            reply = response['message']['content'].strip()
            if not reply:
                reply = "I'm here to listen. Could you share more about how you're feeling?"

            ChatHistory.objects.create(user=request.user, conversation_id=conv_id, message=user_message, reply=reply)
            return JsonResponse({"reply": reply, "conversation_id": str(conv_id)})
        except Exception as e:
            print("Error in chatbot_response:", e)
            return JsonResponse({"reply": "I'm having trouble responding right now. Please try again."})
    else:
        return JsonResponse({"reply": "Invalid request method."})


#  SESSION and DOCTOR VIEWS 

@login_required(login_url='login_page')
def online_session_page(request):
    doctors = User.objects.filter(profile__role='doctor', profile__is_approved=True)
    context = {
        "doctors": doctors
    }
    return render(request, 'chatbot/online_session.html', context)


@login_required(login_url='login_page')
def doctor_detail_page(request, doctor_id):
    doctor = get_object_or_404(User, id=doctor_id, profile__role='doctor', profile__is_approved=True)
    context = {
        "doctor": doctor
    }
    return render(request, 'chatbot/doctor_detail.html', context)


# ARTICLE 
@login_required(login_url='login_page')
def article_feed_page(request):
    is_doctor = False
    try:
        is_doctor = request.user.profile.role == 'doctor' and request.user.profile.is_approved
    except Profile.DoesNotExist:
        Profile.objects.create(user=request.user)

    if request.method == "POST":
        if is_doctor:
            headline = request.POST.get("headline")
            content = request.POST.get("content")
            image = request.FILES.get("image")
            if headline and content:
                Article.objects.create(author=request.user, headline=headline, content=content, image=image)
                return redirect('article_feed_page')

    articles = Article.objects.all() 
    context = {
        "articles": articles,
        "is_doctor": is_doctor
    }
    return render(request, 'chatbot/articles.html', context)


@login_required(login_url='login_page')
def article_detail_view(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    context = {
        'article': article
    }
    return render(request, 'chatbot/article_detail.html', context)


# HELPER and PATIENT SEARCH
def is_approved_doctor(user):
    try:
        return user.is_authenticated and user.profile.role == 'doctor' and user.profile.is_approved
    except Profile.DoesNotExist:
        return False

@user_passes_test(is_approved_doctor, login_url='landing_page')
def search_patients_view(request):
    patient_found = None
    error_message = None
    if request.method == 'POST':
        patient_id_str = request.POST.get('patient_id', '').strip()
        try:
            patient_id = int(patient_id_str.lstrip('PID-').lstrip('0'))
        except ValueError:
            error_message = "Invalid ID format. Please enter numbers only."
            patient_id = None

        if patient_id:
            try:
                patient_found = User.objects.get(id=patient_id, profile__role='patient')
            except User.DoesNotExist:
                error_message = f"No patient found with ID: {patient_id_str}"

    return render(request, 'chatbot/search_patients.html', {
        'patient_found': patient_found,
        'error_message': error_message
    })


@user_passes_test(is_approved_doctor, login_url='login_page')
def toggle_availability_view(request):
    if request.method == 'POST':
        try:
            profile = request.user.profile
            profile.is_available = not profile.is_available
            profile.save()
        except Profile.DoesNotExist:
            pass
    return redirect('profile_page')


# APPOINTMENT VIEWS

@login_required(login_url='login_page')
def book_appointment_view(request, doctor_id):
    doctor = get_object_or_404(User, id=doctor_id, profile__role='doctor', profile__is_approved=True)
    
    if request.method == 'POST':
        timeslot_str = request.POST.get('timeslot')
        if not timeslot_str:
            messages.error(request, 'Please select a valid time slot.')
            return redirect('book_appointment', doctor_id=doctor.id)

        try:
            start_time = datetime.datetime.fromisoformat(timeslot_str)
            
            Appointment.objects.create(
                patient=request.user,
                doctor=doctor,
                start_time=start_time,
                end_time=start_time + datetime.timedelta(hours=1),
                status='pending'
            )
            
            return redirect('booking_pending')
            
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                messages.error(request, 'This time slot was just booked. Please select another.')
            else:
                messages.error(request, f'An error occurred: {e}')
            return redirect('book_appointment', doctor_id=doctor.id)

    today = timezone.localdate()
    booked_slots_qs = Appointment.objects.filter(
        doctor=doctor, 
        start_time__gte=today
    ).values_list('start_time', flat=True)
    booked_slots = set(booked_slots_qs)

    available_days = []
    for i in range(7):
        day = today + datetime.timedelta(days=i)
        slots_for_day = []
        for hour in range(9, 17):
            slot_time = timezone.make_aware(
                datetime.datetime(day.year, day.month, day.day, hour, 0, 0)
            )
            if slot_time > timezone.now() and slot_time not in booked_slots:
                slots_for_day.append({
                    'time_obj': slot_time,
                    'time_str': slot_time.strftime('%I:%M %p')
                })
        
        if slots_for_day:
            available_days.append({
                'date': day,
                'day_name': day.strftime('%A, %B %d'),
                'slots': slots_for_day
            })
    
    context = {
        'doctor': doctor,
        'available_days': available_days
    }
    return render(request, 'chatbot/book_appointment.html', context)


@login_required(login_url='login_page')
def booking_pending_view(request):
    return render(request, 'chatbot/booking_pending.html')


@login_required(login_url='login_page')
def my_appointments_view(request):
    context = {}
    
    if request.method == 'POST' and request.user.profile.role == 'doctor':
        try:
            appt_id = request.POST.get('appointment_id')
            appointment = get_object_or_404(Appointment, id=appt_id, doctor=request.user)

            if 'save_link' in request.POST:
                link = request.POST.get('meeting_link')
                appointment.meeting_link = link
                appointment.save()
                messages.success(request, 'Meeting link updated!')
            
            elif 'clear_link' in request.POST:
                appointment.meeting_link = None
                appointment.save()
                messages.success(request, 'Meeting link cleared.')
            
            return redirect('my_appointments')
        
        except Exception as e:
            messages.error(request, f"Error updating link: {e}")

    if request.method == 'POST' and request.user.profile.role == 'patient':
        try:
            appt_id = request.POST.get('appointment_id')
            appointment = get_object_or_404(Appointment, id=appt_id, patient=request.user)
            
            if 'submit_feedback' in request.POST:
                rating = request.POST.get('rating')
                feedback_text = request.POST.get('feedback_text')
                
                appointment.rating = int(rating)
                appointment.feedback_text = feedback_text
                appointment.save()
                messages.success(request, 'Your feedback has been submitted. Thank you!')
                return redirect('my_appointments')
        except Exception as e:
             messages.error(request, f"Error submitting feedback: {e}")

    if request.user.profile.role == 'doctor':
        context['pending_appointments'] = Appointment.objects.filter(doctor=request.user, status='pending')
        context['confirmed_appointments'] = Appointment.objects.filter(doctor=request.user, status='confirmed')
        context['completed_appointments'] = Appointment.objects.filter(doctor=request.user, status='completed')
    else:
        context['pending_appointments'] = Appointment.objects.filter(patient=request.user, status='pending')
        context['confirmed_appointments'] = Appointment.objects.filter(patient=request.user, status='confirmed')
        context['completed_appointments'] = Appointment.objects.filter(patient=request.user, status='completed')
        context['declined_appointments'] = Appointment.objects.filter(patient=request.user, status='declined')

    # Retrieve available doctors for the sidebar
    context['available_doctors'] = User.objects.filter(
        profile__role='doctor', 
        profile__is_approved=True, 
        profile__is_available=True
    )[:3]
        
    return render(request, 'chatbot/my_appointments.html', context)


@user_passes_test(is_approved_doctor, login_url='landing_page')
def approve_appointment_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if appointment.doctor == request.user:
        appointment.status = 'confirmed'
        appointment.save()
        messages.success(request, 'Appointment confirmed! Please add a meeting link.')
    else:
        messages.error(request, 'You are not authorized to approve this appointment.')
        
    return redirect('my_appointments')

@user_passes_test(is_approved_doctor, login_url='landing_page')
def decline_appointment_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if appointment.doctor == request.user:
        appointment.status = 'declined'
        appointment.save()
        messages.success(request, 'Appointment declined.')
    else:
        messages.error(request, 'You are not authorized to decline this appointment.')
    return redirect('my_appointments')


@user_passes_test(is_approved_doctor, login_url='landing_page')
def complete_appointment_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if appointment.doctor == request.user:
        appointment.status = 'completed'
        appointment.save()
        messages.success(request, 'Appointment marked as complete. Patient can now leave feedback.')
    else:
        messages.error(request, 'You are not authorized to complete this appointment.')
    return redirect('my_appointments')
