import logging
from users.tokens import generate_token
from users.serializers import (
    UserSerializer,
    CustomTokenObtainPairSerializer,
    JWTCookieTokenRefreshSerializer,
    AccountActivationSerializer,
    LogOutSerializer,
)
from django.shortcuts import redirect
from rest_framework.views import APIView
from django.utils.encoding import force_str
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from users.email_services import EmailService
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from utils.permissions import IsAdminOrCreateOnly
from django.utils.http import urlsafe_base64_decode
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
            email_service.send_account_verification_email(user)
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
