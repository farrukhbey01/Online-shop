import uuid

from django.contrib.auth.models import AbstractUser,Group, Permission

from django.db import models

from .utils import generate_otp_code
from .validators import validate_uz_number




class User(AbstractUser):
    username = models.CharField(max_length=14, unique=True, validators=[validate_uz_number])
    is_verified = models.BooleanField(default=False)
    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)



    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username


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
    phone_number = models.IntegerField(max_length=12, validators=[])
    card_holder = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    balance = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.owner_name