"""Контроллеры приложения mailing."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_control
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from mailing.forms import ClientForm, MailingForm, MessageForm
from mailing.models import Client, Mailing, MailingAttempt, Message
from mailing.services import get_dashboard_stats, is_manager, send_mailing


@method_decorator(cache_control(private=True, max_age=60), name="dispatch")
class HomeView(LoginRequiredMixin, TemplateView):
    """Главная страница со статистикой."""

    template_name = "mailing/home.html"

    def get_context_data(self, **kwargs):
        """Добавляет статистику."""
        context = super().get_context_data(**kwargs)
        context.update(get_dashboard_stats(self.request.user))

        return context


class OwnerOrManagerDetailMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Разрешает просмотр владельцу или менеджеру."""

    raise_exception = True

    def test_func(self):
        """Проверяет право просмотра объекта."""
        obj = self.get_object()

        return obj.owner == self.request.user or is_manager(self.request.user)


class OwnerOnlyMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Разрешает изменение только владельцу."""

    raise_exception = True

    def test_func(self):
        """Проверяет владельца объекта."""
        obj = self.get_object()

        return obj.owner == self.request.user


class ClientListView(LoginRequiredMixin, ListView):
    """Список получателей."""

    model = Client
    template_name = "mailing/client_list.html"
    context_object_name = "clients"

    def get_queryset(self):
        """Возвращает клиентов пользователя или всех клиентов для менеджера."""
        if is_manager(self.request.user):
            return Client.objects.all()

        return Client.objects.filter(owner=self.request.user)


class ClientDetailView(OwnerOrManagerDetailMixin, DetailView):
    """Детальная страница получателя."""

    model = Client
    template_name = "mailing/client_detail.html"
    context_object_name = "client"


class ClientCreateView(LoginRequiredMixin, CreateView):
    """Создание получателя."""

    model = Client
    form_class = ClientForm
    template_name = "mailing/form.html"
    success_url = reverse_lazy("mailing:client_list")

    def form_valid(self, form):
        """Назначает владельца."""
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ClientUpdateView(OwnerOnlyMixin, UpdateView):
    """Редактирование получателя."""

    model = Client
    form_class = ClientForm
    template_name = "mailing/form.html"
    success_url = reverse_lazy("mailing:client_list")


class ClientDeleteView(OwnerOnlyMixin, DeleteView):
    """Удаление получателя."""

    model = Client
    template_name = "mailing/confirm_delete.html"
    success_url = reverse_lazy("mailing:client_list")


class MessageListView(LoginRequiredMixin, ListView):
    """Список сообщений."""

    model = Message
    template_name = "mailing/message_list.html"
    context_object_name = "messages_list"

    def get_queryset(self):
        """Возвращает сообщения пользователя."""
        return Message.objects.filter(owner=self.request.user)


class MessageDetailView(OwnerOnlyMixin, DetailView):
    """Детальная страница сообщения."""

    model = Message
    template_name = "mailing/message_detail.html"
    context_object_name = "message_object"


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Создание сообщения."""

    model = Message
    form_class = MessageForm
    template_name = "mailing/form.html"
    success_url = reverse_lazy("mailing:message_list")

    def form_valid(self, form):
        """Назначает владельца."""
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(OwnerOnlyMixin, UpdateView):
    """Редактирование сообщения."""

    model = Message
    form_class = MessageForm
    template_name = "mailing/form.html"
    success_url = reverse_lazy("mailing:message_list")


class MessageDeleteView(OwnerOnlyMixin, DeleteView):
    """Удаление сообщения."""

    model = Message
    template_name = "mailing/confirm_delete.html"
    success_url = reverse_lazy("mailing:message_list")


class MailingListView(LoginRequiredMixin, ListView):
    """Список рассылок."""

    model = Mailing
    template_name = "mailing/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        """Возвращает рассылки пользователя или все для менеджера."""
        if is_manager(self.request.user):
            queryset = Mailing.objects.all()
        else:
            queryset = Mailing.objects.filter(owner=self.request.user)

        for mailing in queryset:
            mailing.update_status()

        return queryset


class MailingDetailView(OwnerOrManagerDetailMixin, DetailView):
    """Детальная страница рассылки."""

    model = Mailing
    template_name = "mailing/mailing_detail.html"
    context_object_name = "mailing"

    def get_object(self, queryset=None):
        """Обновляет статус при просмотре рассылки."""
        obj = super().get_object(queryset)
        obj.update_status()

        return obj


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создание рассылки."""

    model = Mailing
    form_class = MailingForm
    template_name = "mailing/form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_form_kwargs(self):
        """Передает пользователя в форму."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user

        return kwargs

    def form_valid(self, form):
        """Назначает владельца."""
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(OwnerOnlyMixin, UpdateView):
    """Редактирование рассылки."""

    model = Mailing
    form_class = MailingForm
    template_name = "mailing/form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_form_kwargs(self):
        """Передает пользователя в форму."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user

        return kwargs


class MailingDeleteView(OwnerOnlyMixin, DeleteView):
    """Удаление рассылки."""

    model = Mailing
    template_name = "mailing/confirm_delete.html"
    success_url = reverse_lazy("mailing:mailing_list")


class MailingSendView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Ручной запуск рассылки."""

    raise_exception = True

    def test_func(self):
        """Проверяет владельца рассылки."""
        mailing = get_object_or_404(Mailing, pk=self.kwargs["pk"])

        return mailing.owner == self.request.user

    def post(self, request, pk):
        """Отправляет рассылку."""
        mailing = get_object_or_404(Mailing, pk=pk)

        try:
            success_count, failed_count = send_mailing(mailing)
            messages.success(
                request,
                f"Рассылка выполнена. Успешно: {success_count}. Ошибок: {failed_count}.",
            )
        except ValueError as error:
            messages.error(request, str(error))

        return redirect("mailing:mailing_detail", pk=mailing.pk)


class MailingDisableView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Отключение рассылки менеджером."""

    permission_required = "mailing.can_disable_mailing"
    raise_exception = True

    def post(self, request, pk):
        """Отключает рассылку."""
        mailing = get_object_or_404(Mailing, pk=pk)
        mailing.is_active = False
        mailing.save(update_fields=["is_active"])

        messages.success(request, "Рассылка отключена.")

        return redirect("mailing:mailing_detail", pk=mailing.pk)


class AttemptListView(LoginRequiredMixin, ListView):
    """Список попыток рассылок."""

    model = MailingAttempt
    template_name = "mailing/attempt_list.html"
    context_object_name = "attempts"

    def get_queryset(self):
        """Возвращает попытки по рассылкам пользователя или все для менеджера."""
        if is_manager(self.request.user):
            return MailingAttempt.objects.select_related("mailing").all()

        return MailingAttempt.objects.select_related("mailing").filter(
            mailing__owner=self.request.user
        )


class StatisticsView(LoginRequiredMixin, TemplateView):
    """Статистика рассылок пользователя."""

    template_name = "mailing/statistics.html"

    def get_context_data(self, **kwargs):
        """Добавляет статистику попыток."""
        context = super().get_context_data(**kwargs)

        if is_manager(self.request.user):
            attempts = MailingAttempt.objects.all()
        else:
            attempts = MailingAttempt.objects.filter(mailing__owner=self.request.user)

        context["success_attempts"] = attempts.filter(
            status=MailingAttempt.STATUS_SUCCESS
        ).count()
        context["failed_attempts"] = attempts.filter(
            status=MailingAttempt.STATUS_FAILED
        ).count()
        context["sent_messages"] = context["success_attempts"]

        return context
