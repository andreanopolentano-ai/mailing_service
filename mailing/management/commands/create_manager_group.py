"""Команда для создания группы менеджеров."""

from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand


class Command(BaseCommand):
    """Создает группу Менеджер и назначает права."""

    help = "Создает группу Менеджер"

    def handle(self, *args, **options):
        """Создает группу и назначает права."""
        group, _ = Group.objects.get_or_create(name="Менеджер")

        permissions = Permission.objects.filter(
            codename__in=[
                "can_block_user",
                "can_disable_mailing",
                "view_client",
                "view_mailing",
                "view_user",
            ]
        )

        group.permissions.set(permissions)

        self.stdout.write(
            self.style.SUCCESS("Группа 'Менеджер' создана и права назначены.")
        )
