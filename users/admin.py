"""Админка приложения users."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Настройки отображения пользователей в админке."""

    list_display = (
        "id",
        "email",
        "phone",
        "city",
        "is_email_confirmed",
        "is_active",
        "is_staff",
    )
    list_filter = (
        "is_email_confirmed",
        "is_active",
        "is_staff",
        "city",
    )
    search_fields = (
        "email",
        "phone",
        "city",
    )
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Персональная информация",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone",
                    "city",
                    "avatar",
                )
            },
        ),
        (
            "Подтверждение",
            {
                "fields": (
                    "is_email_confirmed",
                )
            },
        ),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_email_confirmed",
                ),
            },
        ),
    )
