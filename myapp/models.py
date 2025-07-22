from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.otp_code}"

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.ip_address} ({self.country})"

def is_expired(self):
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(minutes=5)