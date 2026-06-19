from django.db import models
from django.contrib.auth.models import User
import uuid
from django.db import models
from django.contrib.auth.models import User
import uuid

class Message(models.Model):
    SENDER_USER = 'user'
    SENDER_BOT = 'bot'
    SENDER_CHOICES = [(SENDER_USER,'User'), (SENDER_BOT,'Bot')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=8, choices=SENDER_CHOICES)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'{self.user.username}:{self.sender[:1]}:{self.text[:30]}'


class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    conversation_id = models.UUIDField(default=uuid.uuid4, editable=False)
    message = models.TextField()
    reply = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.message[:30]}"


# UPDATED PROFILE MODEL
class Profile(models.Model):

    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')

    # Doctor fields
    specialty = models.CharField(max_length=200, blank=True, null=True, help_text="e.g., Clinical Psychologist")
    degree_document = models.FileField(upload_to='doctor_degrees/', blank=True, null=True)
    is_approved = models.BooleanField(default=False, help_text="Admin must approve this doctor")

    is_available = models.BooleanField(default=False, help_text="Doctor's availability toggle")

    # All user fields
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile ({self.role})"


# ARTICLE
class Article(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    headline = models.CharField(max_length=255)
    content = models.TextField()
    image = models.ImageField(upload_to='article_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.headline



class Appointment(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
    )

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booked_appointments')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_sessions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    meeting_link = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    rating = models.IntegerField(null=True, blank=True)
    feedback_text = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['start_time']
        unique_together = ('doctor', 'start_time')

    def __str__(self):
        return f"Appointment with Dr. {self.doctor.username} for {self.patient.username} at {self.start_time}"

    # Assuming 'Appointment' model exists or will be created later.

class Medicine(models.Model):
    """Medicine database managed by doctors"""
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=50, choices=[
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('syrup', 'Syrup'),
        ('injection', 'Injection'),
        ('cream', 'Cream'),
        ('drops', 'Drops'),
        ('inhaler', 'Inhaler'),
    ], default='tablet')
    strength = models.CharField(max_length=50, blank=True, null=True)  # e.g., "500mg", "10ml"
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medicines_added')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.strength})" if self.strength else self.name

class Prescription(models.Model):
    prescription_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescriptions_received')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescriptions_given')
    appointment = models.ForeignKey('Appointment', on_delete=models.SET_NULL, null=True, blank=True, related_name='prescriptions')

    diagnosis = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_editable_by_patient = models.BooleanField(default=False)  # NEW: Allow patient editing
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='prescriptions_modified')  # NEW

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prescription for {self.patient.get_full_name()} by Dr. {self.doctor.get_full_name()}"

    def notify_patient_of_update(self):
        """Create notification when prescription is updated"""
        PrescriptionNotification.objects.create(
            prescription=self,
            patient=self.patient,
            message=f"Dr. {self.doctor.get_full_name()} has updated your prescription"
        )

class PrescriptionItem(models.Model):
    """Individual medicine items in a prescription"""
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)

    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=50, choices=[
        ('1', 'Once daily'),
        ('2', 'Twice daily'),
        ('3', 'Three times daily'),
        ('4', 'Four times daily'),
    ], default='2')
    duration_days = models.IntegerField(choices=[
        (3, '3 days'),
        (5, '5 days'),
        (7, '7 days'),
        (10, '10 days'),
        (14, '14 days'),
        (30, '30 days'),
    ], default=7)
    timing = models.CharField(max_length=50, choices=[
        ('before_meal', 'Before meal'),
        ('after_meal', 'After meal'),
        ('with_meal', 'With meal'),
        ('empty_stomach', 'Empty stomach'),
        ('anytime', 'Anytime'),
    ], default='after_meal')
    special_instructions = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.medicine.name} - {self.get_frequency_display()}"

# Move this class out - align it with other models (no indentation)
class PrescriptionNotification(models.Model):
    """Notification system for prescription updates"""
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='notifications')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescription_notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.patient.username} - {self.message}"
