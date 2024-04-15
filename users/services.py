import requests
import secrets
import string
from datetime import datetime, timedelta
import jose
from jose import jwe, jwt
from rest_framework.exceptions import APIException
from config.settings import JWE_SECRET, TELEGRAM_API_KEY


def create_sms_jwe_token(credentials: dict) -> str:
    """Создание зашифрованного JSON токена - JWE"""
    # Создание смс кода
    sms_code = create_sms_code()
    # Отправка смс
    send_sms(sms_code)
    now = datetime.utcnow()
    # Полезные данные для токена
    payload = {
        'iat': now,
        'nbf': now,
        'exp': now + timedelta(seconds=60 * 3),
        'credentials': dict(credentials),
        'sms_code': sms_code,
    }
    # Создание JWT токена для получения строкового представления payload
    jwt_token = jwt.encode(claims=payload, key='')
    # Шифрование токена, создание JWE, ключ шифрования должен быть 256-битным
    encrypted_token = jwe.encrypt(plaintext=jwt_token, key=JWE_SECRET).decode('utf-8')
    return encrypted_token


def create_sms_code() -> str:
    """Функция создания sms кода, состоящего из 4 цифр"""
    return ''.join(secrets.choice(string.digits) for _ in range(4))


def send_sms(message: str):
    """Функция отправки смс (для тестирования через телеграм)"""
    telegram_token = TELEGRAM_API_KEY
    send_message_url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
    requests.post(
        url=send_message_url,
        data={
            'chat_id': 1696835726,
            'text': message
        })


def decode_sms_token(token: str) -> dict:
    """Функция дешифровки и декодирования смс токена"""
    try:
        jwt_token = jwe.decrypt(jwe_str=token, key=JWE_SECRET)
    except (jose.exceptions.JWEError, jose.exceptions.JWEParseError):
        raise APIException('Invalid token')
    # Декодирование JWT
    try:
        return jwt.decode(token=jwt_token, key='')
    except jose.exceptions.JWTError:
        raise APIException('Token lifetime is expired or invalid token is sent')
