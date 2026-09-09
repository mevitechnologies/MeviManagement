from datetime import date, timedelta
import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Workshop,
    Trainer,
    FollowUp,
    TodoTask,
    SubTask,
    OfficeTraining,
    College,
    CalendarEvent,
    DailyAttendance,
    MeetingNote,
    WorkshopRemarks,
)

from .forms import (
    WorkshopForm,
    TrainerForm,
    FollowUpForm,
    TodoTaskForm,
    SubTaskForm,
    SubTaskFormSet,
    OfficeTrainingForm,
    CollegeForm,
    MeetingNoteForm,
    CalendarEventForm,
    WorkshopRemarksForm,
)


# =====================================================
# HELPERS
# =====================================================
def is_superuser(user):
    return user.is_superuser

def is_staff_or_superuser(user):
    return user.is_staff or user.is_superuser



# =====================================================
# AUTH
# =====================================================


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "❌ Invalid username or password")

    return render(request, "login.html")




@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


# =====================================================
# MAIN DASHBOARD (VIEW ONLY)
# =====================================================



@login_required
def dashboard(request):

    import json
    from datetime import timedelta
    from django.urls import reverse

    today = timezone.localdate()

    # =====================================================
    # ALL TRAINERS
    # =====================================================

    trainers = (
        Trainer.objects
        .select_related("user")
        .order_by("Name")
    )

    total_trainers = trainers.count()

    # =====================================================
    # FULL-TIME TRAINERS
    # ONLY THESE ARE ELIGIBLE FOR CHECK-IN
    # =====================================================

    full_time_trainers = (
        Trainer.objects
        .filter(is_full_time=True)
        .select_related("user")
        .order_by("Name")
    )

    full_time_trainer_count = full_time_trainers.count()

    # =====================================================
    # TODAY'S ATTENDANCE
    # FULL-TIME ONLY
    # =====================================================

    attendance_records = (
        DailyAttendance.objects
        .filter(
            date=today,
            trainer__is_full_time=True
        )
        .select_related("trainer")
    )

    attendance_map = {
        attendance.trainer_id: attendance
        for attendance in attendance_records
    }

    checked_in_count = sum(
        1
        for attendance in attendance_records
        if attendance.check_in
    )

    working_count = sum(
        1
        for attendance in attendance_records
        if (
            attendance.check_in
            and not attendance.check_out
        )
    )

    not_checked_in_count = (
        full_time_trainer_count - checked_in_count
    )

    # Prevent negative value
    if not_checked_in_count < 0:
        not_checked_in_count = 0

    # =====================================================
    # TODAY'S TASKS
    # =====================================================

    today_tasks = (
        TodoTask.objects
        .filter(for_date=today)
        .select_related("trainer")
        .order_by(
            "trainer__Name",
            "-created_on"
        )
    )

    # =====================================================
    # TRAINER STATUS
    # FULL-TIME TRAINERS ONLY
    # =====================================================

    trainer_status = []

    for trainer in full_time_trainers:

        attendance = attendance_map.get(
            trainer.id
        )

        trainer_tasks = (
            today_tasks
            .filter(trainer=trainer)
            .order_by("-created_on")
        )

        latest_task = trainer_tasks.first()

        trainer_status.append({
            "trainer": trainer,
            "attendance": attendance,
            "latest_task": latest_task,
            "tasks": trainer_tasks,
        })

    # =====================================================
    # CALENDAR EVENTS
    # =====================================================

    events = []

    # -----------------------------------------------------
    # WORKSHOPS
    # -----------------------------------------------------

    workshops = (
        Workshop.objects
        .prefetch_related("assigned_trainers")
        .select_related("college")
        .all()
    )

    for workshop in workshops:

        trainer_names = ", ".join(
            trainer.Name
            for trainer in workshop.assigned_trainers.all()
        )

        event = {
            "title": f"📚 {workshop.title}",

            "start": (
                workshop.start_date.strftime("%Y-%m-%d")
                if workshop.start_date
                else None
            ),

            "end": (
                (workshop.end_date + timedelta(days=1))
                .strftime("%Y-%m-%d")
                if workshop.end_date
                else None
            ),

            "color": "#198754",

            "extendedProps": {
                "trainer": trainer_names,

                "college": (
                    workshop.college.name
                    if workshop.college
                    else ""
                ),

                "department": (
                    workshop.departments or ""
                ),

                "event_type": "Workshop",

                "description": (
                    workshop.remarks or ""
                ),
            }
        }

        event["url"] = reverse(
            "workshop_detail",
            args=[workshop.pk]
        )

        events.append(event)

    # -----------------------------------------------------
    # OFFICE TRAINING
    # -----------------------------------------------------

    office_trainings = (
        OfficeTraining.objects
        .prefetch_related("trainers")
        .all()
    )

    for training in office_trainings:

        trainer_names = ", ".join(
            trainer.Name
            for trainer in training.trainers.all()
        )

        event = {
            "title": f"🏢 {training.name}",

            "start": (
                training.start_date.strftime("%Y-%m-%d")
                if training.start_date
                else None
            ),

            "end": (
                (training.end_date + timedelta(days=1))
                .strftime("%Y-%m-%d")
                if training.end_date
                else None
            ),

            "color": "#0d6efd",

            "extendedProps": {
                "trainer": trainer_names,

                "college": "Mevi Technologies",

                "department": "",

                "event_type": "Office Training",

                "description": (
                    f"Batch: {training.batch_id}"
                    if training.batch_id
                    else ""
                ),
            }
        }

        event["url"] = reverse(
            "view_office_training",
            args=[training.pk]
        )

        events.append(event)

    # -----------------------------------------------------
    # MEETING NOTES
    # -----------------------------------------------------

    meetings = (
        MeetingNote.objects
        .prefetch_related("attendees")
        .all()
    )

    for meeting in meetings:

        attendees = ", ".join(
            trainer.Name
            for trainer in meeting.attendees.all()
        )

        events.append({
            "title": f"📝 {meeting.title}",

            "start": (
                meeting.meeting_date.strftime("%Y-%m-%d")
                if meeting.meeting_date
                else None
            ),

            "color": "#6f42c1",

            "extendedProps": {
                "trainer": attendees,

                "college": "",

                "department": "",

                "event_type": "Meeting",

                "description": (
                    meeting.discussion_points or ""
                ),
            }
        })

    # =====================================================
    # CURRENT LOGGED-IN TRAINER
    # =====================================================

    current_trainer = (
        Trainer.objects
        .filter(
            user=request.user
        )
        .first()
    )

    # Fallback for existing accounts
    if not current_trainer:

        current_trainer = (
            Trainer.objects
            .filter(
                email=request.user.email
            )
            .first()
        )

    # =====================================================
    # RENDER
    # =====================================================

    return render(
        request,
        "dashboard.html",
        {
            # Calendar
            "events_json": json.dumps(
                events,
                default=str
            ),

            # Date
            "today": today,

            # All trainers
            "trainers": trainers,

            "total_trainers": total_trainers,

            # Full-time / attendance
            "full_time_trainer_count":
                full_time_trainer_count,

            "trainer_status":
                trainer_status,

            "checked_in_count":
                checked_in_count,

            "working_count":
                working_count,

            "not_checked_in_count":
                not_checked_in_count,

            # Current logged-in trainer
            "current_trainer":
                current_trainer,

            # Today's tasks
            "today_tasks":
                today_tasks,
        }
    )

