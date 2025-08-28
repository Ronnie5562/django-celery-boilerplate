import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class UserManager(BaseUserManager):
    """
    Custom UserManager model that manages User model
    """

    use_in_migrations = True

    def create_user(self, email, password, **extra_fields):
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError(
                {"email": f"Input a valid Email: {email} is not valid"}
            )

        user = self.model(email=self.normalize_email(email), **extra_fields)

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    email = models.EmailField(
        max_length=255, unique=True, validators=[validate_email]
    )
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = "email"

    def save(self, *args, **kwargs):
        try:
            self.full_clean()
            self.email = self.email.lower()
        except Exception as e:
            raise e

        super(User, self).save(*args, **kwargs)

    def __str__(self):
        """String representation of a user"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.email})"
        return self.email

    def get_full_name(self):
        """Return the user's full name"""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """Return the user's short name"""
        return self.first_name or self.last_name or self.email.split('@')[0]

    class Meta:
        ordering = ("-date_joined",)
