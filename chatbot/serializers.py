from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Message
User = get_user_model()
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','username','email')
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('username','email','password')
    def create(self, validated_data):
        user = User(username=validated_data['username'], email=validated_data.get('email',''))
        user.set_password(validated_data['password'])
        user.save()
        return user
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id','user','sender','text','created_at')
