"""Сервисы приложения mailing."""

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone

from mailing.models import Client, Mailing, MailingAttempt


def is_manager(user) -> bool:
    """Проверяет, является ли пользователь менеджером."""

    if not user.is_authenticated:
        return False

    return (
        user.groups.filter(name="Менеджер").exists()
        or user.is_superuser
    )


def invalidate_dashboard_cache(owner_id: int) -> None:
    """Сбрасывает кеш статистики владельца и менеджеров."""

    cache.delete_many(
        [
            "dashboard_stats_manager",
            f"dashboard_stats_user_{owner_id}",
        ]
    )


def send_mailing(mailing: Mailing) -> tuple[int, int]:
    """Отправляет рассылку и сохраняет попытки одним запросом."""

    mailing.update_status()

    now = timezone.now()

    if not mailing.is_active:
        raise ValueError("Рассылка отключена.")

    if not mailing.start_time <= now <= mailing.end_time:
        raise ValueError(
            "Рассылку можно отправить только "
            "в разрешённый период."
        )

    success_count = 0
    failed_count = 0
    attempts = []

    for recipient in mailing.recipients.all():
        try:
            result = send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )

            if result:
                attempt_status = MailingAttempt.STATUS_SUCCESS
                server_response = "Письмо отправлено успешно."
                success_count += 1
            else:
                attempt_status = MailingAttempt.STATUS_FAILED
                server_response = (
                    "Почтовый сервер не отправил письмо."
                )
                failed_count += 1

        except Exception as error:
            attempt_status = MailingAttempt.STATUS_FAILED
            server_response = str(error)
            failed_count += 1

        attempts.append(
            MailingAttempt(
                mailing=mailing,
                status=attempt_status,
                server_response=server_response,
            )
        )

    MailingAttempt.objects.bulk_create(attempts)

    invalidate_dashboard_cache(
        owner_id=mailing.owner_id,
    )

    return success_count, failed_count


def get_dashboard_stats(user) -> dict:
    """Возвращает кешированную статистику главной страницы."""

    if is_manager(user):
        cache_key = "dashboard_stats_manager"
    else:
        cache_key = f"dashboard_stats_user_{user.pk}"

    stats = cache.get(cache_key)

    if stats is not None:
        return stats

    if is_manager(user):
        mailings = Mailing.objects.all()
        clients = Client.objects.all()
    else:
        mailings = Mailing.objects.filter(owner=user)
        clients = Client.objects.filter(owner=user)

    for mailing in mailings:
        mailing.update_status()

    now = timezone.now()

    stats = {
        "total_mailings": mailings.count(),
        "active_mailings": mailings.filter(
            start_time__lte=now,
            end_time__gte=now,
            status=Mailing.STATUS_STARTED,
            is_active=True,
        ).count(),
        "unique_clients": (
            clients.values("email")
            .distinct()
            .count()
        ),
    }

    cache.set(
        cache_key,
        stats,
        60,
    )

    return stats
