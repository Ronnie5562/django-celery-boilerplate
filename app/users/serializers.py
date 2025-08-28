from django.conf import settings
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import InvalidToken


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the user object
    """

    class Meta:
        model = get_user_model()
        exclude = (
            "groups",
            "is_staff",
            "is_active",
            "last_login",
            "is_superuser",
            "date_modified",
            "user_permissions",
        )
        required_fields = [
            "email",
            "password",
        ]
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 5},
        }

    def create(self, validated_data):
        """
        Create a user with encrypted password and returns the user instance
        """
        return get_user_model().objects.create_user(
            **validated_data, is_active=False
        )

    def update(self, instance, validated_data):
        """
        Update a user, setting the password correctly and return it
        """
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["photo"] = serializers.CharField(read_only=True)
        self.fields["name"] = serializers.CharField(read_only=True)
        self.fields["email"] = serializers.CharField()

    def validate(self, attrs):
        # Check if the user's account is active
        email = attrs.get("email").strip().lower()
        user_ = User.objects.filter(email=email).first()

        if not user_:
            raise ValidationError(
                {
                    "email": "User with this email does not exist.",
                    "code": "user_not_found",
                }
            )

        if not user_.is_active:
            raise ValidationError(
                {
                    "email": "Account not yet activated. Verify your email.",
                    "code": "account_not_activated",
                },
            )

        if not user_.check_password(attrs["password"]):
            raise ValidationError(
                {
                    "password": "Incorrect password.",
                    "code": "incorrect_password"
                }
            )

        # Validate email and password
        data = super().validate(attrs)

        data["email"] = self.user.email
        data["first_name"] = self.user.first_name or ""
        data["last_name"] = self.user.last_name or ""
        data["user_id"] = self.user.id

        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token


class JWTCookieTokenRefreshSerializer(TokenRefreshSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["refresh"] = serializers.CharField(write_only=True)

    refresh = None

    def validate(self, attrs):
        attrs["refresh"] = attrs.get(settings.SIMPLE_JWT["REFRESH_TOKEN_NAME"])

        if attrs["refresh"]:
            return super().validate(attrs)
        else:
            raise InvalidToken("No valid refresh token found")


class AccountActivationSerializer(serializers.Serializer):
    pass


class LogOutSerializer(serializers.Serializer):
    pass


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)
