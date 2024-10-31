import random
from django.conf import settings
import requests
from rest_framework.exceptions import ValidationError
from datetime import timedelta, datetime
from exceptions.exception import CustomApiException
from exceptions.error_codes import ErrorCodes


def generate_otp_code():
    first_digit = random.randint(1, 9)
    digits = [str(random.randint(0, 9)) for i in range(4)]
    return str(first_digit) + ''.join(digits)


def send_otp(otp):
    message = """
    Project: Final Project\nPhone_number: {}\nOTP_Code: {}\nOTP_Key: {}\nCreated_at: {}\nExpire_date : {}
    """.format(otp.user.username, otp.otp_code, otp.otp_key, otp.created_at, otp.created_at + timedelta(minutes=3))

    status = requests.get(settings.TELEGRAM_API_URL.format(settings.BOT_TOKEN, message, settings.CHANNEL_ID))
    if status.status_code != 200:
        raise CustomApiException("Texnik sabablarga ko'ra ko'd yuborilmadi, Iltimos keyinroq urinib ko'ring!")


def otp_expire(time):
    if datetime.now() - time > timedelta(minutes=3):
        raise CustomApiException(error_code=ErrorCodes.VALIDATION_FAILED.value,message='otp expired')


def check_otp(data):
    if datetime.now() - data.order_by('-created_at').first().created_at > timedelta(hours=12):
        data.delete()

    if len(data) >= 3:
        raise CustomApiException(error_code=ErrorCodes.VALIDATION_FAILED.value, message='Too many attempts, Please try after 12 hours!')

def check_user(user):
    if user is None:

        raise CustomApiException(error_code=ErrorCodes.NOT_FOUND.value, message=' User Not Found')
    if not user.is_verified:
        # raise BadRequestException("User is not verified!")
        raise CustomApiException(error_code=ErrorCodes.VALIDATION_FAILED.value, message='otp expired')