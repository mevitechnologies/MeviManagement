from django.contrib import admin

from .models import (
    College,
    Department,
    Trainer,
    Workshop,
    FollowUp,
    Notification,
    OfficeTraining,
    TodoTask,
    SubTask,
    FollowUpReminder,
    WorkshopRemarks
)


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = (
        "Name",
        "user",
        "email",
        "phone",
        "is_full_time",
        "is_available"
    )

    search_fields = (
        "Name",
        "email",
        "phone"
    )


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "college",
        "departments",
        "status",
        "start_date",
        "end_date"
    )

    list_filter = (
        "status",
        "departments"
    )


admin.site.register(College)
admin.site.register(Department)
admin.site.register(FollowUp)
admin.site.register(Notification)
admin.site.register(OfficeTraining)
admin.site.register(TodoTask)
admin.site.register(SubTask)
admin.site.register(FollowUpReminder)
admin.site.register(WorkshopRemarks)