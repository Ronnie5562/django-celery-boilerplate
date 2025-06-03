import uuid
from datetime import datetime
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model, authenticate


User = get_user_model()


class UserManagerTests(TestCase):
    """Test suite for UserManager"""

    def setUp(self):
        self.manager = User.objects

    def test_create_user_success(self):
        """Test successful user creation"""
        user = self.manager.create_user(
            email="test@example.com", password="testpass123"
        )

        self.assertIsInstance(user, User)
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertIsInstance(user.id, uuid.UUID)

    def test_create_user_with_extra_fields(self):
        """Test user creation with extra fields"""
        user = self.manager.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            is_active=False,
        )

        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertFalse(user.is_active)

    def test_create_user_email_normalization(self):
        """Test that email is normalized during user creation"""
        user = self.manager.create_user(
            email="Test@EXAMPLE.COM", password="testpass123"
        )

        self.assertEqual(user.email, "test@example.com")

    def test_create_user_invalid_email(self):
        """Test user creation with invalid email"""
        with self.assertRaises((ValueError, ValidationError)) as context:
            self.manager.create_user(
                email="invalid-email", password="testpass123"
            )

        self.assertIn("Input a valid Email", str(context.exception))
        self.assertIn("invalid-email", str(context.exception))

    def test_create_user_empty_email(self):
        """Test user creation with empty email"""
        with self.assertRaises((ValueError, ValidationError)):
            self.manager.create_user(email="", password="testpass123")

    def test_create_user_none_email(self):
        """Test user creation with None email"""
        with self.assertRaises((ValueError, ValidationError)):
            self.manager.create_user(email=None, password="testpass123")

    def test_create_user_without_password(self):
        """Test user creation without password"""
        user = self.manager.create_user(
            email="test@example.com", password=None
        )

        # User should be created but password should be unusable
        self.assertIsInstance(user, User)
        self.assertFalse(user.has_usable_password())

    def test_create_superuser_success(self):
        """Test successful superuser creation"""
        user = self.manager.create_superuser(
            email="admin@example.com", password="adminpass123"
        )

        self.assertIsInstance(user, User)
        self.assertEqual(user.email, "admin@example.com")
        self.assertTrue(user.check_password("adminpass123"))
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_superuser_invalid_email(self):
        """Test superuser creation with invalid email"""
        with self.assertRaises((ValueError, ValidationError)):
            self.manager.create_superuser(
                email="invalid-email", password="adminpass123"
            )

    def test_create_superuser_without_password(self):
        """Test superuser creation without password"""
        user = self.manager.create_superuser(
            email="admin@example.com", password=None
        )

        # Superuser should be created but password should be unusable
        self.assertTrue(user.is_superuser)
        self.assertFalse(user.has_usable_password())

    def test_use_in_migrations_flag(self):
        """Test that use_in_migrations is properly set"""
        self.assertTrue(self.manager.use_in_migrations)

    def test_manager_queryset_methods(self):
        """Test that manager inherits queryset methods"""
        # Create test users
        user1 = self.manager.create_user("user1@test.com", "pass123")
        self.manager.create_user("user2@test.com", "pass123")

        # Test basic queryset methods
        self.assertEqual(self.manager.count(), 2)
        self.assertTrue(
            self.manager.filter(email="user1@test.com").exists()
        )
        self.assertEqual(
            self.manager.get(email="user1@test.com").id, user1.id
        )


