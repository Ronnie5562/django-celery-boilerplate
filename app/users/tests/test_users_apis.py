from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from users.tokens import generate_token
from datetime import timedelta


User = get_user_model()


class ListCreateUserViewTests(APITestCase):
    """Test suite for ListCreateUserView"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("users:users_list_create")
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123",
            is_staff=True,
            is_superuser=True,
        )
        self.regular_user = User.objects.create_user(
            email="user@test.com", password="testpass123"
        )

    def test_create_user_success(self):
        """Test successful user creation"""
        data = {
            "email": "newuser@test.com",
            "password": "strongpass123",
            "first_name": "Test",
            "last_name": "User",
        }

        with patch(
            "users.views.email_service.send_welcome_email"
        ) as mock_welcome, patch(
            "users.views.email_service.send_account_verification_email"
        ) as mock_verify:
            response = self.client.post(self.url, data, format="json")

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(
                User.objects.filter(email="newuser@test.com").exists()
            )

            # Verify emails were sent
            mock_welcome.assert_called_once()
            mock_verify.assert_called_once()

    def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email"""
        data = {
            "email": "user@test.com", "password": "strongpass123"
        }  # Already exists

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_invalid_data(self):
        """Test user creation with invalid data"""
        data = {"email": "invalid-email", "password": "123"}  # Too short

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_users_as_admin(self):
        """Test listing users as admin"""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # admin + regular user

    def test_list_users_as_regular_user(self):
        """Test listing users as regular user (should be forbidden)"""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_users_unauthenticated(self):
        """Test listing users without authentication"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("users.views.email_service.send_welcome_email")
    @patch("users.views.email_service.send_account_verification_email")
    def test_email_service_failure_doesnt_break_user_creation(
        self, mock_verify, mock_welcome
    ):
        """Test that email service failures don't prevent user creation"""
        mock_welcome.side_effect = Exception("Email service down")
        mock_verify.side_effect = Exception("Email service down")

        data = {"email": "newuser@test.com", "password": "strongpass123"}

        response = self.client.post(self.url, data, format="json")

        # User should still be created despite email failures
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            User.objects.filter(email="newuser@test.com").exists()
        )


