"""Формы приложения users."""

from django import forms
from django.core.exceptions import ValidationError

from users.models import User


class UserRegisterForm(forms.ModelForm):
    """Форма регистрации пользователя."""

    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone",
            "city",
            "avatar",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        """Добавляет стили полям формы."""
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean_email(self):
        """Проверяет уникальность email."""
        email = self.cleaned_data["email"]

        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")

        return email

    def clean(self):
        """Проверяет совпадение паролей."""
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают.")

        return cleaned_data

    def save(self, commit=True):
        """Создает пользователя с неактивным аккаунтом до подтверждения email."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = False
        user.is_email_confirmed = False

        if commit:
            user.save()

        return user