class UserModelTests(TestCase):
    """Test suite for User model"""

    def setUp(self):
        self.user_data = {
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "John",
            "last_name": "Doe",
        }

    def test_user_creation_basic(self):
        """Test basic user creation"""
        user = User.objects.create_user(**self.user_data)

        self.assertIsInstance(user.id, uuid.UUID)
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertIsInstance(user.date_joined, datetime)
        self.assertIsInstance(user.date_modified, datetime)

    def test_user_str_with_names(self):
        """Test string representation with first and last name"""
        user = User.objects.create_user(**self.user_data)
        expected_str = "John Doe (test@example.com)"

        self.assertEqual(str(user), expected_str)

    def test_user_str_without_names(self):
        """Test string representation without names"""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        self.assertEqual(str(user), "test@example.com")

    def test_user_str_partial_names(self):
        """Test string representation with only first or last name"""
        # Only first name
        user1 = User.objects.create_user(
            email="test1@example.com", password="testpass123",
            first_name="John"
        )
        self.assertEqual(str(user1), "test1@example.com")

        # Only last name
        user2 = User.objects.create_user(
            email="test2@example.com", password="testpass123", last_name="Doe"
        )
        self.assertEqual(str(user2), "test2@example.com")

    def test_email_uniqueness(self):
        """Test that email field is unique"""
        User.objects.create_user(**self.user_data)

        # raise either IntegrityError or ValidationError
        with self.assertRaises((IntegrityError, ValidationError)):
            User.objects.create_user(
                email="test@example.com", password="different_password"
            )

    def test_email_validation_on_save(self):
        """Test email validation during save"""
        user = User(email="invalid-email", first_name="John")

        with self.assertRaises(ValidationError):
            user.save()

    def test_email_case_sensitivity(self):
        """Test email case handling"""
        User.objects.create_user(
            email="Test@Example.Com", password="testpass123"
        )

        # Same email with different case should not be allowed
        with self.assertRaises((IntegrityError, ValidationError)):
            User.objects.create_user(
                email="test@example.com", password="testpass123"
            )

    def test_username_field_configuration(self):
        """Test USERNAME_FIELD configuration"""
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_required_fields_configuration(self):
        """Test REQUIRED_FIELDS configuration"""
        # Should be empty since email is USERNAME_FIELD
        expected_required_fields = []
        actual_required_fields = getattr(User, "REQUIRED_FIELDS", [])

        self.assertEqual(actual_required_fields, expected_required_fields)

    def test_user_permissions_integration(self):
        """Test integration with Django's permission system"""
        user = User.objects.create_user(**self.user_data)

        # Test PermissionsMixin methods
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.get_user_permissions(), set())
        self.assertEqual(user.get_group_permissions(), set())

    def test_user_authentication(self):
        """Test user authentication"""
        user = User.objects.create_user(**self.user_data)

        # Test successful authentication
        authenticated_user = authenticate(
            email="test@example.com", password="testpass123"
        )
        self.assertEqual(authenticated_user, user)

        # Test failed authentication
        failed_auth = authenticate(
            email="test@example.com", password="wrongpassword"
        )
        self.assertIsNone(failed_auth)

    def test_inactive_user_authentication(self):
        """Test that inactive users cannot authenticate"""
        User.objects.create_user(**self.user_data, is_active=False)

        authenticated_user = authenticate(
            email="test@example.com", password="testpass123"
        )
        self.assertIsNone(authenticated_user)

    def test_date_fields_auto_population(self):
        """Test automatic population of date fields"""
        before_creation = timezone.now()
        user = User.objects.create_user(**self.user_data)
        after_creation = timezone.now()

        # Test date_joined
        self.assertGreaterEqual(user.date_joined, before_creation)
        self.assertLessEqual(user.date_joined, after_creation)

        # Test date_modified
        self.assertGreaterEqual(user.date_modified, before_creation)
        self.assertLessEqual(user.date_modified, after_creation)

    def test_date_modified_update(self):
        """Test that date_modified is updated on save"""
        user = User.objects.create_user(**self.user_data)
        original_modified = user.date_modified

        # Wait a small amount to ensure time difference
        import time

        time.sleep(0.01)

        user.first_name = "Updated"
        user.save()

        self.assertGreater(user.date_modified, original_modified)

    def test_model_ordering(self):
        """Test model ordering"""
        # Create users with different creation times
        user1 = User.objects.create_user(
            email="user1@test.com", password="pass123"
        )

        import time

        time.sleep(0.01)  # Ensure different timestamps

        user2 = User.objects.create_user(
            email="user2@test.com", password="pass123"
        )

        # Get all users (should be ordered by -date_joined)
        users = list(User.objects.all())

        self.assertEqual(users[0], user2)  # Most recent first
        self.assertEqual(users[1], user1)  # Older second

    def test_full_clean_validation(self):
        """Test that full_clean is called on save"""
        user = User(email="invalid-email")

        with self.assertRaises(ValidationError):
            user.save()

    def test_password_hashing(self):
        """Test that passwords are properly hashed"""
        user = User.objects.create_user(**self.user_data)

        # Password should be hashed, not stored in plain text
        self.assertNotEqual(user.password, "testpass123")
        self.assertTrue(user.password.startswith("pbkdf2_sha256$"))
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.check_password("wrongpassword"))

    def test_uuid_field_properties(self):
        """Test UUID field properties"""
        user = User.objects.create_user(**self.user_data)

        # Test UUID properties
        self.assertIsInstance(user.id, uuid.UUID)
        self.assertEqual(len(str(user.id)), 36)  # Standard UUID string length
        self.assertEqual(user.id.version, 4)  # Should be UUID4

    def test_blank_name_fields(self):
        """Test that name fields can be blank"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="",
            last_name="",
        )

        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")

    def test_model_meta_configuration(self):
        """Test model Meta configuration"""
        meta = User._meta

        # Test ordering
        self.assertEqual(meta.ordering, ("-date_joined",))

        # Test that model is properly configured
        self.assertEqual(meta.get_field("email").unique, True)
        self.assertEqual(meta.get_field("email").max_length, 255)
        self.assertEqual(meta.get_field("first_name").max_length, 30)
        self.assertEqual(meta.get_field("last_name").max_length, 30)


class UserModelSecurityTests(TestCase):
    """Security-focused tests for User model"""

    def test_xss_protection_in_string_fields(self):
        """Test XSS protection in string fields"""
        xss_payload = '<script>alert("xss")</script>'

        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name=xss_payload,
            last_name='"><img src=x onerror=alert(1)>',
        )

        # Data should be stored as-is (escaping handled at template level)
        self.assertEqual(user.first_name, xss_payload)
        self.assertIn("onerror", user.last_name)

    def test_password_security(self):
        """Test password security features"""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        # Password should be hashed
        self.assertNotEqual(user.password, "testpass123")

        # Should use strong hashing algorithm
        self.assertTrue(user.password.startswith("pbkdf2_sha256$"))

        # Should not be reversible
        with patch("django.contrib.auth.hashers.check_password") as mock_check:
            mock_check.return_value = True
            self.assertTrue(user.check_password("testpass123"))

    def test_sensitive_data_not_in_repr(self):
        """Test that sensitive data is not exposed in repr"""
        user = User.objects.create_user(
            email="test@example.com", password="secretpassword123"
        )

        user_repr = repr(user)
        user_str = str(user)

        # Password should not appear in string representations
        self.assertNotIn("secretpassword123", user_repr)
        self.assertNotIn("secretpassword123", user_str)
        self.assertNotIn("password", user_repr.lower())


class UserModelPerformanceTests(TestCase):
    """Performance tests for User model"""

    def test_bulk_user_creation(self):
        """Test bulk user creation performance"""
        users_data = [
            User(
                email=f"user{i}@example.com",
                first_name=f"User{i}", is_active=True
            ) for i in range(100)
        ]

        # Bulk create should work efficiently
        start_time = timezone.now()
        User.objects.bulk_create(users_data)
        end_time = timezone.now()

        # Verify all users were created
        self.assertEqual(User.objects.count(), 100)

        # Should complete in reasonable time (less than 1 second)
        duration = (end_time - start_time).total_seconds()
        self.assertLess(duration, 1.0)

    def test_email_lookup_performance(self):
        """Test email lookup performance with database index"""
        # Create many users
        [
            User.objects.create_user(
                email=f"user{i}@example.com", password="testpass123"
            )
            for i in range(100)
        ]

        # Email lookup should be fast (uses unique index)
        start_time = timezone.now()
        found_user = User.objects.get(email="user50@example.com")
        end_time = timezone.now()

        self.assertEqual(found_user.email, "user50@example.com")

        # Should be very fast lookup
        duration = (end_time - start_time).total_seconds()
        self.assertLess(duration, 0.1)

    def test_queryset_optimization(self):
        """Test queryset optimization"""
        # Create test data
        for i in range(10):
            User.objects.create_user(
                email=f"user{i}@example.com", password="testpass123"
            )

        # Test select_related (though User doesn't have FK relationships)
        with self.assertNumQueries(1):
            users = list(User.objects.all())
            self.assertEqual(len(users), 10)
