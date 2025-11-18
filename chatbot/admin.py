from django.contrib import admin
from .models import Message, ChatHistory, Profile, Article, Appointment

# Custom Admin view for Profiles
class ProfileAdmin(admin.ModelAdmin):
    # This now shows the User's ID right in the list!
    list_display = ('user', 'get_user_id', 'role', 'is_approved')
    list_filter = ('role', 'is_approved')
    search_fields = ('user__username',)

    @admin.display(description='User ID')
    def get_user_id(self, obj):
        return obj.user.id

# All models.
admin.site.register(Message)
admin.site.register(ChatHistory)
admin.site.register(Profile, ProfileAdmin) 
admin.site.register(Article)

# New models for appointment

admin.site.register(Appointment) 