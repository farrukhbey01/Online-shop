from exceptions.error_codes import ErrorCodes
from exceptions.exception import CustomApiException


def is_admin(func):
    def wrapper(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise CustomApiException(error_code=ErrorCodes.UNAUTHORIZED.value)
        elif request.user.user_type == 2:
            return func(self, request, *args, **kwargs)

        raise CustomApiException(error_code=ErrorCodes.FORBIDDEN.value,
                                 message="You are not authorized to access this api")

    return wrapper



def is_user(func):
    def wrapper(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise CustomApiException(error_code=ErrorCodes.UNAUTHORIZED.value)
        elif request.user.user_type == 1:
            return func(self, request, *args, **kwargs)

        raise CustomApiException(error_code=ErrorCodes.FORBIDDEN.value,
                                 message="You are not authorized to access this api")

    return wrapper