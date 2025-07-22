from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random
import requests

from .models import EmailVerification, UserInfo
from .serializers import RegisterSerializer, OTPVerifySerializer

# Utility functions
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

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

            # Get IP and Country
            ip = get_client_ip(request)
            country = get_country_from_ip(ip)

            # Save UserInfo
            UserInfo.objects.create(user=user, ip_address=ip, country=country)

            # Send OTP
            otp_code = str(random.randint(100000, 999999))
            EmailVerification.objects.update_or_create(
                user=user,
                defaults={'otp_code': otp_code, 'created_at': timezone.now()}
            )

            send_mail(
                'Your OTP',
                f'Your OTP is {otp_code}',
                'ummemuna14@gmail.com',
                [email],
                fail_silently=True
            )

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
                return Response({'error': 'Invalid email or OTP.'}, status=status.HTTP_400_BAD_REQUEST)

            # OTP expired check (1 minute)
            time_diff = timezone.now() - verification.created_at
            if time_diff > timedelta(minutes=1):
                # OTP expired, generate new
                new_otp = str(random.randint(100000, 999999))
                verification.otp_code = new_otp
                verification.created_at = timezone.now()
                verification.save()

                send_mail(
                    'New OTP Code',
                    f'Your OTP has expired. Your new OTP code is {new_otp}',
                    'ummemuna14@gmail.com',
                    [email],
                    fail_silently=True
                )

                return Response({'error': 'OTP expired. New OTP sent to your email.'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate OTP
            if verification.otp_code != otp_code:
                return Response({'error': 'Enter correct OTP.'}, status=status.HTTP_400_BAD_REQUEST)

            # Success → Activate user and send welcome mail
            user.is_active = True
            user.save()
            verification.delete()

            send_mail(
                'Registration Successful',
                'Your registration is complete and your account is now active. Welcome!',
                'ummemuna14@gmail.com',
                [email],
                fail_silently=True
            )

            return Response({'message': 'Email verified successfully.'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
