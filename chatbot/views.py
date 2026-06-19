import base64
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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter # Imports for PDF generation
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from .models import Medicine, Prescription, PrescriptionItem, PrescriptionNotification
from django.contrib.auth.models import User

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
    chat_history = []

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

                # Retrieve all chat history for this patient, ordered by timestamp
                chat_history = ChatHistory.objects.filter(
                    user=patient_found
                ).order_by('timestamp')

            except User.DoesNotExist:
                error_message = f"No patient found with ID: {patient_id_str}"

    return render(request, 'chatbot/search_patients.html', {
        'patient_found': patient_found,
        'error_message': error_message,
        'chat_history': chat_history
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

    # Add unread notifications count
    unread_notifications_count = 0
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'patient':
        unread_notifications_count = request.user.prescription_notifications.filter(is_read=False).count()

    context['unread_notifications_count'] = unread_notifications_count

    # Retrieve available doctors for the sidebar
    context['available_doctors'] = User.objects.filter(
        profile__role='doctor',
        profile__is_approved=True,
        profile__is_available=True
    )

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

# chatbot/views.py

@csrf_exempt
@login_required
def article_rag_api(request):
    """
    Handles RAG chat based on provided article context and image.
    """
    if request.method != "POST":
        return JsonResponse({"reply": "Invalid request method."}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"reply": "Error: You must be logged in to chat."}, status=401)

    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        article_id = data.get("article_id")

        if not user_message:
            return JsonResponse({"reply": "Please ask a question about the article."}, status=400)

        # get image details
        article = get_object_or_404(Article, id=article_id)
        article_content = article.content

        LLM_MODEL = "gemma3:4b"

        # image handling
        ollama_kwargs = {}
        if article.image:

            image_path = article.image.path

            # file reading comp.
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
                ollama_kwargs['images'] = [image_data]

            # Showing updated message for user
            user_message = f"Regarding the attached image and the article text: {user_message}"


        # RAG using
        RAG_SYSTEM_PROMPT = (
            "You are an article analysis assistant. Your ONLY job is to answer the user's question "
            "based STRICTLY on the provided article text and image (if provided). "
            "If the answer is not in the article, state clearly that the information is not available. "
            "--- ARTICLE CONTEXT ---\n"
            f"{article_content}\n"
            "-----------------------"
        )

        messages = [
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]

        # Ollama calling for image
        response = ollama.chat(model=LLM_MODEL, messages=messages, **ollama_kwargs)
        reply = response['message']['content'].strip()

        return JsonResponse({"reply": reply})

    except Exception as e:
        print("Error in article_rag_api:", e)
        return JsonResponse({"reply": f"A server error occurred during RAG processing: {e}"}, status=500)


    # ===== MEDICINE MANAGEMENT VIEWS (Doctor) =====
@user_passes_test(is_approved_doctor, login_url='landing_page')
def manage_medicines_view(request):
    """
    Allows doctors to add, edit, and delete medicines from the database.
    """
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            name = request.POST.get('name')
            generic_name = request.POST.get('generic_name')
            med_type = request.POST.get('type')
            strength = request.POST.get('strength')

            if name:
                Medicine.objects.create(
                    name=name,
                    generic_name=generic_name,
                    type=med_type,
                    strength=strength,
                    added_by=request.user
                )
                messages.success(request, 'Medicine added successfully!')
            return redirect('manage_medicines')

        elif action == 'edit':
            medicine_id = request.POST.get('medicine_id')
            medicine = get_object_or_404(Medicine, id=medicine_id)

            medicine.name = request.POST.get('name')
            medicine.generic_name = request.POST.get('generic_name')
            medicine.type = request.POST.get('type')
            medicine.strength = request.POST.get('strength')
            medicine.save()

            messages.success(request, 'Medicine updated successfully!')
            return redirect('manage_medicines')

        elif action == 'delete':
            medicine_id = request.POST.get('medicine_id')
            medicine = get_object_or_404(Medicine, id=medicine_id)
            medicine.delete()
            messages.success(request, 'Medicine deleted successfully!')
            return redirect('manage_medicines')

    medicines = Medicine.objects.all()
    context = {
        'medicines': medicines
    }
    return render(request, 'chatbot/manage_medicines.html', context)


# ===== PRESCRIPTION MANAGEMENT VIEWS (Doctor & Patient) =====
@user_passes_test(is_approved_doctor, login_url='landing_page')
def create_prescription_view(request, patient_id):
    """
    Create or edit a prescription for a patient.
    """
    patient = get_object_or_404(User, id=patient_id, profile__role='patient')
    medicines = Medicine.objects.all()

    # Check if there's an existing prescription for this patient by this doctor
    prescription = Prescription.objects.filter(
        patient=patient,
        doctor=request.user
    ).first()

    if request.method == 'POST':
        diagnosis = request.POST.get('diagnosis')
        notes = request.POST.get('notes')
        allow_patient_edit = request.POST.get('allow_patient_edit') == 'on'  # NEW

        is_update = False
        # Create or update prescription
        if prescription:
            is_update = True
            prescription.diagnosis = diagnosis
            prescription.notes = notes
            prescription.is_editable_by_patient = allow_patient_edit  # NEW
            prescription.last_modified_by = request.user  # NEW
            prescription.save()
            # Delete existing items to replace with new ones
            prescription.items.all().delete()

            # Notify patient of update
            prescription.notify_patient_of_update()  # NEW
        else:
            prescription = Prescription.objects.create(
                patient=patient,
                doctor=request.user,
                diagnosis=diagnosis,
                notes=notes,
                is_editable_by_patient=allow_patient_edit,  # NEW
                last_modified_by=request.user  # NEW
            )

        # Add prescription items
        medicine_ids = request.POST.getlist('medicine_id[]')
        dosages = request.POST.getlist('dosage[]')
        frequencies = request.POST.getlist('frequency[]')
        durations = request.POST.getlist('duration[]')
        timings = request.POST.getlist('timing[]')
        instructions = request.POST.getlist('instructions[]')

        for i in range(len(medicine_ids)):
            if medicine_ids[i]:  # Only add if medicine is selected
                PrescriptionItem.objects.create(
                    prescription=prescription,
                    medicine_id=medicine_ids[i],
                    dosage=dosages[i] if i < len(dosages) else '1 tablet',
                    frequency=frequencies[i] if i < len(frequencies) else '2',
                    duration_days=int(durations[i]) if i < len(durations) else 7,
                    timing=timings[i] if i < len(timings) else 'after_meal',
                    special_instructions=instructions[i] if i < len(instructions) else ''
                )

        if is_update:
            messages.success(request, 'Prescription updated successfully! Patient has been notified.')
        else:
            messages.success(request, 'Prescription created successfully!')
        return redirect('view_prescription', prescription_id=prescription.prescription_id)

    context = {
        'patient': patient,
        'medicines': medicines,
        'prescription': prescription,
        'existing_items': prescription.items.all() if prescription else []
    }
    return render(request, 'chatbot/create_prescription.html', context)


@login_required(login_url='login_page')
def edit_prescription_patient_view(request, prescription_id):
    """
    Allow patient to edit their prescription if permitted by doctor.
    """
    prescription = get_object_or_404(Prescription, prescription_id=prescription_id)

    # Check authorization
    if request.user != prescription.patient:
        messages.error(request, 'You are not authorized to edit this prescription.')
        return redirect('landing_page')

    if not prescription.is_editable_by_patient:
        messages.error(request, 'This prescription cannot be edited. Please contact your doctor.')
        return redirect('view_prescription', prescription_id=prescription_id)

    medicines = Medicine.objects.all()

    if request.method == 'POST':
        notes = request.POST.get('notes')  # Patient can only edit notes

        prescription.notes = notes
        prescription.last_modified_by = request.user
        prescription.save()

        messages.success(request, 'Your notes have been updated successfully!')
        return redirect('view_prescription', prescription_id=prescription.prescription_id)

    context = {
        'prescription': prescription,
        'medicines': medicines,
        'items': prescription.items.all(),
        'is_patient_view': True
    }
    return render(request, 'chatbot/edit_prescription_patient.html', context)


@login_required(login_url='login_page')
def view_prescription_view(request, prescription_id):
    """
    View a prescription (accessible by both doctor and patient).
    """
    prescription = get_object_or_404(Prescription, prescription_id=prescription_id)

    # Check authorization
    if request.user != prescription.patient and request.user != prescription.doctor:
        messages.error(request, 'You are not authorized to view this prescription.')
        return redirect('landing_page')

    # Mark notifications as read if patient is viewing
    if request.user == prescription.patient:
        PrescriptionNotification.objects.filter(
            prescription=prescription,
            patient=request.user,
            is_read=False
        ).update(is_read=True)

    context = {
        'prescription': prescription,
        'items': prescription.items.all()
    }
    return render(request, 'chatbot/view_prescription.html', context)


@login_required(login_url='login_page')
def notifications_view(request):
    """
    View all prescription notifications for the patient.
    """
    if request.user.profile.role != 'patient':
        messages.error(request, 'This page is only for patients.')
        return redirect('landing_page')

    notifications = PrescriptionNotification.objects.filter(patient=request.user)
    unread_count = notifications.filter(is_read=False).count()

    context = {
        'notifications': notifications,
        'unread_count': unread_count
    }
    return render(request, 'chatbot/notifications.html', context)


@login_required(login_url='login_page')
def mark_notification_read(request, notification_id):
    """
    Mark a notification as read.
    """
    notification = get_object_or_404(PrescriptionNotification, id=notification_id, patient=request.user)
    notification.is_read = True
    notification.save()
    return redirect('view_prescription', prescription_id=notification.prescription.prescription_id)

@login_required(login_url='login_page')
def download_prescription_pdf(request, prescription_id):
    """
    Generate and download prescription as PDF.
    """
    prescription = get_object_or_404(Prescription, prescription_id=prescription_id)

    # Check authorization
    if request.user != prescription.patient and request.user != prescription.doctor:
        messages.error(request, 'You are not authorized to download this prescription.')
        return redirect('landing_page')

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

    # Container for PDF elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#007bff'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12
    )

    # Title
    elements.append(Paragraph("MindGPT Medical Prescription", title_style))
    elements.append(Spacer(1, 0.2*inch))

    # Prescription Info
    info_data = [
        ['Prescription ID:', str(prescription.prescription_id)],
        ['Date:', prescription.created_at.strftime('%B %d, %Y')],
        ['Patient Name:', prescription.patient.get_full_name()],
        ['Patient ID:', f'PID-{prescription.patient.id:05d}'],
        ['Doctor Name:', f'Dr. {prescription.doctor.get_full_name()}'],
        ['Specialization:', prescription.doctor.profile.specialty if hasattr(prescription.doctor.profile, 'specialty') else 'General'],
    ]

    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f7ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))

    # Diagnosis
    if prescription.diagnosis:
        elements.append(Paragraph("Diagnosis:", heading_style))
        elements.append(Paragraph(prescription.diagnosis, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))

    # Medicines
    elements.append(Paragraph("Prescribed Medications:", heading_style))

    med_data = [['Medicine', 'Dosage', 'Frequency', 'Duration', 'Timing']]

    for item in prescription.items.all():
        med_data.append([
            f"{item.medicine.name}\n({item.medicine.strength})" if item.medicine.strength else item.medicine.name,
            item.dosage,
            item.get_frequency_display(),
            f"{item.duration_days} days",
            item.get_timing_display()
        ])

    med_table = Table(med_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1*inch, 1.2*inch])
    med_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    elements.append(med_table)
    elements.append(Spacer(1, 0.2*inch))

    # Special Instructions
    for item in prescription.items.all():
        if item.special_instructions:
            elements.append(Paragraph(f"<b>{item.medicine.name}:</b> {item.special_instructions}", styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))

    # Notes
    if prescription.notes:
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("Additional Notes:", heading_style))
        elements.append(Paragraph(prescription.notes, styles['Normal']))

    # Footer
    elements.append(Spacer(1, 0.5*inch))
    footer_text = "This is a digitally generated prescription. For any queries, please contact your doctor."
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))

    # Build PDF
    doc.build(elements)

    # Get PDF from buffer
    buffer.seek(0)

    # Return as download
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="prescription_{prescription.prescription_id}.pdf"'

    return response
