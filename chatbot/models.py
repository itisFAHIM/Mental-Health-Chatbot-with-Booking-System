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
    
    