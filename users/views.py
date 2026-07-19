"""Контроллеры приложения users."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView

from users.forms import UserRegisterForm
from users.models import User


class RegisterView(CreateView):
    """Регистрирует пользователя и отправляет письмо подтверждения."""

    model = User
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:email_confirmation_sent")

    def form_valid(self, form):
        """Создает пользователя и отправляет ссылку подтверждения."""
        response = super().form_valid(form)

        confirm_url = self.request.build_absolute_uri(
            reverse(
                "users:email_confirm",
                kwargs={
                    "token": self.object.email_confirmation_token,
                },
            )
        )

        send_mail(
            subject="Email confirmation",
            message=confirm_url,
            from_email=None,
            recipient_list=[self.object.email],
            fail_silently=False,
        )

        return response


class EmailConfirmView(View):
    """Подтверждает email пользователя."""

    def get(self, request, token):
        """Активирует пользователя по UUID-токену."""
        user = get_object_or_404(User, email_confirmation_token=token)

        user.is_active = True
        user.is_email_confirmed = True
        user.email_confirmation_token = None
        user.save(
            update_fields=[
                "is_active",
                "is_email_confirmed",
                "email_confirmation_token",
            ]
        )

        login(request, user)

        return redirect("mailing:home")


class EmailConfirmationSentView(View):
    """Показывает сообщение об отправке письма."""

    def get(self, request):
        """Возвращает страницу с сообщением."""
        return render(request, "users/email_confirmation_sent.html")


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Список пользователей для менеджера."""

    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    permission_required = "users.can_block_user"
    raise_exception = True


class UserBlockView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Блокирует пользователя сервиса."""

    permission_required = "users.can_block_user"
    raise_exception = True

    def post(self, request, pk):
        """Блокирует выбранного пользователя."""
        user = get_object_or_404(User, pk=pk)

        if user == request.user:
            messages.error(request, "Нельзя заблокировать самого себя.")
            return redirect("users:user_list")

        user.is_active = False
        user.save(update_fields=["is_active"])

        messages.success(request, "Пользователь заблокирован.")

        return redirect("users:user_list")
