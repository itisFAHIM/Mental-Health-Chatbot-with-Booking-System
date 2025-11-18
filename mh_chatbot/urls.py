# mh_chatbot/urls.py
from django.contrib import admin
from django.urls import path, include

# --- NEW IMPORTS ---
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('chatbot.urls')),
]

# --- NEW: Add this line to serve media files in development ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)