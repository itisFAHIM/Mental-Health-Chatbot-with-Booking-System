# from django.urls import path
# from . import views

# urlpatterns = [
#     path('', views.landing_page, name='landing_page'),
#     path('login/', views.login_page, name='login_page'),
#     path('signup/', views.signup_page, name='signup_page'),
#     path('logout/', views.logout_view, name='logout_view'),
#     path('chat/', views.index, name='index'),

#     # API endpoints
#     path('api/auth/register/', views.register_view, name='register'),
#     path('api/auth/login/', views.login_view, name='login'),
#     path('api/chat/', views.chatbot_response, name='chat_api'),
#     path('api/history/', views.history_api, name='history_api'),
# ]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('login/', views.login_page, name='login_page'),
    path('signup/', views.signup_page, name='signup_page'),
    path('logout/', views.logout_view, name='logout_view'),
    path('chat/', views.index, name='index'),

    # API endpoints
    path('api/auth/register/', views.register_view, name='register'),
    path('api/auth/login/', views.login_view, name='login'),
    path('api/chat/', views.chatbot_response, name='chat_api'),
    path('api/history/', views.history_api, name='history_api'),
]
