from rest_framework import serializers as s
from users.models import User


class LoginSerializer(s.Serializer):
    """Сериализатор для проверки номера телефона российского оператора связи,
    вводимый номер может начинаться с +7, 7 или 8, либо без кода страны"""
    phone = s.RegexField(
        regex=r'^((([+]{1}[7]{1})|[7]{1}|[8]{1})?[9]{1}[0-9]{9})?$',
        min_length=10,
        max_length=12
    )


class SMSCodeSerializer(s.Serializer):
    """Сериализатор вводимого кода из смс, который должен содержать 4 цифры"""
    sms_token = s.CharField(required=False)
    sms_code = s.RegexField(
        regex=r'^[0-9]{4}?$',
        max_length=4,
        min_length=4
    )


class UserSerializer(s.ModelSerializer):
    """Сериализатор модели пользователя"""
    invited_users_phones = s.SerializerMethodField(read_only=True)
    invited_by = s.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'invitation_code',
            'invited_by',
            'invited_users_phones'
        ]
        read_only_fields = [
            'invitation_code',
            'invited_by',
            'invited_users_phones',
            'phone'
        ]

    def get_invited_users_phones(self, obj: User):
        """
        Метод получения телефонов пользователей,
        активировавших реферальный код
        """
        return User.objects.filter(
            invited_by=obj.pk).values_list('phone', flat=True)

    def get_invited_by(self, obj: User):
        """Метод получения телефона реферера"""
        return User.objects.get(pk=obj.invited_by.pk).phone


class InvitedBySerializer(s.Serializer):
    """Сериализатор реферального кода, состоящего из 6 букв и цифр"""
    invitation_code = s.RegexField(regex=r'^[0-9A-Z]{6}?$',)
