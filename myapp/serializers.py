from rest_framework import serializers
from django.contrib.auth.models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']

    def create(self, validated_data):
        email = validated_data['email']
        user = User(
            username=email,
            email=email,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_active=False  # inactive until email verified
        )
        user.set_password(validated_data['password'])
        user.save()
        
        return user

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)
