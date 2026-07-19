"""Админка приложения mailing."""

from django.contrib import admin

from mailing.models import Client, Mailing, MailingAttempt, Message


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Админка получателей."""

    list_display = ("id", "email", "full_name", "owner")
    search_fields = ("email", "full_name")
    list_filter = ("owner",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Админка сообщений."""

    list_display = ("id", "subject", "owner")
    search_fields = ("subject", "body")
    list_filter = ("owner",)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    """Админка рассылок."""

    list_display = ("id", "start_time", "end_time", "status", "is_active", "owner")
    list_filter = ("status", "is_active", "owner")
    search_fields = ("message__subject",)


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    """Админка попыток рассылок."""

    list_display = ("id", "mailing", "attempt_time", "status")
    list_filter = ("status", "attempt_time")
