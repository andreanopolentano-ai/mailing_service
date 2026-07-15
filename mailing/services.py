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

    return user.groups.filter(name="Менеджер").exists() or user.is_superuser


def send_mailing(mailing: Mailing) -> tuple[int, int]:
    """Отправляет рассылку и сохраняет попытки."""
    mailing.update_status()

    now = timezone.now()

    if not mailing.is_active:
        raise ValueError("Рассылка отключена.")

    if not (mailing.start_time <= now <= mailing.end_time):
        raise ValueError("Рассылку можно отправить только в разрешенный период.")

    success_count = 0
    failed_count = 0

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
                MailingAttempt.objects.create(
                    mailing=mailing,
                    status=MailingAttempt.STATUS_SUCCESS,
                    server_response="Письмо отправлено успешно.",
                )
                success_count += 1
            else:
                MailingAttempt.objects.create(
                    mailing=mailing,
                    status=MailingAttempt.STATUS_FAILED,
                    server_response="Почтовый сервер не отправил письмо.",
                )
                failed_count += 1

        except Exception as error:
            MailingAttempt.objects.create(
                mailing=mailing,
                status=MailingAttempt.STATUS_FAILED,
                server_response=str(error),
            )
            failed_count += 1

    return success_count, failed_count


def get_dashboard_stats(user) -> dict:
    """Возвращает статистику главной страницы с серверным кешированием."""
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
        "unique_clients": clients.values("email").distinct().count(),
    }

    cache.set(cache_key, stats, 60)

    return stats
