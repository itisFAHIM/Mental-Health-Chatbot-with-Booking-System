from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # ... (all your existing paths)
    path('session/', views.online_session_page, name='online_session_page'),
    path('session/doctor/<int:doctor_id>/', views.doctor_detail_page, name='doctor_detail_page'),

    # --- NEW: ARTICLE PAGE URL ---
    path('articles/', views.article_feed_page, name='article_feed_page'),  
]
