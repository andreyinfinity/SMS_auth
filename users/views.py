from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse_lazy
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from users.models import User
from users.serializers import UserSerializer, LoginSerializer, SMSCodeSerializer, InvitedBySerializer
from users.services import create_sms_jwe_token, decode_sms_token


class Login(generics.GenericAPIView):
    """Контроллер обработки вводимого номера телефона. Формирует зашифрованный смс-токен
    и отправляет смс сообщение на указанный номер"""
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            encrypted_token = create_sms_jwe_token(serializer.data)
            return Response(status=status.HTTP_200_OK, data={
                'sms-token': encrypted_token,
                'url_to_redirect': reverse_lazy('users:sms-confirm'),
                'fields_to_be_required': ['sms_code']
            })


class SMSConfirmation(generics.CreateAPIView):
    serializer_class = SMSCodeSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = SMSCodeSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_sms_code = serializer.data.get('sms_code')
            # Получение смс токена из тела запроса или заголовка
            sms_token = serializer.data.get('sms-token') or request.headers.get('sms-token')
            if not sms_token:
                raise APIException('sms token is not provided')
            payload = decode_sms_token(sms_token)
            # Верификация смс кода
            if payload.get('sms_code') != user_sms_code:
                raise APIException('Wrong sms code', code=status.HTTP_401_UNAUTHORIZED)
            return self.authorize(payload['credentials'])

    def authorize(self, credentials: dict):
        user = User.get_or_create_user(credentials)
        # Генерация access токена для user
        access_token = AccessToken.for_user(user=user)
        # Генерация refresh токена для user
        refresh_token = RefreshToken.for_user(user=user)

        return Response({'access': str(access_token),
                         'refresh': str(refresh_token)})


class UserProfile(generics.RetrieveUpdateDestroyAPIView):
    """CRUD для работы с профилем пользователя"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        """Получение самого себя в качестве объекта пользователя"""
        return User.objects.get(pk=self.request.user.pk)


class Invitation(generics.GenericAPIView):
    """Контроллер ввода реферального кода"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = InvitedBySerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            invited_by = serializer.data.get('invitation_code')
            # Проверка установлен ли реферер у пользователя
            if request.user.invited_by is not None:
                raise APIException('You already set the invitation code', code=status.HTTP_409_CONFLICT)
            # Получение объекта реферера по реферальному коду
            referer = User.objects.get(invitation_code=invited_by)
            # Если этого реферального кода ни у кого нет
            if not referer:
                raise APIException('User with such invitation code doest not exist')
            # Если это собственный реферальный код
            if referer.pk == request.user.pk:
                raise APIException('You can not set self invitation code')
            # Сохранение поля реферера у пользователя
            request.user.invited_by = referer
            request.user.save()
            return Response(data={
                'invited_by': referer.phone,
            })
