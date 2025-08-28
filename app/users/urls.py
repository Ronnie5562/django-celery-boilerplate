"""
URL mapping for users App APIs.
"""
from django.urls import path
from users import views
from rest_framework_simplejwt.views import (
    TokenVerifyView,
)

app_name = "users"

urlpatterns = [
    path(
        "",
        views.ListCreateUserView.as_view(),
        name="users_list_create"
    ),
    path(
        "<uuid:id>/",
        views.DetailUserView.as_view(),
        name="user_details"
    ),
    path(
        "me/",
        views.ManageProfileView.as_view(),
        name="manage_profile"
    ),
    path(
        "activate/<str:uidb64>/<str:token>/",
        views.ActivateAccountAPIView.as_view(),
        name="activate",
    ),
    path(
        'password-reset/',
        views.PasswordResetView.as_view(),
        name='password_reset'
    ),
    path(
        'password-reset-confirm/<str:uidb64>/<str:token>/',
        views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    path(
        "token/", views.JWTCookieTokenObtainPairView.as_view(),
        name="token_obtain_pair"
    ),
    path(
        "token/refresh/",
        views.JWTCookieTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "token/verify/",
        TokenVerifyView.as_view(),
        name="token_verify"
    ),
    path(
        "logout/",
        views.LogOutAPIView.as_view(),
        name="token_verify"
    ),
]
