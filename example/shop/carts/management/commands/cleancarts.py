import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import translation, timezone
from django.conf import settings
from ...models import Cart


class Command(BaseCommand):
    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGE_CODE)

        with transaction.atomic(using=None):
            carts_times = {
                'anonymous': timezone.now() - datetime.timedelta(days=7),
                'userowned': timezone.now() - datetime.timedelta(days=28),
            }

            # clean anonymous carts
            Cart.objects.filter(
                user__isnull=True,
                date_update__lte=carts_times['anonymous']).delete()

            # clean user owned carts
            Cart.objects.filter(
                user__isnull=False,
                date_update__lte=carts_times['userowned']).delete()
