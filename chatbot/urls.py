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
    
    # === REPLACE THE OLD HISTORY URL WITH THESE TWO ===
    # path('api/history/', views.history_api, name='history_api'),  <-- DELETE THIS LINE
    
    # 1. Gets the list of conversation titles for the sidebar
    path('api/history/conversations/', views.conversation_list_api, name='conversation_list_api'),
    
    # 2. Gets the messages for ONE specific conversation
    path('api/history/conversation/<uuid:conversation_id>/', views.conversation_detail_api, name='conversation_detail_api'),
]