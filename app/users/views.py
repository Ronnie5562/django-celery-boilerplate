import logging
from users.tokens import generate_token
from users.serializers import (
    UserSerializer,
    CustomTokenObtainPairSerializer,
    JWTCookieTokenRefreshSerializer,
    AccountActivationSerializer,
    LogOutSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
)
from django.shortcuts import redirect
from rest_framework.views import APIView
from django.utils.encoding import force_str
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .throttle import PasswordResetThrottle
from users.email_services import EmailService
from django.contrib.auth import get_user_model
from utils.permissions import IsAdminOrCreateOnly
from django.utils.http import urlsafe_base64_decode
from django.utils.decorators import method_decorator
from rest_framework import generics, permissions, status
from django.contrib.auth.tokens import default_token_generator
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework_simplejwt.authentication import JWTAuthentication


email_service = EmailService()
logger = logging.getLogger(__name__)


class ListCreateUserView(generics.ListCreateAPIView):
    """View to create/list users
    Images Base url:
    """

    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()
    authentication_classes = []
    permission_classes = [IsAdminOrCreateOnly]

    def perform_create(self, serializer):
        """Create a new user"""
        user = serializer.save()

        try:
            email_service.send_welcome_email(user)
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")

        try:
            email_service.send_account_verification_email(
                self.request,
                user
            )
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")


class DetailUserView(generics.RetrieveAPIView):
    """APIView to retrieve a user"""

    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()
    lookup_field = "id"


class ManageProfileView(generics.RetrieveUpdateDestroyAPIView):
    """APIView to manage the authenticated user profile"""

    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Restricts users to manage only their own profile"""
        return self.request.user


class ActivateAccountAPIView(APIView):
    serializer_class = AccountActivationSerializer

    def get(self, request, uidb64, token):
        User = get_user_model()
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            myuser = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            myuser = None

        if myuser is not None and generate_token.check_token(myuser, token):
            myuser.is_active = True
            myuser.save()
            # Change to frontend signin url
            return redirect("http://localhost:5173/login/")
        else:
            # Change to a frontend page that says activation link is invalid
            # And provide a link to resend the activation link to their email
            return redirect("http://localhost:5173?activation=invalid")


class LogOutAPIView(APIView):
    serializer_class = LogOutSerializer
    # permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        response = Response("Logged out successfully")

        response.set_cookie("refresh_token", "", expires=0)
        response.set_cookie("access_token", "", expires=0)

        return response


class JWTSetCookieMixin:
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(
            request, response, *args, **kwargs
        )

        if isinstance(response, Response):
            refresh_token = response.data.get("refresh")  # noqa
            # if refresh_token:
            #     response.set_cookie(
            #         settings.SIMPLE_JWT.get(
            #             "REFRESH_TOKEN_NAME", "refresh"
            #         ),
            #         refresh_token,
            #         max_age=int(
            #             settings.SIMPLE_JWT.get(
            #                 "REFRESH_TOKEN_LIFETIME",
            #                 timedelta(days=1)
            #             ).total_seconds()
            #         ),
            #         httponly=True,
            #         samesite=settings.SIMPLE_JWT.get(
            #             "AUTH_COOKIE_SAMESITE", 'Lax'
            #         ),
            #         domain=settings.SIMPLE_JWT.get(
            #             "AUTH_COOKIE_DOMAIN", None
            #         ),
            #         secure=settings.SIMPLE_JWT.get(
            #             "AUTH_COOKIE_SECURE", True
            #         ),
            #     )

            access_token = response.data.get("access")  # noqa
            # if access_token:
            #     response.set_cookie(
            #         settings.SIMPLE_JWT.get(
            #             "ACCESS_TOKEN_NAME", "access"
            #         ),
            #         access_token,
            #         max_age=int(
            #             settings.SIMPLE_JWT.get(
            #                 "ACCESS_TOKEN_LIFETIME",
            #                 timedelta(minutes=5)
            #             ).total_seconds()
            #         ),
            #         httponly=True,
            #         samesite=settings.SIMPLE_JWT.get(
            #             "AUTH_COOKIE_SAMESITE", 'Lax'),
            #         domain=settings.SIMPLE_JWT.get(
            #             "AUTH_COOKIE_DOMAIN", None
            #         ),
            #         secure=settings.SIMPLE_JWT.get(
            #             "AUTH_COOKIE_SECURE", True
            #         ),
            #     )
            # del response.data["access"]

        return response


class JWTCookieTokenObtainPairView(JWTSetCookieMixin, TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class JWTCookieTokenRefreshView(JWTSetCookieMixin, TokenRefreshView):
    serializer_class = JWTCookieTokenRefreshSerializer


class PasswordResetView(APIView):
    serializer_class = PasswordResetSerializer
    throttle_classes = [PasswordResetThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        # print(serializer)
        serializer.is_valid(raise_exception=True)

        # Get user by email
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=serializer.validated_data['email'])
        except User.DoesNotExist:
            return Response(
                {
                    "detail": "A password reset link has been sent."
                },
                status=status.HTTP_200_OK
            )

        # Send password reset email
        email_service = EmailService()
        email_service.send_password_reset_link(request, user)

        return Response(
            {
                "detail": "Password reset e-mail has been sent."
            },
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    """
    Password reset confirmation endpoint.

    Validates the reset token and sets the new password.

    Parameters:
    - uid: Base64 encoded user ID3
    - token: Password reset token
    - new_password1: New password
    - new_password2: New password confirmation
    """
    serializer_class = PasswordResetConfirmSerializer

    @method_decorator(
        sensitive_post_parameters('new_password1', 'new_password2')
    )
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        uidb64 = kwargs.get('uidb64')
        token = kwargs.get('token')

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_user_model()._default_manager.get(pk=uid)
        except (
            TypeError, ValueError, OverflowError, get_user_model().DoesNotExist
        ):
            user = None

        if user is None or not default_token_generator.check_token(
            user, token
        ):
            return Response(
                {"detail": "Invalid password reset link"},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_password = serializer.validated_data['new_password1']
        user.set_password(new_password)
        user.save()

        return Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK
        )
