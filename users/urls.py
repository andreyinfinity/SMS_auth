from django.urls import path
from rest_framework.routers import DefaultRouter

from users import views
from users.apps import UsersConfig
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView


app_name = UsersConfig.name

urlpatterns = [
    path('login/', views.Login.as_view(), name='login'),
    path('sms-confirm/', views.SMSConfirmation.as_view(), name='sms-confirm'),
    path('profile/', views.UserProfile.as_view(), name='profile'),
    path('profile/invitation/', views.Invitation.as_view(), name='invitation'),

    path('token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
