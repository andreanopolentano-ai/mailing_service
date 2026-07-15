"""Команда для ручной отправки рассылки."""

from django.core.management import BaseCommand, CommandError

from mailing.models import Mailing
from mailing.services import send_mailing


class Command(BaseCommand):
    """Отправляет рассылку по ID."""

    help = "Отправляет рассылку по ID"

    def add_arguments(self, parser):
        """Добавляет аргументы команды."""
        parser.add_argument("mailing_id", type=int)

    def handle(self, *args, **options):
        """Запускает отправку рассылки."""
        mailing_id = options["mailing_id"]

        try:
            mailing = Mailing.objects.get(pk=mailing_id)
        except Mailing.DoesNotExist as error:
            raise CommandError("Рассылка не найдена.") from error

        try:
            success_count, failed_count = send_mailing(mailing)
        except ValueError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            self.style.SUCCESS(
                f"Рассылка выполнена. Успешно: {success_count}. Ошибок: {failed_count}."
            )
        )
