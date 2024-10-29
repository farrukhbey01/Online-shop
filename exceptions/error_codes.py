from rest_framework import status

from enum import Enum


class ErrorCodes(Enum):
    UNAUTHORIZED = 1
    INVALID_INPUT = 2
    FORBIDDEN = 3
    NOT_FOUND = 4
    ALREADY_EXISTS = 5
    USER_DOES_NOT_EXIST = 6
    VALIDATION_FAILED = 7


error_messages = {
    1: {"result": "Unauthorized access", "http_status": status.HTTP_401_UNAUTHORIZED},
    2: {"result": "Invalid input provided", "http_status": status.HTTP_400_BAD_REQUEST},
    3: {"result": "Permission denied", "http_status": status.HTTP_403_FORBIDDEN},
    4: {"result": "Resource not found", "http_status": status.HTTP_404_NOT_FOUND},
    5: {"result": "User Already exists", "http_status": status.HTTP_400_BAD_REQUEST},
    6: {"result": "User Does not exist or Invalid password", "http_status": status.HTTP_400_BAD_REQUEST},
    7: {"result": "Validate Error", "http_status": status.HTTP_400_BAD_REQUEST},
}


def get_error_message(code):
    return error_messages.get(code, 'Unknown error')