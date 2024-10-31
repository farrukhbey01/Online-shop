from datetime import timedelta, datetime
from enum import verify

from django.contrib.auth import update_session_auth_hash
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password, make_password
from user.models import User, OTP
from rest_framework.permissions import IsAuthenticated, AllowAny
from user.serializers import UserSerializer
from .serializers import (
     LoginSerializer, OTPSerializer, ChangePasswordSerializer, ResetUserPasswordSerializer,
    OTPUserPasswordSerializer, NewPasswordSerializer, OTPResendSerializer
)
from .utils import send_otp, otp_expire, check_otp, check_user
from exceptions.exception import *
from exceptions.error_codes import *

# @api_view(['GET'])
# def auth_me(request):
#     if request.user.is_authenticated:
#         return Response(data=UserSerializer(request.user).data, status=status.HTTP_200_OK)
#     return Response(status=status.HTTP_401_UNAUTHORIZED)


class UserViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        request_body=UserSerializer(),
        responses={
            201: openapi.Response(
                description='otp_key',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'otp_key': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='otp_key'
                        )
                    }
                )
            )
        }
    )
    def register(self, request):
        data = request.data  # Post request
        obj_user = User.objects.filter(username=data.get('username')).first()  # Is there a user or not?

        if obj_user and obj_user.is_verified:
            return Response(
                data={"error": "User already exists!", 'ok': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UserSerializer(obj_user, data=data, partial=True) if obj_user else UserSerializer(data=data)

        if not serializer.is_valid():
            return Response(
                data={"message": serializer.errors, 'ok': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_user = serializer.save()
        obj_create = OTP.objects.create(user_id=validated_user.id)
        obj_all = OTP.objects.filter(user_id=validated_user.id)

        if check_otp(obj_all):
            return Response(
                data={"error": "Too many attempts try after 12 hours", 'ok': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        obj_create.save()
        send_otp(obj_create)
        return Response(data={"message": {'otp_key': obj_create.otp_key}, "ok": True}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        request_body=OTPSerializer(),
        responses={200: openapi.Response(description='Success')})
    def verify(self, request):
        otp_code = request.data.get('otp_code')
        otp_key = request.data.get('otp_key')

        if not otp_code or not otp_key:
            return Response(
                data={'error': 'OTP code or key not found', 'ok': False},
                status=status.HTTP_400_BAD_REQUEST)

        obj_otp = OTP.objects.filter(otp_key=otp_key).first()

        if obj_otp is None:
            return Response(
                data={'error': 'OTP not found', 'ok': False},
                status=status.HTTP_400_BAD_REQUEST)

        otp_expire(obj_otp.created_at)

        if obj_otp.attempts >= 1:
            return Response(
                data={"error": "Please get new OTP code and key!", 'ok': False},
                status=status.HTTP_400_BAD_REQUEST)

        if obj_otp.otp_code != otp_code:
            obj_otp.attempts += 1
            obj_otp.save(update_fields=['attempts'])
            return Response(
                data={'error': 'OTP code is incorrect!', 'ok': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = obj_otp.user
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        OTP.objects.filter(user=user).delete()
        return Response(data={'message': 'OTP verification successful!', 'ok': True}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                    'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                }
            ),
            responses={
                200: openapi.Response('Login successful', openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access_token': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh_token': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )),
                400: 'Incorrect password',
                404: 'User not found'
            },
            operation_summary="User login",
            operation_description="This endpoint allows a user to log in."
        )
    def login(self, request):
        data = request.data
        user = User.objects.filter(username=data['username'], is_verified =True).first()
        if not user:
            raise CustomApiException(error_code=ErrorCodes.USER_DOES_NOT_EXIST.value)
        if not check_password(data['password'], user.password):
            raise CustomApiException(ErrorCodes.INVALID_INPUT.value, message='Incorrect password')
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        return Response({'access_token': access_token, 'refresh_token': str(refresh)}, status=status.HTTP_200_OK)

class ChangePasswordViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={200: openapi.Response(description='Successful')})
    def update(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            # Checking if old password is correct
            if not user.check_password(serializer.data.get('old_password')):
                return Response(
                    data={'error': 'Old password is incorrect!', 'ok': False},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Set password and save
            user.set_password(serializer.data.get('new_password'))
            user.save()
            update_session_auth_hash(request, user)  # Password Hashing

            return Response(
                data={'message': 'password successfully changed', 'ok': True},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPassword(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=ResetUserPasswordSerializer,
        responses={
            201: openapi.Response(
                description='otp_key',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'otp_key': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='otp_key'
                        )
                    }
                )
            )
        }
    )
    def reset(self, request):
        username = request.data.get('username')
        if not username:
            return Response(
                data={"error": "Please fill the blank!", "ok": False},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.filter(username=username).first()

        check_user(user)  # it will check user

        check_otp(OTP.objects.filter(user_id=user.id))

        obj_create = OTP.objects.create(user_id=user.id)
        obj_create.save()
        send_otp(obj_create)
        return Response(data={'message': {"otp_key": obj_create.otp_key}, 'ok': True}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=OTPUserPasswordSerializer,
        responses={
            200: openapi.Response(
                description='otp_token',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'otp_token': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='otp_token'
                        )
                    }
                )
            )
        }
    )
    def verify(self, request):
        otp_key = request.data.get('otp_key')
        otp_code = request.data.get('otp_code')

        if not otp_key or not otp_code:
            return Response(
                data={'error': 'Please fill all blanks!', 'ok': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp = OTP.objects.filter(otp_key=otp_key).first()

        if otp is None:
            return Response(
                data={"error": "Invalid OTP key!", "ok": False},
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp.attempts >= 3:
            return Response(
                data={"error": "Too many attempts! Try later after 12 hours.", 'ok': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp.otp_code != otp_code:
            otp.attempts += 1
            otp.save(update_fields=['attempts'])
            return Response(
                data={"error": "Incorrect OTP code! Try again.", 'ok': False},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(data={'message': {"otp_token": otp.otp_token}, 'ok': True}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=NewPasswordSerializer(),
        responses={200: openapi.Response(description='Successful')})
    def reset_new(self, request):
        token = request.data.get('otp_token')
        new_password = request.data.get('password')

        if not token or not new_password:
            return Response(
                data={'message': 'Please fill all blanks!', 'ok': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        obj_otp = OTP.objects.filter(otp_token=token).first()

        if obj_otp is None:
            return Response({'error': 'Invalid OTP token!'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_expire(obj_otp.created_at):
            return Response({'error': 'OTP expired!', 'ok': False}, status=status.HTTP_400_BAD_REQUEST)

        user = obj_otp.user
        user.password = make_password(new_password)
        user.save(update_fields=['password'])
        OTP.objects.filter(otp_token=token).delete()

        return Response(
            data={'message': 'Password reset successful!', 'ok': True},
            status=status.HTTP_200_OK
        )


class OTPReset(viewsets.ViewSet):
    @swagger_auto_schema(
        request_body=OTPResendSerializer,
        responses={
            201: openapi.Response(
                description='otp_key',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'otp_key': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='otp_key'
                        )
                    }
                )
            )
        }
    )
    def resend_otp(self, request):
        otp_key = request.data.get('otp_key')
        if not otp_key:
            return Response(
                data={'message': 'Pleas fill the blank!', 'ok': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        obj_otp = OTP.objects.filter(otp_key=otp_key).first()

        if obj_otp is None:
            return Response(data={'error': 'Otp_key is wrong!', 'ok': False}, status=status.HTTP_400_BAD_REQUEST)

        if datetime.now() - obj_otp.created_at < 3:
            return Response(
                data={'error': 'OTP is not expired yet! You can use it.', 'ok': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = obj_otp.user

        if user.is_verified:
            return Response(
                data={'error': 'User already verified!', 'ok': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_obj = OTP.objects.create(user=user)

        if check_otp(new_obj):
            return Response(
                data={'error': 'Too many attempts try after 12 hours.', 'ok': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_obj.save()
        send_otp(new_obj)
        return Response(
            data={'message': {'otp_key': new_obj.otp_key}, 'ok': True},
            status=status.HTTP_200_OK
        )


# class UserProfileViewSet(viewsets.ViewSet):
#     permission_classes = [IsAuthenticated]
#     @swagger_auto_schema(
#         responses={200: UserProfileSerializer},
#         operation_description="Foydalanuvchi profilini olish"
#     )
#     def retrieve(self, request):
#         user = request.user
#         serializer = UserProfileSerializer(user)
#         return Response(serializer.data)
#
#     @swagger_auto_schema(
#         request_body=UserProfileSerializer,
#         responses={200: openapi.Response('Profil muvaffaqiyatli yangilandi.', UserProfileSerializer)},
#         operation_description="Foydalanuvchi profilini yangilash"
#     )
#     def update(self, request, pk):
#         user = get_object_or_404(User, pk=pk)
#         serializer = UserProfileSerializer(user, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response({'message': 'Profil muvaffaqiyatli yangilandi.', 'data': serializer.data},
#                         status=status.HTTP_200_OK)
#
#     @swagger_auto_schema(
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             properties={
#                 'password': openapi.Schema(type=openapi.TYPE_STRING, description="Yangi parol")
#             }
#         ),
#         responses={200: openapi.Response('Parol muvaffaqiyatli yangilandi.')},
#         operation_description="Foydalanuvchi parolini yangilash"
#     )
#     def update_password(self, request, pk):
#         user = get_object_or_404(User, pk=pk)
#         new_password = request.data.get('password')
#
#         if new_password:
#             user.password = make_password(new_password)  # Parolni hashlash
#             user.save()
#             return Response({'message': 'Parol muvaffaqiyatli yangilandi.'}, status=status.HTTP_200_OK)
#         else:
#             return Response({'error': 'Parol kiritilishi shart.'}, status=status.HTTP_400_BAD_REQUEST)
#
#     @swagger_auto_schema(request_body=openapi.Schema(
#         type=openapi.TYPE_OBJECT,
#         properties={
#             'old_password': openapi.Schema(type=openapi.TYPE_STRING, description="Eski parol"),
#             'new_password': openapi.Schema(type=openapi.TYPE_STRING, description="Yangi parol"),
#         }
#     ))
#     def change_password(self, request):
#         user = request.user
#         old_password = request.data.get('old_password')
#         new_password = request.data.get('new_password')
#
#         if not user.check_password(old_password):
#             return Response({"error": "Eski parol noto'g'ri."}, status=status.HTTP_400_BAD_REQUEST)
#
#         user.password = make_password(new_password)
#         user.save()
#         return Response({"message": "Parol muvaffaqiyatli yangilandi."}, status=status.HTTP_200_OK)
#
#     @swagger_auto_schema(
#         operation_description="Foydalanuvchining yangi kartasini registratsiya qilish",
#         request_body=CardSerializer,
#         responses={
#             200: openapi.Response('Karta muvaffaqiyatli registratsiya qilindi.'),
#             400: openapi.Response('Karta registratsiya qilishda xato.')
#         }
#     )
#     def register_card(self, request):
#         # Karta ma'lumotlarini olish
#         serializer = CardSerializer(data=request.data)
#         if serializer.is_valid():
#             card_number = serializer.validated_data['card_number']
#             expiry_date = serializer.validated_data['expiry_date']
#             cvv = serializer.validated_data['cvv']
#
#             # Stripe tokenini yaratish
#             stripe_token = self.create_stripe_token(card_number, expiry_date, cvv)
#
#             # Karta registratsiya qilish uchun oldingi kodni qo'llang
#             if not stripe_token:
#                 return Response({'message': 'Karta tokenini yaratishda xato.'}, status=status.HTTP_400_BAD_REQUEST)
#
#             # Karta ma'lumotlarini registratsiya qilish
#             # (oldingi koddan foydalaning)
#
#             return Response({
#                 'message': 'Karta muvaffaqiyatli registratsiya qilindi.'
#             }, status=status.HTTP_200_OK)
#
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def create_stripe_token(self, card_number, expiry_date, cvv):
#         try:
#             exp_month, exp_year = map(int, expiry_date.split('/'))
#             token = stripe.Token.create(
#                 card={
#                     'number': card_number,
#                     'exp_month': exp_month,
#                     'exp_year': exp_year,
#                     'cvc': cvv,
#                 }
#             )
#             return token.id
#         except ValueError:
#             return None  # Agar split qilishda muammo bo'lsa
#         except stripe.error.StripeError:
#             return None  # Stripe bilan bog'liq xato