# =====================================================
# WORKSHOPS
# =====================================================

@login_required
def workshop_list(request):
    today = timezone.now().date()

    upcoming = Workshop.objects.filter(
        start_date__gt=today
    ).order_by("start_date")

    ongoing = Workshop.objects.filter(
        start_date__lte=today,
        end_date__gte=today
    ).order_by("start_date")

    tentative = Workshop.objects.filter(
        status="tentative",
        start_date__gte=today
    ).order_by("start_date")

    fixed = Workshop.objects.filter(
        status="fixed",
        start_date__gte=today
    ).order_by("start_date")

    # ❗ Past workshops that still need action
    post_workshop = Workshop.objects.filter(
        end_date__lt=today
    ).exclude(status__in=["completed", "cancelled"]).order_by("-end_date")

    # ✅ COMPLETED WORKSHOPS (NEW)
    completed = Workshop.objects.filter(
        status="completed"
    ).order_by("-end_date")

    return render(request, "workshop_list.html", {
        "upcoming": upcoming,
        "ongoing": ongoing,
        "tentative": tentative,
        "fixed": fixed,
        "post_workshop": post_workshop,
        "completed": completed,   # ✅ pass to template
        "today": today,
        "is_admin": request.user.is_staff,
    })


@login_required
def workshop_detail(request, pk):

    workshop = get_object_or_404(
        Workshop,
        pk=pk
    )

    trainer = Trainer.objects.filter(
        user=request.user
    ).first()

    trainer_report_exists = False
    can_add_remark = False

    if trainer:

        can_add_remark = workshop.assigned_trainers.filter(
            id=trainer.id
        ).exists()

        trainer_report_exists = WorkshopRemarks.objects.filter(
            workshop=workshop,
            trainer=trainer
        ).exists()

    context = {
        "workshop": workshop,
        "trainer": trainer,
        "can_add_remark": can_add_remark,
        "trainer_report_exists": trainer_report_exists,
    }

    return render(
        request,
        "workshop_detail.html",
        context
    )


@login_required
@user_passes_test(is_superuser)
def add_workshop(request):
    form = WorkshopForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Workshop added successfully")
        return redirect("workshop_list")
    return render(request, "add_workshop.html", {"form": form})


@login_required
@user_passes_test(is_superuser)
def edit_workshop(request, pk):
    workshop = get_object_or_404(Workshop, pk=pk)
    form = WorkshopForm(request.POST or None, instance=workshop)
    if form.is_valid():
        form.save()
        messages.success(request, "Workshop updated")
        return redirect("workshop_list")
    return render(request, "edit_workshop.html", {"form": form})