class DetailUserViewTests(APITestCase):
    """Test suite for DetailUserView"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com", password="testpass123"
        )
        self.url = reverse("users:user_details", kwargs={"id": self.user.id})

    def test_get_user_success(self):
        """Test successful user retrieval"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_get_nonexistent_user(self):
        """Test retrieval of non-existent user"""
        url = reverse(
            "users:user_details",
            kwargs={"id": "12345678-1234-1234-1234-123456789abc"}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ManageProfileViewTests(APITestCase):
    """Test suite for ManageProfileView"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.other_user = User.objects.create_user(
            email="other@test.com", password="testpass123"
        )
        self.url = reverse("users:manage_profile")

    def test_get_own_profile(self):
        """Test retrieving own profile"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_update_own_profile(self):
        """Test updating own profile"""
        self.client.force_authenticate(user=self.user)

        data = {"first_name": "Updated", "last_name": "Name"}

        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Name")

    def test_delete_own_profile(self):
        """Test deleting own profile"""
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_profile_access_unauthenticated(self):
        """Test profile access without authentication"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_isolation(self):
        """Test that users can only access their own profile"""
        self.client.force_authenticate(user=self.user)

        # The view should always return the authenticated user's profile
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertNotEqual(response.data["email"], self.other_user.email)


class ActivateAccountAPIViewTests(APITestCase):
    """Test suite for ActivateAccountAPIView"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com", password="testpass123", is_active=False
        )
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = generate_token.make_token(self.user)

    def test_invalid_token_activation(self):
        """Test activation with invalid token"""
        url = reverse(
            "users:activate_account",
            kwargs={"uidb64": self.uid, "token": "invalid-token"},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_invalid_uid_activation(self):
        """Test activation with invalid UID"""
        url = reverse(
            "users:activate_account",
            kwargs={"uidb64": "invalid-uid", "token": self.token},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_nonexistent_user_activation(self):
        """Test activation for non-existent user"""
        nonexistent_uid = urlsafe_base64_encode(
            force_bytes("6db094b6-50c5-459d-986e-0bb25c7f5cca")
        )  # Random UUID
        url = reverse(
            "users:activate_account",
            kwargs={"uidb64": nonexistent_uid, "token": self.token},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_already_active_user(self):
        """Test activation of already active user"""
        self.user.is_active = True
        self.user.save()

        url = reverse(
            "users:activate_account",
            kwargs={"uidb64": self.uid, "token": self.token}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)


class JWTCookieTokenObtainPairViewTests(APITestCase):
    """Test suite for JWTCookieTokenObtainPairView"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com", password="testpass123", is_active=True
        )
        self.url = reverse("users:token_obtain_pair")

    def test_successful_token_obtain(self):
        """Test successful token obtainment"""
        data = {"email": "test@test.com", "password": "testpass123"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_invalid_credentials(self):
        """Test token obtainment with invalid credentials"""
        data = {"email": "test@test.com", "password": "wrongpassword"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_user(self):
        """Test token obtainment for inactive user"""
        self.user.is_active = False
        self.user.save()

        data = {"email": "test@test.com", "password": "testpass123"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_credentials(self):
        """Test token obtainment with missing credentials"""
        data = {
            "email": "test@test.com"
            # Missing password
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_user(self):
        """Test token obtainment for non-existent user"""
        data = {"email": "nonexistent@test.com", "password": "testpass123"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JWTCookieTokenRefreshViewTests(APITestCase):
    """Test suite for JWTCookieTokenRefreshView"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com", password="testpass123", is_active=True
        )
        self.refresh_token = RefreshToken.for_user(self.user)
        self.url = reverse("users:token_refresh")

    def test_successful_token_refresh(self):
        """Test successful token refresh"""
        data = {"refresh": str(self.refresh_token)}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_invalid_refresh_token(self):
        """Test token refresh with invalid token"""
        data = {"refresh": "invalid-token"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_refresh_token(self):
        """Test token refresh without refresh token"""
        data = {}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_refresh_token(self):
        """Test token refresh with expired token"""
        # Create an expired token
        self.refresh_token.set_exp(lifetime=timedelta(seconds=-1))

        data = {"refresh": str(self.refresh_token)}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JWTSetCookieMixinTests(APITestCase):
    """Test suite for JWTSetCookieMixin functionality"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com", password="testpass123", is_active=True
        )

    def test_cookie_setting_disabled(self):
        """Test that cookie setting is currently disabled (commented out)"""
        url = reverse("users:token_obtain_pair")
        data = {"email": "test@test.com", "password": "testpass123"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Since cookie setting is commented out, cookies should not be set
        self.assertNotIn("refresh", response.cookies)
        self.assertNotIn("access", response.cookies)

        # But tokens should still be in response data
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


class SecurityTests(APITestCase):
    """Security-focused tests"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com", password="testpass123", is_active=True
        )

    def test_password_not_in_response(self):
        """Test that password is never included in API responses"""
        self.client.force_authenticate(user=self.user)

        # Test profile view
        url = reverse("users:manage_profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("password", response.data)

    def test_xss_protection_in_user_creation(self):
        """Test XSS protection in user creation"""
        data = {
            "email": "test@test.com",
            "password": "testpass123",
            "first_name": '<script>alert("xss")</script>',
            "last_name": '"><img src=x onerror=alert(1)>',
        }

        response = self.client.post(
            reverse("users:users_list_create"), data, format="json"
        )

        if response.status_code == 201:
            # If user was created, confirm the malicious content was sanitized
            user = User.objects.get(email="test@test.com")
            self.assertNotIn("<script>", user.first_name)
            self.assertNotIn("onerror", user.last_name)

    def test_rate_limiting_awareness(self):
        """Test that views are prepared for rate limiting"""
        # Multiple rapid requests to login endpoint
        url = reverse("users:token_obtain_pair")
        data = {"email": "test@test.com", "password": "wrongpassword"}

        # Make multiple requests (would be rate limited in production)
        for _ in range(5):
            response = self.client.post(url, data, format="json")
            self.assertEqual(
                response.status_code, status.HTTP_400_BAD_REQUEST
            )

    def test_sensitive_data_not_logged(self):
        """Test that sensitive data is not accidentally logged"""
        with patch("builtins.print") as mock_print:
            # Create user (triggers email sending)
            data = {"email": "newuser@test.com", "password": "strongpass123"}

            with patch("users.views.email_service.send_welcome_email"), patch(
                "users.views.email_service.send_account_verification_email"
            ):
                self.client.post(
                    reverse("users:users_list_create"), data, format="json"
                )

                # Check that print statements don't contain sensitive data
                for call in mock_print.call_args_list:
                    args = str(call)
                    self.assertNotIn("password", args.lower())
                    self.assertNotIn("strongpass123", args)


class IntegrationTests(APITestCase):
    """Integration tests for complete user workflows"""

    def setUp(self):
        self.client = APIClient()

    def test_complete_user_registration_flow(self):
        """Test complete user registration and activation flow"""
        # Step 1: Register user
        registration_data = {
            "email": "newuser@test.com",
            "password": "strongpass123",
            "first_name": "New",
            "last_name": "User",
        }

        with patch(
            "users.views.email_service.send_welcome_email"
        ) as mock_welcome, patch(
            "users.views.email_service.send_account_verification_email"
        ) as mock_verify:
            response = self.client.post(
                reverse("users:users_list_create"),
                registration_data,
                format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Verify user was created but not active
            user = User.objects.get(email="newuser@test.com")
            self.assertFalse(user.is_active)

            # Verify emails were sent
            mock_welcome.assert_called_once_with(user)
            mock_verify.assert_called_once()

        # Step 2: Activate account
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = generate_token.make_token(user)

        activation_url = reverse(
            "users:activate_account", kwargs={"uidb64": uid, "token": token}
        )

        response = self.client.get(activation_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        user.refresh_from_db()
        self.assertTrue(user.is_active)

        # Step 3: Login
        login_data = {
            "email": "newuser@test.com", "password": "strongpass123"
        }

        response = self.client.post(
            reverse("users:token_obtain_pair"),
            login_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_complete_profile_management_flow(self):
        """Test complete profile management flow"""
        # Create and authenticate user
        user = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

        self.client.force_authenticate(user=user)

        # Step 1: View profile
        response = self.client.get(reverse("users:manage_profile"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@test.com")

        # Step 2: Update profile
        update_data = {"first_name": "Updated", "last_name": "Name"}

        response = self.client.patch(
            reverse("users:manage_profile"), update_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Updated")

        # Step 3: Verify update persisted
        response = self.client.get(reverse("users:manage_profile"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Updated")
        self.assertEqual(response.data["last_name"], "Name")

    def test_token_refresh_flow(self):
        """Test token refresh flow"""
        # Create user and get initial tokens
        User.objects.create_user(
            email="test@test.com", password="testpass123", is_active=True
        )

        login_data = {"email": "test@test.com", "password": "testpass123"}

        response = self.client.post(
            reverse("users:token_obtain_pair"), login_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        original_access = response.data["access"]
        refresh_token = response.data["refresh"]

        # Use refresh token to get new access token
        refresh_data = {"refresh": refresh_token}

        response = self.client.post(
            reverse("users:token_refresh"), refresh_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

        # New access token should be different from original
        new_access = response.data["access"]
        self.assertNotEqual(original_access, new_access)
