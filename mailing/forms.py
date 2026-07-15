"""Формы приложения mailing."""

from django import forms

from mailing.models import Client, Mailing, Message


class StyleFormMixin:
    """Добавляет Bootstrap-стили полям формы."""

    def add_styles(self):
        """Проставляет CSS-классы."""
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"


class ClientForm(StyleFormMixin, forms.ModelForm):
    """Форма получателя."""

    class Meta:
        model = Client
        fields = (
            "email",
            "full_name",
            "comment",
        )

    def __init__(self, *args, **kwargs):
        """Добавляет стили."""
        super().__init__(*args, **kwargs)
        self.add_styles()


class MessageForm(StyleFormMixin, forms.ModelForm):
    """Форма сообщения."""

    class Meta:
        model = Message
        fields = (
            "subject",
            "body",
        )

    def __init__(self, *args, **kwargs):
        """Добавляет стили."""
        super().__init__(*args, **kwargs)
        self.add_styles()


class MailingForm(StyleFormMixin, forms.ModelForm):
    """Форма рассылки."""

    class Meta:
        model = Mailing
        fields = (
            "start_time",
            "end_time",
            "message",
            "recipients",
        )
        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "recipients": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, user=None, **kwargs):
        """Фильтрует сообщения и получателей текущего пользователя."""
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields["message"].queryset = Message.objects.filter(owner=user)
            self.fields["recipients"].queryset = Client.objects.filter(owner=user)

        self.add_styles()