@login_required
@user_passes_test(is_superuser)
def delete_workshop(request, pk):
    get_object_or_404(Workshop, pk=pk).delete()
    messages.success(request, "Workshop deleted")
    return redirect("workshop_list")


@login_required
@user_passes_test(is_superuser)
def update_workshop_status(request, pk, status):
    workshop = get_object_or_404(Workshop, pk=pk)
    if status not in ["completed", "cancelled", "postponed"]:
        messages.error(request, "Invalid status")
        return redirect("workshop_list")
    workshop.status = status
    workshop.save()
    messages.success(request, f"Workshop marked as {status}")
    return redirect("workshop_list")


# =====================================================
# TRAINERS
# =====================================================

@login_required
@user_passes_test(is_superuser)
def trainer_list(request):
    trainers = Trainer.objects.all().order_by("Name")
    paginator = Paginator(trainers, 6)
    return render(request, "trainer_list.html", {
        "trainers": paginator.get_page(request.GET.get("page"))
    })


@login_required
@user_passes_test(is_superuser)
def add_trainer(request):
    form = TrainerForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect("trainer_list")
    return render(request, "add_trainer.html", {"form": form})


@login_required
@user_passes_test(is_superuser)
def edit_trainer(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    form = TrainerForm(request.POST or None, instance=trainer)
    if form.is_valid():
        form.save()
        return redirect("trainer_list")
    return render(request, "edit_trainer.html", {"form": form})


@login_required
@user_passes_test(is_superuser)
def delete_trainer(request, pk):
    get_object_or_404(Trainer, pk=pk).delete()
    return redirect("trainer_list")


# =====================================================
# ADMIN TASK DASHBOARD
# =====================================================

@login_required
def admin_task_dashboard(request):
    today = timezone.now().date()
    one_week_ago = today - timedelta(days=7)

    tasks = TodoTask.objects.filter(
        for_date__gte=one_week_ago
    ).select_related("trainer")

    form = None

    # ✅ Only superuser can add task
    if request.user.is_superuser:
        form = TodoTaskForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            form.save()
            return redirect("admin_task_dashboard")

    return render(request, "todo/admin_dashboard.html", {
        "form": form,   # None for normal users
        "grouped_tasks": {
            "pending": tasks.filter(status="pending"),
            "in_progress": tasks.filter(status="in_progress"),
            "completed": tasks.filter(status="completed"),
        }
    })

@login_required
@user_passes_test(is_superuser)
def add_task_page(request):
    form = TodoTaskForm(request.POST or None)
    formset = SubTaskFormSet(
        request.POST or None,
        queryset=SubTask.objects.none(),
        prefix="subtasks"
    )

    if request.method == "POST" and form.is_valid() and formset.is_valid():
        task = form.save()
        for sub in formset:
            if sub.cleaned_data.get("title"):
                s = sub.save(commit=False)
                s.parent_task = task
                s.save()
        return redirect("admin_task_dashboard")

    return render(request, "todo/add_task.html", {
        "form": form,
        "subtask_formset": formset
    })


@login_required
def task_detail(request, task_id):
    task = get_object_or_404(TodoTask, id=task_id)
    subtasks = task.subtasks.all()

    total = subtasks.count()
    done = subtasks.filter(is_completed=True).count()
    task.progress = int((done / total) * 100) if total else 0

    return render(request, "todo/task_detail.html", {
        "task": task,
        "subtasks": subtasks
    })


@login_required
@user_passes_test(is_superuser)
def toggle_subtask_done(request, task_id, subtask_id):
    sub = get_object_or_404(SubTask, id=subtask_id, parent_task_id=task_id)
    sub.is_completed = not sub.is_completed
    sub.save()
    return redirect("task_detail", task_id=task_id)


@login_required
@user_passes_test(is_superuser)
def delete_task(request, task_id):
    get_object_or_404(TodoTask, id=task_id).delete()
    return redirect("task_history")

@login_required
@user_passes_test(is_superuser)
def change_task_status(request, task_id):
    task = get_object_or_404(TodoTask, id=task_id)

    if task.status == "pending":
        task.status = "in_progress"
    elif task.status == "in_progress":
        task.status = "completed"
    else:
        task.status = "pending"   # optional reset

    task.save()
    return redirect("admin_task_dashboard")

@login_required
@user_passes_test(is_superuser)
def add_subtask(request, task_id):
    task = get_object_or_404(TodoTask, id=task_id)

    if request.method == "POST":
        title = request.POST.get("title")
        if title:
            SubTask.objects.create(parent_task=task, title=title)
        return redirect("task_detail", task_id=task.id)

    return render(request, "todo/add_subtask.html", {
        "task": task
    })
@login_required
@user_passes_test(is_superuser)
def edit_subtask(request, subtask_id):

    subtask = get_object_or_404(
        SubTask,
        id=subtask_id
    )

    if request.method == "POST":

        title = request.POST.get("title")

        if title:
            subtask.title = title
            subtask.save()

            return redirect(
                "task_detail",
                task_id=subtask.parent_task.id
            )

    return render(
        request,
        "todo/edit_subtask.html",
        {
            "subtask": subtask
        }
    )
@login_required
@user_passes_test(is_superuser)
def delete_subtask(request, subtask_id):

    subtask = get_object_or_404(
        SubTask,
        id=subtask_id
    )

    task_id = subtask.parent_task.id

    subtask.delete()

    return redirect(
        "task_detail",
        task_id=task_id
    )

@login_required
@user_passes_test(is_superuser)
def edit_task(request, task_id):
    task = get_object_or_404(TodoTask, id=task_id)
    form = TodoTaskForm(request.POST or None, instance=task)

    if form.is_valid():
        form.save()
        return redirect("admin_task_dashboard")

    return render(request, "todo/edit_task.html", {
        "form": form,
        "task": task
    })


# =====================================================
# TRAINER DASHBOARD
# =====================================================

@login_required
def trainer_dashboard(request):

    trainer = Trainer.objects.filter(
        user=request.user
    ).first()

    if not trainer:
        trainer = Trainer.objects.filter(
            email=request.user.email
        ).first()

    if not trainer:
        messages.error(
            request,
            "Your account is not linked to a Trainer profile."
        )
        return redirect("dashboard")

    today = timezone.localdate()

    # Only full-time trainers get attendance record
    attendance = None

    if trainer.is_full_time:

        attendance, created = (
            DailyAttendance.objects.get_or_create(
                trainer=trainer,
                date=today
            )
        )

    # Today's tasks
    tasks = (
        TodoTask.objects
        .filter(
            trainer=trainer,
            for_date=today
        )
        .order_by("-created_on")
    )

    workshops = (
        Workshop.objects
        .filter(
            assigned_trainers=trainer
        )
        .select_related("college")
        .order_by("start_date")
    )

    return render(
        request,
        "todo/trainer_dashboard.html",
        {
            "trainer": trainer,
            "today": today,
            "attendance": attendance,
            "tasks": tasks,
            "workshops": workshops,
            "is_full_time": trainer.is_full_time,
        }
    )
@login_required
def trainer_schedule(request):

    events = CalendarEvent.objects.prefetch_related(
        "trainers"
    ).select_related(
        "college",
        "workshop"
    ).order_by(
        "date",
        "start_time"
    )

    events_json = []

    for event in events:

        trainer_names = ", ".join(
            trainer.Name
            for trainer in event.trainers.all()
        )

        start = None
        end = None

        if event.start_time:

            start = f"{event.date}T{event.start_time}"

        else:

            start = str(event.date)

        if event.end_time:

            end = f"{event.date}T{event.end_time}"

        event_color = {
            "workshop": "#198754",
            "fdp": "#dc3545",
            "online_workshop": "#20c997",
            "office": "#0d6efd",
            "guest_training": "#fd7e14",
            "meeting": "#6f42c1",
            "other": "#6c757d",
        }.get(
            event.event_type,
            "#6c757d"
        )

        events_json.append({

            "id": str(event.id),

            "title": event.title,

            "start": start,

            "end": end,

            "allDay": not bool(event.start_time),

            "backgroundColor": event_color,

            "borderColor": event_color,

            "editable": request.user.is_superuser,

            "durationEditable": request.user.is_superuser,

            "startEditable": request.user.is_superuser,

            "url": reverse(
                "edit_calendar_event",
                args=[event.id]
            ),

            "extendedProps": {

                "trainers": trainer_names,

                "event_type":
                    event.get_event_type_display(),

                "college":
                    event.college.name
                    if event.college
                    else "",

                "workshop":
                    event.workshop.title
                    if event.workshop
                    else "",

                "department":
                    event.department,

                "location":
                    event.location,

                "guest_faculty":
                    getattr(event, "guest_faculty", ""),

                "description":
                    event.description,
            }
        })

    return render(
        request,
        "trainer_schedule.html",
        {
            "events_json": json.dumps(events_json),
        }
    )

@login_required
def follow_ups(request):
    """
    View follow-ups.
    Admin can edit/delete.
    Others can only view.
    """
    today = timezone.now().date()

    followups = (
        FollowUp.objects
        .select_related("workshop", "college", "assigned_to")
        .order_by("follow_from")   # ✅ FIXED
    )

    pending = followups.filter(is_completed=False)
    completed = followups.filter(is_completed=True)

    return render(request, "followups.html", {
        "pending_followups": pending,
        "completed_followups": completed,
        "today": today,
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def add_followup(request):
    """
    Admin-only: Add a follow-up for a workshop
    """
    if request.method == "POST":
        form = FollowUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Follow-up added successfully.")
            return redirect('follow_ups')
    else:
        form = FollowUpForm()

    return render(request, 'followup_form.html', {
        'form': form,
        'title': 'Add Follow-Up'
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_followup(request, pk):
    followup = get_object_or_404(FollowUp, pk=pk)

    if request.method == "POST":
        form = FollowUpForm(request.POST, instance=followup)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Follow-up updated successfully.")
            return redirect('follow_ups')
    else:
        form = FollowUpForm(instance=followup)

    return render(request, 'followup_form.html', {
        'form': form,
        'title': 'Edit Follow-Up'
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_followup(request, pk):
    followup = get_object_or_404(FollowUp, pk=pk)
    followup.delete()
    messages.success(request, "🗑️ Follow-up deleted.")
    return redirect('follow_ups')



@login_required
def calendar_view(request):

    events = []

    # Workshops
    for w in Workshop.objects.all():

        events.append({
            "title": f"📚 {w.title}",
            "start": w.start_date.strftime("%Y-%m-%d"),
            "end": (w.end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            "color": "#198754",
            "url": reverse("workshop_detail", args=[w.pk])
        })

    # Office Trainings
    for t in OfficeTraining.objects.all():

        events.append({
            "title": f"🏢 {t.name}",
            "start": t.start_date.strftime("%Y-%m-%d"),
            "end": (t.end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            "color": "#0d6efd",
            "url": reverse("view_office_training", args=[t.pk])
        })

    return render(
        request,
        "calendar.html",
        {
            "events_json": json.dumps(events)
        }
    )

# =====================================================
# OFFICE TRAININGS
# =====================================================
@login_required
def view_office_training(request, pk):
    training = get_object_or_404(OfficeTraining, pk=pk)
    return render(request, "office_training/view.html", {
        "training": training
    })

@login_required
def office_training_list(request):
    today = timezone.now().date()

    trainings = OfficeTraining.objects.all().order_by("-start_date")

    ongoing = trainings.filter(start_date__lte=today, end_date__gte=today)
    scheduled = trainings.filter(start_date__gt=today)
    past = trainings.filter(end_date__lt=today)

    return render(request, "office_training/list.html", {
        "ongoing": ongoing,
        "scheduled": scheduled,
        "past": past,
        "calendar_trainings": trainings,
        "today": today,
        "is_admin": request.user.is_superuser,  # 🔒 only superuser edits
    })

@login_required
@user_passes_test(is_superuser)
def add_office_training(request):
    form = OfficeTrainingForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Office training added successfully.")
        return redirect("office_training_list")
    return render(request, "office_training/form.html", {
        "form": form,
        "title": "Add Office Training"
    })


@login_required
@user_passes_test(is_superuser)
def edit_office_training(request, pk):
    training = get_object_or_404(OfficeTraining, pk=pk)
    form = OfficeTrainingForm(request.POST or None, instance=training)
    if form.is_valid():
        form.save()
        messages.success(request, "Office training updated.")
        return redirect("office_training_list")
    return render(request, "office_training/form.html", {
        "form": form,
        "title": "Edit Office Training"
    })


@login_required
@user_passes_test(is_superuser)
def delete_office_training(request, pk):
    training = get_object_or_404(OfficeTraining, pk=pk)
    training.delete()
    messages.success(request, "Office training deleted.")
    return redirect("office_training_list")


# =====================================================
# TASK HISTORY (ADMIN ONLY)
# =====================================================

@login_required
@user_passes_test(is_superuser)
def task_history(request):
    """
    Shows tasks older than 7 days.
    Admin only.
    """
    today = timezone.now().date()
    one_week_ago = today - timedelta(days=7)

    tasks = TodoTask.objects.filter(
        for_date__lt=one_week_ago
    ).select_related("trainer").order_by("-for_date")

    trainers = Trainer.objects.filter(is_full_time=True).order_by("Name")

    # Filters
    trainer_id = request.GET.get("trainer")
    date_filter = request.GET.get("date")
    priority = request.GET.get("priority")

    if trainer_id:
        tasks = tasks.filter(trainer_id=trainer_id)
    if date_filter:
        tasks = tasks.filter(for_date=date_filter)
    if priority:
        tasks = tasks.filter(priority=priority)

    return render(request, "todo/task_history.html", {
        "tasks": tasks,
        "trainers": trainers,
        "query_trainer": trainer_id,
        "query_date": date_filter,
        "query_priority": priority,
    })

@login_required
def completed_workshops(request):
    workshops = Workshop.objects.filter(status='completed').order_by('-end_date')
    return render(request, 'completed_workshops.html', {
        'workshops': workshops
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def college_list(request):
    colleges = College.objects.all().order_by("name")

    return render(request, "college/list.html", {
        "colleges": colleges
    })

@login_required
@user_passes_test(is_superuser)
def add_college(request):
    form = CollegeForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "College added successfully")
        return redirect("college_list")
    return render(request, "college/form.html", {"form": form, "title": "Add College"})


@login_required
@user_passes_test(is_superuser)
def edit_college(request, pk):
    college = get_object_or_404(College, pk=pk)
    form = CollegeForm(request.POST or None, instance=college)
    if form.is_valid():
        form.save()
        messages.success(request, "College updated successfully")
        return redirect("college_list")
    return render(request, "college/form.html", {"form": form, "title": "Edit College"})


@login_required
@user_passes_test(is_superuser)
def delete_college(request, pk):
    college = get_object_or_404(College, pk=pk)
    college.delete()
    messages.success(request, "College deleted")
    return redirect("college_list")


@login_required
def add_workshop_remark(request, workshop_id):

    workshop = get_object_or_404(
        Workshop,
        id=workshop_id
    )

    trainer = Trainer.objects.filter(
        user=request.user
    ).first()

    if not trainer:
        messages.error(
            request,
            "Your account is not linked to a Trainer profile."
        )

        return redirect(
            "workshop_detail",
            pk=workshop.id
        )

    if request.method == "POST":

        form = WorkshopRemarksForm(
            request.POST
        )

        if form.is_valid():

            remark = form.save(
                commit=False
            )

            remark.workshop = workshop
            remark.trainer = trainer

            remark.save()

            messages.success(
                request,
                "Workshop remark submitted successfully."
            )

            return redirect(
                "workshop_detail",
                pk=workshop.id
            )

    else:

        form = WorkshopRemarksForm()

    return render(
        request,
        "add_workshop_remark.html",
        {
            "workshop": workshop,
            "form": form
        }
    )


@login_required
def edit_workshop_remark(request, remark_id):

    remark = get_object_or_404(
        WorkshopRemarks,
        id=remark_id
    )

    trainer = Trainer.objects.filter(
        user=request.user
    ).first()

    # Superuser can edit any remark
    if not request.user.is_superuser:

        if not trainer:
            messages.error(
                request,
                "Trainer profile not found."
            )
            return redirect(
                "workshop_detail",
                pk=remark.workshop.id
            )

        # Trainer can edit only their own remark
        if remark.trainer != trainer:
            messages.error(
                request,
                "You can edit only your own remarks."
            )
            return redirect(
                "workshop_detail",
                pk=remark.workshop.id
            )

    if request.method == "POST":

        form = WorkshopRemarksForm(
            request.POST,
            instance=remark
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Remark updated successfully."
            )

            return redirect(
                "workshop_detail",
                pk=remark.workshop.id
            )

    else:

        form = WorkshopRemarksForm(
            instance=remark
        )

    return render(
        request,
        "add_workshop_remark.html",
        {
            "form": form,
            "workshop": remark.workshop,
            "is_edit": True,
        }
    )

@login_required
def meeting_notes(request):

    notes = MeetingNote.objects.all().order_by(
        "-meeting_date"
    )

    q = request.GET.get("q")

    date_filter = request.GET.get("date")

    if q:
        notes = notes.filter(
            title__icontains=q
        )

    if date_filter:
        notes = notes.filter(
            meeting_date=date_filter
        )

    return render(
        request,
        "meeting_notes/list.html",
        {
            "notes": notes
        }
    )

@login_required
def add_meeting_note(request):

    form = MeetingNoteForm(
        request.POST or None,
        request.FILES or None
    )

    if form.is_valid():

        note = form.save(
            commit=False
        )

        note.created_by = request.user

        note.save()

        form.save_m2m()

        return redirect(
            "meeting_notes"
        )

    return render(
        request,
        "meeting_notes/form.html",
        {
            "form": form
        }
    )


@login_required
def edit_meeting_note(
    request,
    pk
):

    note = get_object_or_404(
        MeetingNote,
        pk=pk
    )

    form = MeetingNoteForm(
        request.POST or None,
        request.FILES or None,
        instance=note
    )

    if form.is_valid():
        form.save()
        return redirect(
            "meeting_notes"
        )

    return render(
        request,
        "meeting_notes/form.html",
        {
            "form": form
        }
    )

@login_required
@user_passes_test(is_superuser)
def delete_meeting_note(
    request,
    pk
):

    note = get_object_or_404(
        MeetingNote,
        pk=pk
    )

    note.delete()

    return redirect(
        "meeting_notes"
    )
def custom_404(request, exception):
    return render(request, "404.html", status=404)


@login_required
@user_passes_test(is_superuser)
def add_calendar_event(request):

    selected_date = request.GET.get("date")
    selected_time = request.GET.get("time")

    if request.method == "POST":

        form = CalendarEventForm(request.POST)

        if form.is_valid():

            event = form.save(commit=False)

            event.created_by = request.user

            event.save()

            form.save_m2m()

            messages.success(
                request,
                "Calendar event added successfully."
            )

            return redirect(
                "trainer_schedule"
            )

    else:

        initial = {}

        if selected_date:
            initial["date"] = selected_date

        if selected_time:
            initial["start_time"] = selected_time

        form = CalendarEventForm(
            initial=initial
        )

    return render(
        request,
        "calendar/add_event.html",
        {
            "form": form,
            "title": "Add Calendar Event",
        }
    )
@login_required
@user_passes_test(is_superuser)
def edit_calendar_event(request, pk):

    event = get_object_or_404(
        CalendarEvent,
        pk=pk
    )

    if request.method == "POST":

        form = CalendarEventForm(
            request.POST,
            instance=event
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Calendar event updated successfully."
            )

            return redirect(
                "trainer_schedule"
            )

    else:

        form = CalendarEventForm(
            instance=event
        )

    return render(
        request,
        "calendar/add_event.html",
        {
            "form": form,
            "event": event,
            "title": "Edit Calendar Event",
        }
    )
@login_required
@user_passes_test(is_superuser)
def delete_calendar_event(request, pk):

    event = get_object_or_404(
        CalendarEvent,
        pk=pk
    )

    event.delete()

    messages.success(
        request,
        "Calendar event deleted."
    )

    return redirect("trainer_schedule")

@login_required
@user_passes_test(is_superuser)
def duplicate_calendar_event(request, pk):

    event = get_object_or_404(
        CalendarEvent,
        pk=pk
    )

    new_date = request.GET.get("date")

    if new_date:

        try:
            new_date = date.fromisoformat(
                new_date
            )

        except ValueError:

            messages.error(
                request,
                "Invalid date."
            )

            return redirect(
                "trainer_schedule"
            )

    else:

        new_date = event.date + timedelta(
            days=1
        )

    new_event = CalendarEvent.objects.create(

        title=event.title,

        date=new_date,

        start_time=event.start_time,

        end_time=event.end_time,

        workshop=event.workshop,

        college=event.college,

        department=event.department,

        event_type=event.event_type,

        guest_faculty=getattr(event, "guest_faculty", ""),

        location=event.location,

        description=event.description,

        created_by=request.user,
    )

    new_event.trainers.set(
        event.trainers.all()
    )

    messages.success(
        request,
        f"Event duplicated to {new_date}."
    )

    return redirect(
        "trainer_schedule"
    )

@login_required
@user_passes_test(is_superuser)
def duplicate_calendar_event_next_day(request, pk):

    event = get_object_or_404(
        CalendarEvent,
        pk=pk
    )

    new_event = CalendarEvent.objects.create(

        title=event.title,

        date=event.date + timedelta(days=1),

        start_time=event.start_time,

        end_time=event.end_time,

        workshop=event.workshop,

        college=event.college,

        department=event.department,

        event_type=event.event_type,

        guest_faculty=getattr(event, "guest_faculty", ""),

        location=event.location,

        description=event.description,

        created_by=request.user,
    )

    new_event.trainers.set(
        event.trainers.all()
    )

    return redirect(
        "trainer_schedule"
    )

@login_required
@user_passes_test(is_superuser)
def duplicate_calendar_event_next_week(request, pk):

    event = get_object_or_404(
        CalendarEvent,
        pk=pk
    )

    new_event = CalendarEvent.objects.create(

        title=event.title,

        date=event.date + timedelta(days=7),

        start_time=event.start_time,

        end_time=event.end_time,

        workshop=event.workshop,

        college=event.college,

        department=event.department,

        event_type=event.event_type,

        guest_faculty=getattr(event, "guest_faculty", ""),

        location=event.location,

        description=event.description,

        created_by=request.user,
    )

    new_event.trainers.set(
        event.trainers.all()
    )

    return redirect(
        "trainer_schedule"
    )

@login_required
@user_passes_test(is_superuser)
@require_POST
def move_calendar_event(request, pk):

    event = get_object_or_404(
        CalendarEvent,
        pk=pk
    )

    try:

        data = json.loads(
            request.body
        )

        new_date = data.get("date")

        if not new_date:

            return JsonResponse(
                {
                    "success": False,
                    "error": "Date is required."
                },
                status=400
            )

        event.date = date.fromisoformat(
            new_date
        )

        event.save()

        return JsonResponse(
            {
                "success": True
            }
        )

    except Exception as e:

        return JsonResponse(
            {
                "success": False,
                "error": str(e)
            },
            status=400
        )


@login_required
@user_passes_test(is_superuser)
@require_POST
def resize_calendar_event(request, pk):

    event = get_object_or_404(
        CalendarEvent,
        pk=pk
    )

    try:

        data = json.loads(
            request.body
        )

        start = data.get("start")
        end = data.get("end")

        if start:
            event.start_time = start

        if end:
            event.end_time = end

        event.save()

        return JsonResponse(
            {
                "success": True
            }
        )

    except Exception as e:

        return JsonResponse(
            {
                "success": False,
                "error": str(e)
            },
            status=400
        )


@login_required
def daily_checkin(request):

    trainer = Trainer.objects.filter(
        user=request.user
    ).first()

    if not trainer:
        trainer = Trainer.objects.filter(
            email=request.user.email
        ).first()

    if not trainer:
        messages.error(
            request,
            "Your account is not linked to a Trainer profile."
        )
        return redirect("dashboard")

    # =====================================================
    # ONLY FULL-TIME TRAINERS CAN CHECK IN
    # =====================================================

    if not trainer.is_full_time:
        messages.error(
            request,
            "Only full-time trainers are allowed to check in."
        )
        return redirect("trainer_dashboard")

    today = timezone.localdate()

    attendance, created = DailyAttendance.objects.get_or_create(
        trainer=trainer,
        date=today
    )

    if request.method == "POST":

        action = request.POST.get("action")

        # =================================================
        # CHECK IN
        # =================================================

        if action == "check_in":

            if not attendance.check_in:

                attendance.check_in = timezone.now()
                attendance.check_out = None
                attendance.save()

                messages.success(
                    request,
                    "You have successfully checked in."
                )

        # =================================================
        # CHECK OUT
        # =================================================

        elif action == "check_out":

            if (
                attendance.check_in
                and not attendance.check_out
            ):

                attendance.check_out = timezone.now()
                attendance.save()

                messages.success(
                    request,
                    "You have successfully checked out."
                )

    return redirect("trainer_dashboard")
@login_required
def add_today_task(request):

    trainer = Trainer.objects.filter(
        user=request.user
    ).first()

    if not trainer:
        trainer = Trainer.objects.filter(
            email=request.user.email
        ).first()

    if not trainer:
        messages.error(
            request,
            "Your account is not linked to a Trainer profile."
        )
        return redirect("dashboard")

    # =====================================================
    # ONLY FULL-TIME TRAINERS
    # =====================================================

    if not trainer.is_full_time:
        messages.error(
            request,
            "Only full-time trainers can add daily work updates."
        )
        return redirect("trainer_dashboard")

    today = timezone.localdate()

    attendance = DailyAttendance.objects.filter(
        trainer=trainer,
        date=today
    ).first()

    # =====================================================
    # MUST CHECK IN FIRST
    # =====================================================

    if not attendance or not attendance.check_in:

        messages.error(
            request,
            "Please check in before adding today's work."
        )

        return redirect("trainer_dashboard")

    # =====================================================
    # CANNOT ADD AFTER CHECKOUT
    # =====================================================

    if attendance.check_out:

        messages.error(
            request,
            "You have already checked out for today."
        )

        return redirect("trainer_dashboard")

    if request.method == "POST":

        task_text = request.POST.get(
            "task",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        if not task_text:

            messages.error(
                request,
                "Please enter what you are working on."
            )

            return redirect("trainer_dashboard")

        TodoTask.objects.create(
            trainer=trainer,
            task=task_text,
            description=description,
            for_date=today,
            status="in_progress",
            priority="medium",
            estimated_hours=1.0,
            is_done=False,
        )

        messages.success(
            request,
            "Today's work was added successfully."
        )

    return redirect("trainer_dashboard")
@login_required

@login_required
def checkin_portal(request):
    trainers = (
        Trainer.objects
        .filter(is_full_time=True)
        .order_by("Name")
    )

    today = timezone.localdate()

    attendance_records = (
        DailyAttendance.objects
        .filter(
            date=today,
            trainer__is_full_time=True
        )
        .select_related("trainer")
        .order_by("trainer__Name")
    )

    attendance_map = {
        attendance.trainer_id: attendance
        for attendance in attendance_records
    }

    trainer_list = []

    for trainer in trainers:
        trainer_list.append({
            "trainer": trainer,
            "attendance": attendance_map.get(trainer.id),
        })

    return render(
        request,
        "checkin_portal.html",
        {
            "trainer_list": trainer_list,
            "today": today,
        }
    )


# =====================================================
# WEEKLY WORK SCHEDULE
# =====================================================

@login_required
def weekly_schedule(request):

    today = timezone.localdate()

    week_param = request.GET.get("week")

    if week_param:
        try:
            selected_date = date.fromisoformat(week_param)
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    week_start = (
        selected_date -
        timedelta(days=selected_date.weekday())
    )

    week_days = [
        week_start + timedelta(days=i)
        for i in range(7)
    ]

    week_end = week_days[-1]

    events = (
        CalendarEvent.objects
        .filter(
            date__gte=week_start,
            date__lte=week_end
        )
        .select_related(
            "college",
            "workshop"
        )
        .prefetch_related(
            "trainers"
        )
        .order_by(
            "date",
            "start_time"
        )
    )

    schedule = []

    for day in week_days:

        day_events = []

        for event in events:

            if event.date != day:
                continue

            trainer_names = ", ".join(
                trainer.Name
                for trainer in event.trainers.all()
            )

            day_events.append({
                "id": event.id,
                "title": event.title,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "event_type": event.get_event_type_display(),
                "trainers": trainer_names,
                "college": (
                    event.college.name
                    if event.college
                    else ""
                ),
                "department": event.department,
                "location": event.location,
                "description": event.description,
                "guest_faculty": getattr(
                    event,
                    "guest_faculty",
                    ""
                ),
                "workshop": (
                    event.workshop.title
                    if event.workshop
                    else ""
                ),
            })

        schedule.append({
            "date": day,
            "events": day_events,
        })

    previous_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    return render(
        request,
        "calendar/weekly_schedule.html",
        {
            "week_days": week_days,
            "schedule": schedule,
            "week_start": week_start,
            "week_end": week_end,
            "previous_week": previous_week,
            "next_week": next_week,
            "today": today,
        }
    )
