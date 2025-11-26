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
    # Main Pages
    path('', views.landing_page, name='landing_page'),
    path('chat/', views.index, name='index'),

    # Authentication Flow
    path('login/', views.login_page, name='login_page'),
    path('logout/', views.logout_view, name='logout_view'),
    path('signup/', views.signup_chooser_view, name='signup_chooser'),
    path('signup/patient/', views.patient_signup_view, name='patient_signup'),
    path('signup/doctor/', views.doctor_signup_view, name='doctor_signup'),
    path('waiting-approval/', views.waiting_approval_view, name='waiting_approval'),
    
    # Profile & Appointments
    path('profile/', views.profile_view, name='profile_page'),
    path('toggle-availability/', views.toggle_availability_view, name='toggle_availability'),
    path('my-appointments/', views.my_appointments_view, name='my_appointments'),
    path('booking-pending/', views.booking_pending_view, name='booking_pending'),
    path('approve-appointment/<int:appointment_id>/', views.approve_appointment_view, name='approve_appointment'),
    path('decline-appointment/<int:appointment_id>/', views.decline_appointment_view, name='decline_appointment'),
    path('book-appointment/<int:doctor_id>/', views.book_appointment_view, name='book_appointment'),
    path('complete-appointment/<int:appointment_id>/', views.complete_appointment_view, name='complete_appointment'),

    # Featured Pages
    path('session/', views.online_session_page, name='online_session_page'),
    path('session/doctor/<int:doctor_id>/', views.doctor_detail_page, name='doctor_detail_page'),
    path('articles/', views.article_feed_page, name='article_feed_page'),
    path('article/<int:article_id>/', views.article_detail_view, name='article_detail_page'),
    path('search-patients/', views.search_patients_view, name='search_patients'),

    # APIs
    path('api/auth/register/', views.register_view, name='register'),
    path('api/auth/login/', views.login_view, name='login'),
    path('api/chat/', views.chatbot_response, name='chat_api'),
    path('api/history/conversations/', views.conversation_list_api, name='conversation_list_api'),
    path('api/history/conversation/<uuid:conversation_id>/', views.conversation_detail_api, name='conversation_detail_api'),
]