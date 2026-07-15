"""Модели приложения mailing."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Client(models.Model):
    """Получатель рассылки."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clients",
        verbose_name="Владелец",
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )
    full_name = models.CharField(
        max_length=255,
        verbose_name="Ф. И. О.",
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Комментарий",
    )

    class Meta:
        verbose_name = "получатель"
        verbose_name_plural = "получатели"

    def __str__(self) -> str:
        """Возвращает строковое представление клиента."""
        return f"{self.full_name} <{self.email}>"


class Message(models.Model):
    """Сообщение для рассылки."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Владелец",
    )
    subject = models.CharField(
        max_length=255,
        verbose_name="Тема письма",
    )
    body = models.TextField(
        verbose_name="Тело письма",
    )

    class Meta:
        verbose_name = "сообщение"
        verbose_name_plural = "сообщения"

    def __str__(self) -> str:
        """Возвращает строковое представление сообщения."""
        return self.subject


class Mailing(models.Model):
    """Рассылка."""

    STATUS_CREATED = "created"
    STATUS_STARTED = "started"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Создана"),
        (STATUS_STARTED, "Запущена"),
        (STATUS_COMPLETED, "Завершена"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Владелец",
    )
    start_time = models.DateTimeField(
        verbose_name="Дата и время начала отправки",
    )
    end_time = models.DateTimeField(
        verbose_name="Дата и время окончания отправки",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        verbose_name="Статус",
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Сообщение",
    )
    recipients = models.ManyToManyField(
        Client,
        related_name="mailings",
        verbose_name="Получатели",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна",
    )

    class Meta:
        verbose_name = "рассылка"
        verbose_name_plural = "рассылки"
        permissions = [
            (
                "can_disable_mailing",
                "Может отключать рассылки",
            ),
        ]

    def __str__(self) -> str:
        """Возвращает строковое представление рассылки."""
        return f"Рассылка #{self.pk} — {self.get_status_display()}"

    def clean(self):
        """Проверяет корректность дат рассылки."""
        now = timezone.now()

        if self.start_time and self.pk is None and self.start_time < now:
            raise ValidationError("Дата начала рассылки не может быть в прошлом.")

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Дата начала должна быть раньше даты окончания.")

    def update_status(self):
        """Обновляет статус рассылки в зависимости от текущего времени."""
        now = timezone.now()

        if now < self.start_time:
            new_status = self.STATUS_CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = self.STATUS_STARTED
        else:
            new_status = self.STATUS_COMPLETED

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=["status"])

        return self.status


class MailingAttempt(models.Model):
    """Попытка отправки рассылки."""

    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Успешно"),
        (STATUS_FAILED, "Не успешно"),
    ]

    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Рассылка",
    )
    attempt_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время попытки",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="Статус",
    )
    server_response = models.TextField(
        blank=True,
        null=True,
        verbose_name="Ответ почтового сервера",
    )

    class Meta:
        verbose_name = "попытка рассылки"
        verbose_name_plural = "попытки рассылок"

    def __str__(self) -> str:
        """Возвращает строковое представление попытки."""
        return f"{self.mailing} — {self.get_status_display()}"
