import uuid

from django.contrib.auth.models import AbstractUser,Group, Permission

from django.db import models

from .utils import generate_otp_code
from .validators import validate_uz_number




class User(AbstractUser):
    USER_TYPE_CHOICES = (
        (1, 'User'),
        (2, 'Admin'),
    )
    username = models.CharField(max_length=14, unique=True, validators=[validate_uz_number])
    is_verified = models.BooleanField(default=False)
    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)
    user_type = models.IntegerField(choices=USER_TYPE_CHOICES, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.username} - {self.user_type}'





class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.IntegerField(default=generate_otp_code)
    otp_key = models.UUIDField(default=uuid.uuid4)

    otp_token = models.UUIDField(default=uuid.uuid4())
    attempts = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

class Card(models.Model):
    pan = models.IntegerField(default=0, validators=[])
    expire_month = models.IntegerField(default=0, validators=[])
    expire_year = models.IntegerField(default=0, validators=[])
    phone_number = models.CharField(max_length=13,validators=[])
    card_holder = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    balance = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.owner_name