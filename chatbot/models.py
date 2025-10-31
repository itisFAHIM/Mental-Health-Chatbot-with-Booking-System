from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
import uuid
User = get_user_model()

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
from django.db import models
from django.contrib.auth.models import User

class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # ADD THIS FIELD to group messages
    conversation_id = models.UUIDField(default=uuid.uuid4, editable=False)
    
    message = models.TextField()
    reply = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.message[:30]}"
