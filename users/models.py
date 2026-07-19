"""Модели приложения users."""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from users.managers import UserManager


class User(AbstractUser):
    """Кастомная модель пользователя с авторизацией по email."""

    username = None

    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )
    phone = models.CharField(
        max_length=35,
        blank=True,
        null=True,
        verbose_name="Телефон",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Город",
    )
    avatar = models.ImageField(
        upload_to="users/avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар",
    )
    is_email_confirmed = models.BooleanField(
        default=False,
        verbose_name="Email подтвержден",
    )
    email_confirmation_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        blank=True,
        null=True,
        verbose_name="Токен подтверждения email",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
        permissions = [
            (
                "can_block_user",
                "Может блокировать пользователей",
            ),
        ]

    def __str__(self) -> str:
        """Возвращает строковое представление пользователя."""
        return self.email
