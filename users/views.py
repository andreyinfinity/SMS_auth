from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse_lazy
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from users.models import User
from users import serializers as s
from users.services import create_sms_jwe_token, decode_sms_token


class Login(generics.GenericAPIView):
    """
    Первый запрос на ввод номера телефона `phone` должен начинаться с 79....
    Отправляется смс с кодом (в тестовом режиме смс возвращается в ответе `sms_code`).
    Возвращает `sms-token`, который необходимо использовать в headers,
    либо в body следующего запроса `sms-confirm`. JWE токен зашифрован 256
    битным ключом, lifetime=3m, в полезной нагрузке содержит отправленный
    `sms_code` и `phone` для последующей верификации.
    """
    serializer_class = s.LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = s.LoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            encrypted_token, sms_code = create_sms_jwe_token(serializer.data)
            return Response(status=status.HTTP_200_OK, data={
                'sms_code': sms_code,
                'sms-token': encrypted_token,
                'url_to_confirm_sms_code': reverse_lazy('users:sms-confirm'),
                'fields_to_be_required': ['sms_code']
            })


class SMSConfirmation(generics.CreateAPIView):
    """
    Второй запрос для ввода смс кода `sms_code`. Зашифрованный смс токен
    `sms_token` необходимо передавать в headers или body запроса. Возвращает
    JWT токен для аутентификации `access` `refresh`.
    """
    serializer_class = s.SMSCodeSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = s.SMSCodeSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_sms_code = serializer.data.get('sms_code')
            # Получение смс токена из тела запроса или заголовка
            sms_token = (serializer.data.get('sms_token')
                         or request.headers.get('sms-token'))
            if not sms_token:
                raise APIException('sms token is not provided')
            payload = decode_sms_token(sms_token)
            # Верификация смс кода
            if payload.get('sms_code') != user_sms_code:
                raise APIException(
                    detail='Wrong sms code',
                    code=status.HTTP_401_UNAUTHORIZED
                )
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
    """
    Профиль пользователя имеет возможность
    GET, PUT, PATCH, DELETE запросов.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = s.UserSerializer

    def get_object(self):
        """Получение самого себя в качестве объекта пользователя"""
        return User.objects.get(pk=self.request.user.pk)


class Invitation(generics.GenericAPIView):
    """
    Ввод реферального кода `invitation_code`. Код должен состоять из 6
    заглавных букв и цифр. После успешного ввода кода выводится ответ с
    номером телефона реферера 'invited_by' и реферер сохраняется в
    профиле пользователя.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = s.InvitedBySerializer

    def post(self, request, *args, **kwargs):
        serializer = s.InvitedBySerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            invited_by = serializer.data.get('invitation_code')
            # Проверка установлен ли реферер у пользователя
            if request.user.invited_by is not None:
                raise APIException(
                    detail='You already set the invitation code',
                    code=status.HTTP_409_CONFLICT
                )
            # Получение объекта реферера по реферальному коду
            referer = User.objects.get(invitation_code=invited_by)
            # Если этого реферального кода ни у кого нет
            if not referer:
                raise APIException(
                    detail='User with such invitation code doest not exist',
                    code=status.HTTP_406_NOT_ACCEPTABLE
                )
            # Если это собственный реферальный код
            if referer.pk == request.user.pk:
                raise APIException(
                    detail='You can not set self invitation code',
                    code=status.HTTP_406_NOT_ACCEPTABLE
                )
            # Сохранение поля реферера у пользователя
            request.user.invited_by = referer
            request.user.save()
            return Response(data={
                'invited_by': referer.phone,
            })
