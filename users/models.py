import secrets
import string

from django.contrib.auth.models import AbstractUser
from django.db import models


NULLABLE = {"blank": True, "null": True}


class User(AbstractUser):
    """Пользователь"""
    username = None
    phone = models.CharField(
        max_length=11,
        verbose_name='телефон',
        unique=True
    )
    invitation_code = models.CharField(
        max_length=6,
        verbose_name='реферальный код',
        **NULLABLE
    )
    invited_by = models.ForeignKey(
        to='self',
        on_delete=models.RESTRICT,
        verbose_name='реферер',
        **NULLABLE
    )
    password = models.CharField(
        max_length=128,
        **NULLABLE
    )

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self):
        return f'{self.phone}'

    @classmethod
    def create_user(cls, credentials: dict):
        """Метод создания пользователя с присвоением ему реферального кода"""
        user = cls(**credentials)
        user.create_invitation_code()
        user.save()
        return user

    @classmethod
    def get_or_create_user(cls, credentials: dict):
        """Метод получения объекта пользователя, при отсутствии его создание"""
        phone = credentials['phone']
        user = cls.objects.filter(phone=phone).first()
        if not user:
            user = cls.create_user(credentials)
        return user

    def create_invitation_code(self):
        """
        Метод создания реферального кода,
        состоящего из заглавных букв и цифр
        """
        letters_and_digits = string.ascii_uppercase + string.digits
        while invitation_code := (
                ''.join(secrets.choice(letters_and_digits) for _ in range(6))):
            if User.objects.filter(invitation_code=invitation_code).exists():
                continue
            self.invitation_code = invitation_code
            break
