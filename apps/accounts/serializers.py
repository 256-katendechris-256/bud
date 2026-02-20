from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def _build_unique_username(email):
    base = slugify(email.split('@')[0])[:24] or 'user'
    candidate = base
    index = 1
    while User.objects.filter(username=candidate).exists():
        suffix = f"-{index}"
        candidate = f"{base[:max(1, 24 - len(suffix))]}{suffix}"
        index += 1
    return candidate


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'password2')

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        from .services import EmailVerificationService
    
        email = validated_data['email'].strip().lower()
        validated_data.pop('password2')

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    username=_build_unique_username(email),
                    password=validated_data['password'],
                    is_active=False,
                )
                EmailVerificationService.send_verification_email(user)
                return user
        except Exception as exc:
            raise serializers.ValidationError(
                {"email": f"Could not send verification email: {exc}"}
            )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs['email'].strip().lower()
        password = attrs['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError({"detail": "Invalid credentials"}) from exc

        if not user.check_password(password):
            raise serializers.ValidationError({"detail": "Invalid credentials"})
        if not user.email_verified:
            raise serializers.ValidationError({"detail": "Verify your email before logging in"})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "Your account is not approved yet"})

        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'email_verified',
            'username',
            'first_name',
            'last_name',
            'role',
            'is_active',
            'is_staff',
            'created_at',
        )
