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

# --------- Utility Functions --------- #
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


# --------- Register View --------- #
class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            if User.objects.filter(username=email).exists():
                return Response({'error': 'User already exists'}, status=400)

            user = serializer.save()

            # IP + Country logging
            ip = get_client_ip(request)
            country = get_country_from_ip(ip)
            UserInfo.objects.create(user=user, ip_address=ip, country=country)

            # Generate and store OTP
            otp_code = str(random.randint(100000, 999999))
            EmailVerification.objects.update_or_create(
                user=user,
                defaults={'otp_code': otp_code, 'created_at': timezone.now()}
            )

            # Send OTP via email
            send_mail(
                subject='Your OTP Code',
                message=f'Your OTP is: {otp_code}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False
            )

            return Response({'message': 'Registered successfully. OTP sent to email.'}, status=201)

        return Response(serializer.errors, status=400)

# --------- OTP Verification View --------- #
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

            # Check expiry
            expiry_time = verification.created_at + timedelta(minutes=10)
            if timezone.now() > expiry_time:
                new_otp = str(random.randint(100000, 999999))
                verification.otp_code = new_otp
                verification.created_at = timezone.now()
                verification.save()

                send_mail(
                    subject='Your New OTP Code',
                    message=f'Your new OTP is: {new_otp}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False
                )
                return Response({'error': 'OTP expired. New OTP sent to email.'}, status=400)

            # Incorrect OTP
            if verification.otp_code != otp_code:
                return Response({'error': 'Incorrect OTP.'}, status=400)

            # Success
            user.is_active = True
            user.save()
            verification.delete()

            send_mail(
                subject='Registration Complete',
                message='Your account is now active. Welcome!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False
            )

            return Response({'message': 'Email verified and account activated.'}, status=200)

        return Response(serializer.errors, status=400)
