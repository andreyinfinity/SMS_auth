from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from users import views
from users.apps import UsersConfig


app_name = UsersConfig.name


urlpatterns = [
    path('login/', views.Login.as_view(), name='login'),
    path('login/sms-confirm/', views.SMSConfirmation.as_view(), name='sms-confirm'),
    path('profile/', views.UserProfile.as_view(), name='profile'),
    path('profile/invitation/', views.Invitation.as_view(), name='invitation'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
