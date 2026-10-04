from datetime import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from workshop_manager.models import (
    DailyAttendance,
)


class Command(BaseCommand):

    help = (
        "Automatically checkout trainers who are still working "
        "at 8:30 PM."
    )

    def handle(self, *args, **options):

        today = timezone.localdate()

        checkout_time = time(20, 30)

        checkout_datetime = timezone.make_aware(
            timezone.datetime.combine(
                today,
                checkout_time
            ),
            timezone.get_current_timezone()
        )

        open_attendance = (
            DailyAttendance.objects
            .filter(
                date=today,
                trainer__is_full_time=True,
                check_in__isnull=False,
                check_out__isnull=True,
            )
        )

        count = 0

        for attendance in open_attendance:

            # Safety check
            if attendance.check_in >= checkout_datetime:
                continue

            attendance.check_out = checkout_datetime

            attendance.save(
                update_fields=[
                    "check_out"
                ]
            )

            count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    (
                        f"Auto checkout: "
                        f"{attendance.trainer.Name} "
                        f"at 08:30 PM"
                    )
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Auto checkout completed. {count} trainer(s) updated."
            )
        )