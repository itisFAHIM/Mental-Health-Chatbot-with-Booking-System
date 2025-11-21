from django.contrib import admin
from .models import Message, ChatHistory, Profile, Article, Appointment

# Admin PF
class ProfileAdmin(admin.ModelAdmin):
    
    list_display = ('user', 'get_user_id', 'role', 'is_approved')
    list_filter = ('role', 'is_approved')
    search_fields = ('user__username',)

    @admin.display(description='User ID')
    def get_user_id(self, obj):
        return obj.user.id

# Models Used
admin.site.register(Message)
admin.site.register(ChatHistory)
admin.site.register(Profile, ProfileAdmin) 
admin.site.register(Article)

# Appointment Model

admin.site.register(Appointment) 