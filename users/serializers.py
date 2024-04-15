from rest_framework import serializers
from users.models import User


class LoginSerializer(serializers.Serializer):
    """Сериализатор для проверки номера телефона российского оператора связи,
    вводимый номер может начинаться с +7, 7 или 8, либо без кода страны"""
    phone = serializers.RegexField(
        r'^((([+]{1}[7]{1})|[7]{1}|[8]{1})?[9]{1}[0-9]{9})?$',
        min_length=10,
        max_length=12
    )


class SMSCodeSerializer(serializers.Serializer):
    """Сериализатор вводимого кода из смс, который должен содержать 4 цифры"""
    sms_token = serializers.CharField(required=False)
    sms_code = serializers.RegexField(
        regex=r'^[0-9]{4}?$',
        max_length=4,
        min_length=4
    )


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор модели пользователя"""
    class Meta:
        model = User
        fields = '__all__'

