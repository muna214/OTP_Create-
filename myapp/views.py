from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random
import requests
from django.conf import settings

from .models import EmailVerification, UserInfo
from .serializers import RegisterSerializer, OTPVerifySerializer

# Utility Functions
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def get_country_from_ip(ip):
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/")
        if response.status_code == 200:
            data = response.json()
            return data.get("country_name", "Unknown")
    except:
        pass
    return "Unknown"

# Register View
class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            if User.objects.filter(username=email).exists():
                return Response({'error': 'User already exists'}, status=400)

            user = serializer.save()

            ip = get_client_ip(request)
            print(f"Detected IP: {ip}")  # For testing only
            country = get_country_from_ip(ip)

            UserInfo.objects.create(user=user, ip_address=ip, country=country)

            otp_code = str(random.randint(100000, 999999))
            EmailVerification.objects.update_or_create(
                user=user,
                defaults={'otp_code': otp_code, 'created_at': timezone.now()}
            )

            send_mail(
                'Your OTP Code',
                f'Your OTP is: {otp_code}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True
            )

            print(f"OTP sent to {email}: {otp_code}")  # Debug only
            return Response({'message': 'Registered. OTP sent to email.'})

        return Response(serializer.errors, status=400)

# OTP Verification View
class VerifyOTPView(generics.GenericAPIView):
    serializer_class = OTPVerifySerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']

            try:
                user = User.objects.get(email=email)
                verification = EmailVerification.objects.get(user=user)
            except (User.DoesNotExist, EmailVerification.DoesNotExist):
                return Response({'error': 'Invalid email or OTP.'}, status=400)

            if verification.is_expired():
                new_otp = str(random.randint(100000, 999999))
                verification.otp_code = new_otp
                verification.created_at = timezone.now()
                verification.save()

                send_mail(
                    'New OTP Code',
                    f'Your OTP has expired. Your new OTP is: {new_otp}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=True
                )

                return Response({'error': 'OTP expired. New OTP sent.'}, status=400)

            if verification.otp_code != otp_code:
                return Response({'error': 'Incorrect OTP.'}, status=400)

            user.is_active = True
            user.save()
            verification.delete()

            send_mail(
                'Registration Complete',
                'Your account is now active. Welcome!',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True
            )

            return Response({'message': 'Email verified successfully.'})

        return Response(serializer.errors, status=400)
