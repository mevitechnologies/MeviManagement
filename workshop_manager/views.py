from datetime import date, timedelta
from decimal import Decimal
import json
from decimal import Decimal
from django.db.models import Count, Q, Sum
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
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
    DailyLearning,
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
    DailyLearningForm,
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


# =====================================================
# MAIN DASHBOARD
# =====================================================

@login_required
def dashboard(request):

    today = timezone.localdate()

    # =====================================================
    # GREETINGS
    # =====================================================

    greetings = {
        "morning": [
            (
                "Good Morning, Mevi Family! 🌻",
                "Nenne enaythu anta worry beda… ivattu namma fresh start. "
                "Ondu small step, ondu good thought, ondu happy smile — "
                "let's make today meaningful. ❤️"
            ),
            (
                "Namaskara, Team Mevi! ☀️",
                "Coffee ready aa? 😄 "
                "Let's learn something, finish something, help someone "
                "and make the day count."
            ),
            (
                "Good Morning, Wonderful People! 🌱",
                "Perfect day bekagilla… swalpa progress saaku. "
                "Let's move forward together."
            ),
            (
                "Good Morning, Mevi Family! 💜",
                "Every new day gives us one more chance to learn, improve "
                "and make someone's journey a little easier."
            ),
            (
                "Namaskara! A New Day, A New Beginning. 🌸",
                "Namma work just tasks alla — every small effort "
                "contributes to something bigger."
            ),
        ],

        "afternoon": [
            (
                "Good Afternoon, Mevi Family! ☀️",
                "Half day done! 😄 "
                "Swalpa energy recharge madi, let's finish the day strong."
            ),
            (
                "Hello Team Mevi! 🌻",
                "Ivattu perfect agirbeku anta illa. "
                "Just keep moving, keep helping and keep learning."
            ),
            (
                "Good Afternoon, Wonderful Team! 💜",
                "One task completed, one student helped, one problem solved — "
                "small wins become big journeys."
            ),
            (
                "Namaskara Mevi Family! 🌱",
                "Work pressure irbahudu… but together handle madidre "
                "everything becomes a little lighter. 🤝"
            ),
        ],

        "evening": [
            (
                "Good Evening, Mevi Family! 🌙",
                "Before the day ends, remember — "
                "today's small efforts may become tomorrow's big achievements."
            ),
            (
                "Hello Team! 🌸",
                "Ivattu enu complete madidru, be proud of the progress. "
                "Tomorrow is another beautiful opportunity."
            ),
            (
                "Good Evening, Wonderful People! 💜",
                "Work is important, but the people we work with make "
                "the journey special. Thank you for being a team."
            ),
        ],
    }

    hour = timezone.localtime().hour

    if hour < 12:
        greeting_period = "morning"
        greeting_icon = "🌅"

    elif hour < 17:
        greeting_period = "afternoon"
        greeting_icon = "☀️"

    else:
        greeting_period = "evening"
        greeting_icon = "🌙"

    greeting_index = today.toordinal() % len(
        greetings[greeting_period]
    )

    greeting, greeting_message = greetings[
        greeting_period
    ][greeting_index]

    # =====================================================
    # THOUGHT OF THE DAY
    # =====================================================

    DAILY_THOUGHTS = [

        (
            "A great trainer doesn't just teach a skill — "
            "they inspire someone to believe they can master it."
        ),

        (
            "Knowledge becomes powerful when it is shared."
        ),

        (
            "The best trainers never stop being learners."
        ),

        (
            "Every learner you teach today carries a possibility "
            "you may never fully see. Teach with purpose."
        ),

        (
            "Teaching is not about having all the answers. "
            "It is about creating an environment where people "
            "love discovering them."
        ),

        (
            "Learn something new. Teach something useful. "
            "Inspire someone. Repeat."
        ),

        (
            "One hour of teaching can create an impact "
            "that lasts for years."
        ),

        (
            "Your passion for learning can become "
            "someone else's motivation to grow."
        ),

        (
            "Don't just complete a training session. "
            "Create a learning experience."
        ),

        (
            "Every question from a student is an opportunity "
            "to make your teaching better."
        ),

        (
            "Great teaching begins with curiosity "
            "and grows through patience."
        ),

        (
            "Train minds. Build skills. Create confidence."
        ),

        (
            "The goal isn't simply to finish the syllabus. "
            "The goal is to create understanding."
        ),

        (
            "Keep learning, keep teaching, keep improving."
        ),

        (
            "Behind every skilled professional is someone "
            "who once took the time to teach them."
        ),

        (
            "Ondu dina perfect agiralla. "
            "But every day has something beautiful to teach us."
        ),

        (
            "Swalpa swalpa progress kooda progress ne. "
            "Never underestimate small steps."
        ),

        (
            "Namma journey nammade. "
            "Compare beda. Just keep growing."
        ),

        (
            "Someone may remember your lesson, "
            "but they will definitely remember how you made them feel."
        ),

        (
            "Ondu helping hand, ondu kind word, "
            "ondu little appreciation — it can change someone's day."
        ),

    ]

    daily_thought = DAILY_THOUGHTS[
        today.toordinal() % len(DAILY_THOUGHTS)
    ]

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
    # =====================================================

    full_time_trainers = (
        Trainer.objects
        .filter(is_full_time=True)
        .select_related("user")
        .order_by("Name")
    )

    full_time_trainer_count = full_time_trainers.count()

    # =====================================================
    # TODAY ATTENDANCE
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

    checked_out_count = sum(
        1
        for attendance in attendance_records
        if (
            attendance.check_in
            and attendance.check_out
        )
    )

    not_checked_in_count = max(
        full_time_trainer_count - checked_in_count,
        0
    )

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
    # WITH ACTIVITY COUNT
    # =====================================================

    trainer_status = []

    for trainer in full_time_trainers:

        attendance = attendance_map.get(
            trainer.id
        )

        trainer_tasks = today_tasks.filter(
            trainer=trainer
        )

        activity_count = trainer_tasks.count()

        completed_activity_count = trainer_tasks.filter(
            status="completed"
        ).count()

        working_activity_count = trainer_tasks.exclude(
            status="completed"
        ).count()

        latest_task = trainer_tasks.first()

        if attendance and attendance.check_out:
            status = "checked_out"

        elif attendance and attendance.check_in:
            status = "working"

        else:
            status = "not_checked_in"

        trainer_status.append({

            "trainer": trainer,

            "attendance": attendance,

            "status": status,

            "activity_count":
                activity_count,

            "completed_activity_count":
                completed_activity_count,

            "working_activity_count":
                working_activity_count,

            "latest_task":
                latest_task,

            "tasks":
                trainer_tasks,

        })

    # =====================================================
    # UPCOMING WORKSHOPS
    # =====================================================

    upcoming_workshops = (
        Workshop.objects
        .filter(
            start_date__gte=today
        )
        .exclude(
            status="cancelled"
        )
        .select_related("college")
        .prefetch_related("assigned_trainers")
        .order_by("start_date")[:6]
    )

    # =====================================================
    # UPCOMING 7 DAYS
    # =====================================================

    next_seven_days = today + timedelta(days=7)

    upcoming_schedule = []

    # -----------------------------------------------------
    # WORKSHOPS
    # -----------------------------------------------------

    upcoming_workshops_schedule = (
        Workshop.objects
        .filter(
            start_date__lte=next_seven_days,
            end_date__gte=today
        )
        .exclude(status="cancelled")
        .select_related("college")
        .prefetch_related("assigned_trainers")
        .order_by(
            "start_date",
            "title"
        )
    )

    for workshop in upcoming_workshops_schedule:

        trainer_names = ", ".join(
            trainer.Name
            for trainer
            in workshop.assigned_trainers.all()
        )

        upcoming_schedule.append({

            "date":
                workshop.start_date,

            "end_date":
                workshop.end_date,

            "title":
                workshop.title,

            "type":
                "Workshop",

            "college":
                workshop.college.name
                if workshop.college
                else "—",

            "trainer":
                trainer_names
                if trainer_names
                else "—",

            "time":
                "As scheduled",

            "location":
                workshop.college.name
                if workshop.college
                else "—",

            "status":
                workshop.get_status_display(),

        })

    # -----------------------------------------------------
    # CALENDAR EVENTS
    # -----------------------------------------------------

    calendar_schedule_events = (
        CalendarEvent.objects
        .filter(
            date__gte=today,
            date__lte=next_seven_days
        )
        .exclude(
            event_type="workshop",
            workshop__isnull=False
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

    for event in calendar_schedule_events:

        trainer_names = ", ".join(
            trainer.Name
            for trainer in event.trainers.all()
        )

        if event.start_time and event.end_time:

            time_text = (
                f"{event.start_time.strftime('%I:%M %p')}"
                f" – "
                f"{event.end_time.strftime('%I:%M %p')}"
            )

        elif event.start_time:

            time_text = event.start_time.strftime(
                "%I:%M %p"
            )

        else:

            time_text = "—"

        upcoming_schedule.append({

            "date":
                event.date,

            "end_date":
                event.date,

            "title":
                event.title,

            "type":
                event.get_event_type_display(),

            "college":
                event.college.name
                if event.college
                else "—",

            "trainer":
                trainer_names
                if trainer_names
                else "—",

            "time":
                time_text,

            "location":
                event.location
                if event.location
                else "—",

            "status":
                "Scheduled",

        })

    upcoming_schedule.sort(
        key=lambda item: (
            item["date"],
            item["title"].lower()
        )
    )

    # =====================================================
    # NEEDS ATTENTION
    # =====================================================

    pending_workshops_count = (
        Workshop.objects
        .filter(
            start_date__gte=today
        )
        .filter(
            status="tentative"
        )
        .count()
    )

    pending_reports_count = (
        Workshop.objects
        .filter(
            end_date__lt=today
        )
        .exclude(
            status__in=[
                "completed",
                "cancelled"
            ]
        )
        .count()
    )

    # =====================================================
    # CALENDAR EVENTS FOR MASTER CALENDAR
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
            for trainer
            in workshop.assigned_trainers.all()
        )

        events.append({

            "id":
                f"workshop-{workshop.pk}",

            "title":
                f"📚 {workshop.title}",

            "start":
                workshop.start_date.strftime(
                    "%Y-%m-%d"
                )
                if workshop.start_date
                else None,

            "end":
                (
                    workshop.end_date +
                    timedelta(days=1)
                ).strftime("%Y-%m-%d")
                if workshop.end_date
                else None,

            "color":
                "#5B4BDB",

            "url":
                reverse(
                    "workshop_detail",
                    args=[workshop.pk]
                ),

            "extendedProps": {

                "trainer":
                    trainer_names,

                "college":
                    workshop.college.name
                    if workshop.college
                    else "",

                "department":
                    workshop.departments or "",

                "event_type":
                    "Workshop",

                "status":
                    workshop.get_status_display(),

                "description":
                    workshop.remarks or "",

            }
        })

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
            for trainer
            in training.trainers.all()
        )

        events.append({

            "id":
                f"office-{training.pk}",

            "title":
                f"🏢 {training.name}",

            "start":
                training.start_date.strftime(
                    "%Y-%m-%d"
                )
                if training.start_date
                else None,

            "end":
                (
                    training.end_date +
                    timedelta(days=1)
                ).strftime("%Y-%m-%d")
                if training.end_date
                else None,

            "color":
                "#2563EB",

            "url":
                reverse(
                    "view_office_training",
                    args=[training.pk]
                ),

            "extendedProps": {

                "trainer":
                    trainer_names,

                "college":
                    "Mevi Technologies",

                "department":
                    "",

                "event_type":
                    "Office Training",

                "status":
                    "Scheduled",

                "description":
                    (
                        f"Batch: {training.batch_id}"
                        if training.batch_id
                        else ""
                    ),

            }
        })

    # -----------------------------------------------------
    # CALENDAR EVENTS
    # -----------------------------------------------------

    calendar_events = (
        CalendarEvent.objects
        .select_related(
            "college",
            "workshop"
        )
        .prefetch_related(
            "trainers"
        )
        .all()
    )

    event_colors = {

        "workshop":
            "#5B4BDB",

        "fdp":
            "#EC4899",

        "online_workshop":
            "#2563EB",

        "office":
            "#16A34A",

        "guest_training":
            "#F59E0B",

        "meeting":
            "#7C3AED",

        "other":
            "#64748B",

    }

    for event in calendar_events:

        trainer_names = ", ".join(
            trainer.Name
            for trainer
            in event.trainers.all()
        )

        start = str(event.date)

        end = None

        if event.start_time:

            start = (
                f"{event.date}T"
                f"{event.start_time}"
            )

        if event.end_time:

            end = (
                f"{event.date}T"
                f"{event.end_time}"
            )

        event_type_key = (
            event.event_type
            if event.event_type
            else "other"
        )

        events.append({

            "id":
                f"event-{event.pk}",

            "title":
                event.title,

            "start":
                start,

            "end":
                end,

            "allDay":
                not bool(event.start_time),

            "color":
                event_colors.get(
                    event_type_key,
                    "#64748B"
                ),

            "borderColor":
                event_colors.get(
                    event_type_key,
                    "#64748B"
                ),

            "url":
                reverse(
                    "edit_calendar_event",
                    args=[event.pk]
                )
                if request.user.is_superuser
                else None,

            "extendedProps": {

                "trainer":
                    trainer_names,

                "college":
                    event.college.name
                    if event.college
                    else "",

                "department":
                    event.department or "",

                "event_type":
                    event.get_event_type_display(),

                "status":
                    "Scheduled",

                "location":
                    event.location or "",

                "guest_faculty":
                    getattr(
                        event,
                        "guest_faculty",
                        ""
                    ),

                "description":
                    event.description or "",

            }
        })

    # =====================================================
    # RENDER
    # =====================================================

    return render(
        request,
        "dashboard.html",
        {

            "today":
                today,

            "greeting":
                greeting,

            "greeting_message":
                greeting_message,

            "greeting_icon":
                greeting_icon,

            "daily_thought":
                daily_thought,

            # Trainers
            "trainers":
                trainers,

            "total_trainers":
                total_trainers,

            "full_time_trainer_count":
                full_time_trainer_count,

            # Attendance
            "trainer_status":
                trainer_status,

            "checked_in_count":
                checked_in_count,

            "working_count":
                working_count,

            "checked_out_count":
                checked_out_count,

            "not_checked_in_count":
                not_checked_in_count,

            # Work
            "today_tasks":
                today_tasks,

            # Workshops
            "upcoming_workshops":
                upcoming_workshops,

            "upcoming_schedule":
                upcoming_schedule,

            # Attention
            "pending_workshops_count":
                pending_workshops_count,

            "pending_reports_count":
                pending_reports_count,

            # Calendar
            "events_json":
                json.dumps(
                    events,
                    default=str
                ),

        }
    )
# =====================================================
# WORKSHOPS
# =====================================================
@login_required
def delete_workshop(request, pk):

    workshop = get_object_or_404(
        Workshop,
        pk=pk
    )

    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(
            request,
            "You do not have permission to delete workshops."
        )
        return redirect("workshop_list")

    if request.method == "POST":

        title = workshop.title

        workshop.delete()

        messages.success(
            request,
            f'Workshop "{title}" was deleted successfully.'
        )

        return redirect("workshop_list")

    return render(
        request,
        "workshop/delete_workshop.html",
        {
            "workshop": workshop
        }
    )
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

    trainer = get_object_or_404(
        Trainer,
        pk=pk
    )

    form = TrainerForm(
        request.POST or None,
        request.FILES or None,
        instance=trainer
    )

    if form.is_valid():

        form.save()

        messages.success(
            request,
            "Trainer profile updated successfully."
        )

        return redirect("trainer_list")

    return render(
        request,
        "edit_trainer.html",
        {
            "form": form,
            "trainer": trainer,
        }
    )


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


# =====================================================
# ADD TASK / ADD WORK
# =====================================================


@login_required
def add_task_page(request):

    if request.method == "POST":

        form = TodoTaskForm(
            request.POST,
            trainer=request.user.trainer
            if hasattr(request.user, "trainer")
            else None
        )

        subtask_formset = SubTaskFormSet(
            request.POST,
            prefix="subtasks"
        )

        if form.is_valid() and subtask_formset.is_valid():

            task = form.save(commit=False)

            # -------------------------------------------------
            # TRAINER
            # -------------------------------------------------

            if not request.user.is_superuser:

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

                task.trainer = trainer

            # -------------------------------------------------
            # DEFAULT STATUS
            # -------------------------------------------------

            task.status = "pending"
            task.is_done = False

            task.save()

            # -------------------------------------------------
            # SUBTASKS
            # -------------------------------------------------

            subtask_formset.instance = task
            subtask_formset.save()

            messages.success(
                request,
                "Work added successfully."
            )

            return redirect("trainer_dashboard")

    else:

        # -------------------------------------------------
        # DEFAULT TRAINER
        # -------------------------------------------------

        initial = {}

        if not request.user.is_superuser:

            trainer = Trainer.objects.filter(
                user=request.user
            ).first()

            if not trainer:
                trainer = Trainer.objects.filter(
                    email=request.user.email
                ).first()

            if trainer:
                initial["trainer"] = trainer

        form = TodoTaskForm(
            initial=initial
        )

        subtask_formset = SubTaskFormSet(
            queryset=SubTask.objects.none(),
            prefix="subtasks"
        )

    return render(
        request,
        "todo/add_task.html",
        {
            "form": form,
            "subtask_formset": subtask_formset,
        }
    )
# ============================================================
# TASK DETAIL
# ============================================================

@login_required
def task_detail(request, task_id):

    task = get_object_or_404(
        TodoTask.objects.select_related("trainer"),
        id=task_id
    )

    # ============================================================
    # PERMISSION
    # ============================================================

    if not request.user.is_superuser:

        trainer = Trainer.objects.filter(
            user=request.user
        ).first()

        if not trainer:

            trainer = Trainer.objects.filter(
                email__iexact=request.user.email
            ).first()

        if not trainer:

            messages.error(
                request,
                "Your account is not linked to a Trainer profile."
            )

            return redirect("dashboard")

        if task.trainer_id != trainer.id:

            messages.error(
                request,
                "You can view only your own work."
            )

            return redirect("trainer_dashboard")

    # ============================================================
    # SUBTASKS
    # ============================================================

    subtasks = task.subtasks.all()

    total = subtasks.count()

    done = subtasks.filter(
        is_completed=True
    ).count()

    progress = (
        int((done / total) * 100)
        if total
        else 0
    )

    # ============================================================
    # RENDER
    # ============================================================

    return render(
        request,
        "todo/task_detail.html",
        {
            "task": task,
            "subtasks": subtasks,
            "total_subtasks": total,
            "completed_subtasks": done,
            "progress": progress,
        }
    )
# ============================================================
# TOGGLE SUBTASK
# ============================================================

@login_required
@require_POST
def toggle_subtask_done(
    request,
    task_id,
    subtask_id
):

    # ============================================================
    # GET SUBTASK
    # ============================================================

    subtask = get_object_or_404(
        SubTask,
        id=subtask_id,
        parent_task_id=task_id
    )

    task = subtask.parent_task

    # ============================================================
    # FIND TRAINER
    # ============================================================

    trainer = Trainer.objects.filter(
        user=request.user
    ).first()

    if not trainer:

        trainer = Trainer.objects.filter(
            email__iexact=request.user.email
        ).first()

    # ============================================================
    # PERMISSION
    # ============================================================

    if not request.user.is_superuser:

        if not trainer:

            messages.error(
                request,
                "Trainer profile not found."
            )

            return redirect("dashboard")

        if task.trainer_id != trainer.id:

            messages.error(
                request,
                "You can update only your own work."
            )

            return redirect("trainer_dashboard")

    # ============================================================
    # TOGGLE SUBTASK
    # ============================================================

    subtask.is_completed = not subtask.is_completed

    subtask.save(
        update_fields=[
            "is_completed"
        ]
    )

    # ============================================================
    # CALCULATE SUBTASK PROGRESS
    # ============================================================

    total_subtasks = task.subtasks.count()

    completed_subtasks = (
        task.subtasks
        .filter(is_completed=True)
        .count()
    )

    # ============================================================
    # AUTOMATICALLY UPDATE PARENT TASK
    # ============================================================

    if (
        total_subtasks > 0
        and completed_subtasks == total_subtasks
    ):

        # ALL SUBTASKS COMPLETED
        task.status = "completed"
        task.is_done = True

    elif completed_subtasks > 0:

        # SOME SUBTASKS COMPLETED
        task.status = "in_progress"
        task.is_done = False

    else:

        # NO SUBTASKS COMPLETED
        task.status = "pending"
        task.is_done = False

    task.save(
        update_fields=[
            "status",
            "is_done"
        ]
    )

    # ============================================================
    # RETURN
    # ============================================================

    return redirect(
        "task_detail",
        task_id=task.id
    )


@login_required
@user_passes_test(is_superuser)
def delete_task(request, task_id):
    get_object_or_404(TodoTask, id=task_id).delete()
    return redirect("task_history")


# ============================================================
# CHANGE TASK STATUS
# ============================================================

@login_required
@require_POST
def change_task_status(request, task_id):

    # ============================================================
    # GET TASK
    # ============================================================

    task = get_object_or_404(
        TodoTask,
        id=task_id
    )

    # ============================================================
    # FIND TRAINER
    # ============================================================

    trainer = Trainer.objects.filter(
        user=request.user
    ).first()

    if not trainer:
        trainer = Trainer.objects.filter(
            email__iexact=request.user.email
        ).first()

    # ============================================================
    # TRAINER PROFILE CHECK
    # ============================================================

    if not trainer and not request.user.is_superuser:

        messages.error(
            request,
            "Your account is not linked to a Trainer profile."
        )

        return redirect("dashboard")

    # ============================================================
    # PERMISSION
    # ============================================================

    if not request.user.is_superuser:

        if task.trainer_id != trainer.id:

            messages.error(
                request,
                "You can update only your own work."
            )

            return redirect("trainer_dashboard")

    # ============================================================
    # GET NEW STATUS
    # ============================================================

    new_status = request.POST.get("status")

    # ============================================================
    # VALID STATUS
    # ============================================================

    allowed_statuses = [
        "pending",
        "in_progress",
        "completed",
    ]

    if new_status not in allowed_statuses:

        messages.error(
            request,
            "Invalid task status."
        )

        if request.user.is_superuser:
            return redirect("admin_task_dashboard")

        return redirect("trainer_dashboard")

    # ============================================================
    # UPDATE TASK
    # ============================================================

    task.status = new_status

    task.is_done = (
        new_status == "completed"
    )

    task.save(
        update_fields=[
            "status",
            "is_done",
        ]
    )

    # ============================================================
    # SUCCESS MESSAGE
    # ============================================================

    if new_status == "completed":

        messages.success(
            request,
            f'"{task.task}" marked as completed.'
        )

    elif new_status == "in_progress":

        messages.success(
            request,
            f'"{task.task}" moved to In Progress.'
        )

    else:

        messages.success(
            request,
            f'"{task.task}" moved to Pending.'
        )

    # ============================================================
    # REDIRECT
    # ============================================================

    if request.user.is_superuser:

        return redirect(
            "admin_task_dashboard"
        )

    return redirect(
        "trainer_dashboard"
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

# =====================================================
# TRAINER DASHBOARD
# =====================================================

# =====================================================
# TRAINER DASHBOARD
# =====================================================

# =====================================================
# TRAINER DASHBOARD
# =====================================================

@login_required
def trainer_dashboard(request):

    today = timezone.localdate()

    # =====================================================
    # FIND TRAINER
    # =====================================================

    trainer = Trainer.objects.filter(
        user=request.user
    ).first()

    if not trainer:
        trainer = Trainer.objects.filter(
            email=request.user.email
        ).first()

    if not trainer:

        return render(
            request,
            "trainer/trainer_dashboard.html",
            {
                "error": (
                    "Your account is not linked to a Trainer profile."
                )
            }
        )

    # =====================================================
    # TODAY ATTENDANCE
    # =====================================================

    attendance = DailyAttendance.objects.filter(
        trainer=trainer,
        date=today
    ).first()

    checked_in = bool(
        attendance
        and attendance.check_in
        and not attendance.check_out
    )

    checked_out = bool(
        attendance
        and attendance.check_out
    )

    # =====================================================
    # TODAY TASKS
    # =====================================================

    today_tasks = (
        TodoTask.objects
        .filter(
            trainer=trainer,
            for_date=today
        )
        .prefetch_related("subtasks")
        .order_by(
            "is_done",
            "-priority",
            "-created_on"
        )
    )

    # =====================================================
    # TODAY TASK STATISTICS
    # =====================================================

    task_stats = (
        TodoTask.objects
        .filter(
            trainer=trainer,
            for_date=today
        )
        .aggregate(
            total=Count("id"),

            completed=Count(
                "id",
                filter=Q(
                    status="completed"
                )
            ),

            in_progress=Count(
                "id",
                filter=Q(
                    status="in_progress"
                )
            ),

            pending=Count(
                "id",
                filter=Q(
                    status="pending"
                )
            ),

            planned_hours=Sum(
                "estimated_hours"
            ),
        )
    )

    total_tasks = (
        task_stats["total"] or 0
    )

    completed_tasks = (
        task_stats["completed"] or 0
    )

    in_progress_tasks = (
        task_stats["in_progress"] or 0
    )

    pending_tasks = (
        task_stats["pending"] or 0
    )

    planned_hours = (
        task_stats["planned_hours"]
        or Decimal("0")
    )

    if total_tasks > 0:

        completion_percentage = round(
            (
                completed_tasks
                / total_tasks
            ) * 100
        )

    else:

        completion_percentage = 0

    # =====================================================
    # TODAY LEARNING
    # =====================================================

    daily_learning = (
        DailyLearning.objects
        .filter(
            trainer=trainer,
            date=today
        )
        .first()
    )

    # =====================================================
    # PREVIOUS 7 DAYS
    # =====================================================

    previous_7_days_start = (
        today - timedelta(days=6)
    )

    previous_tasks = (
        TodoTask.objects
        .filter(
            trainer=trainer,
            for_date__gte=previous_7_days_start,
            for_date__lte=today
        )
        .prefetch_related("subtasks")
        .order_by(
            "-for_date",
            "-created_on"
        )
    )

    # =====================================================
    # OVERDUE WORK
    # =====================================================

    overdue_tasks = (
        TodoTask.objects
        .filter(
            trainer=trainer,
            for_date__lt=today
        )
        .exclude(
            status="completed"
        )
        .prefetch_related("subtasks")
        .order_by(
            "for_date",
            "-priority"
        )
    )

    # =====================================================
    # CURRENT MONTH
    # =====================================================

    month_start = today.replace(
        day=1
    )

    if today.month == 12:

        next_month = today.replace(
            year=today.year + 1,
            month=1,
            day=1
        )

    else:

        next_month = today.replace(
            month=today.month + 1,
            day=1
        )

    month_end = (
        next_month - timedelta(days=1)
    )

    # =====================================================
    # MONTHLY TASKS
    # =====================================================

    monthly_tasks = (
        TodoTask.objects
        .filter(
            trainer=trainer,
            for_date__gte=month_start,
            for_date__lte=month_end
        )
    )

    monthly_stats = (
        monthly_tasks.aggregate(

            total=Count("id"),

            completed=Count(
                "id",
                filter=Q(
                    status="completed"
                )
            ),

            in_progress=Count(
                "id",
                filter=Q(
                    status="in_progress"
                )
            ),

            pending=Count(
                "id",
                filter=Q(
                    status="pending"
                )
            ),

            planned_hours=Sum(
                "estimated_hours"
            ),
        )
    )

    monthly_total = (
        monthly_stats["total"] or 0
    )

    monthly_completed = (
        monthly_stats["completed"] or 0
    )

    monthly_in_progress = (
        monthly_stats["in_progress"] or 0
    )

    monthly_pending = (
        monthly_stats["pending"] or 0
    )

    monthly_planned_hours = (
        monthly_stats["planned_hours"]
        or Decimal("0")
    )

    if monthly_total > 0:

        monthly_completion_percentage = round(
            (
                monthly_completed
                / monthly_total
            ) * 100
        )

    else:

        monthly_completion_percentage = 0

    # =====================================================
    # MONTHLY CATEGORY STATISTICS
    # =====================================================

    monthly_category_stats = []

    for (
        category_code,
        category_name
    ) in TodoTask.CATEGORY_CHOICES:

        category_tasks = monthly_tasks.filter(
            category=category_code
        )

        category_total = (
            category_tasks.count()
        )

        category_completed = (
            category_tasks
            .filter(
                status="completed"
            )
            .count()
        )

        category_hours = (
            category_tasks
            .aggregate(
                total=Sum(
                    "estimated_hours"
                )
            )["total"]
            or Decimal("0")
        )

        monthly_category_stats.append({

            "code": category_code,

            "name": category_name,

            "total": category_total,

            "completed": category_completed,

            "hours": category_hours,
        })

    # =====================================================
    # MONTHLY LEARNING
    # =====================================================

    monthly_learning = (
        DailyLearning.objects
        .filter(
            trainer=trainer,
            date__gte=month_start,
            date__lte=month_end
        )
        .order_by("-date")
    )

    monthly_learning_days = (
        monthly_learning.count()
    )

    # =====================================================
    # ASSIGNED WORKSHOPS
    # =====================================================

    assigned_workshops = (
        Workshop.objects
        .filter(
            assigned_trainers=trainer
        )
        .select_related("college")
        .order_by("-start_date")
    )

    # =====================================================
    # UPCOMING WORKSHOPS
    # =====================================================

    upcoming_workshops = (
        assigned_workshops
        .filter(
            start_date__gte=today
        )
        .exclude(
            status="cancelled"
        )
        .order_by(
            "start_date"
        )[:5]
    )

    # =====================================================
    # ONGOING WORKSHOPS
    # =====================================================

    ongoing_workshops = (
        assigned_workshops
        .filter(
            start_date__lte=today,
            end_date__gte=today
        )
        .exclude(
            status__in=[
                "cancelled",
                "completed"
            ]
        )
    )

    # =====================================================
    # WEEKLY CALENDAR
    # =====================================================

    week_start = (
        today
        - timedelta(
            days=today.weekday()
        )
    )

    week_end = (
        week_start
        + timedelta(days=6)
    )

    calendar_events = (
        CalendarEvent.objects
        .filter(
            date__gte=week_start,
            date__lte=week_end,
            trainers=trainer
        )
        .select_related(
            "workshop",
            "college"
        )
        .prefetch_related(
            "trainers"
        )
        .order_by(
            "date",
            "start_time"
        )
    )

    weekly_schedule = []

    for offset in range(7):

        current_date = (
            week_start
            + timedelta(days=offset)
        )

        day_events = [
            event
            for event in calendar_events
            if event.date == current_date
        ]

        day_workshops = [
            workshop
            for workshop in assigned_workshops
            if (
                workshop.start_date
                <= current_date
                <= workshop.end_date
            )
        ]

        weekly_schedule.append({

            "date": current_date,

            "events": day_events,

            "workshops": day_workshops,
        })

    # =====================================================
    # TODAY SUBTASK STATISTICS
    # =====================================================

    today_subtasks = (
        SubTask.objects
        .filter(
            parent_task__trainer=trainer,
            parent_task__for_date=today
        )
    )

    total_subtasks = (
        today_subtasks.count()
    )

    completed_subtasks = (
        today_subtasks
        .filter(
            is_completed=True
        )
        .count()
    )

    if total_subtasks > 0:

        subtask_percentage = round(
            (
                completed_subtasks
                / total_subtasks
            ) * 100
        )

    else:

        subtask_percentage = 0

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "trainer": trainer,

        # Attendance
        "attendance": attendance,
        "checked_in": checked_in,
        "checked_out": checked_out,

        # Date
        "today": today,

        # Today
        "today_tasks": today_tasks,
        "daily_learning": daily_learning,

        # Today statistics
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "pending_tasks": pending_tasks,
        "planned_hours": planned_hours,
        "completion_percentage": completion_percentage,

        # Previous work
        "previous_tasks": previous_tasks,
        "overdue_tasks": overdue_tasks,

        # Monthly
        "month_start": month_start,
        "monthly_total": monthly_total,
        "monthly_completed": monthly_completed,
        "monthly_in_progress": monthly_in_progress,
        "monthly_pending": monthly_pending,
        "monthly_planned_hours": monthly_planned_hours,
        "monthly_completion_percentage":
            monthly_completion_percentage,
        "monthly_category_stats":
            monthly_category_stats,

        # Learning
        "monthly_learning":
            monthly_learning,

        "monthly_learning_days":
            monthly_learning_days,

        # Workshops
        "assigned_workshops":
            assigned_workshops,

        "upcoming_workshops":
            upcoming_workshops,

        "ongoing_workshops":
            ongoing_workshops,

        # Calendar
        "week_start": week_start,

        "week_end": week_end,

        "weekly_schedule":
            weekly_schedule,

        # Subtasks
        "total_subtasks":
            total_subtasks,

        "completed_subtasks":
            completed_subtasks,

        "subtask_percentage":
            subtask_percentage,
    }

    return render(
        request,
        "todo/trainer_dashboard.html",
        context
    )
@login_required
# ============================================================
# TRAINER PERSONAL SCHEDULE
# ============================================================

@login_required
def trainer_schedule(request):

    # ========================================================
    # FIND TRAINER CONNECTED TO LOGGED-IN USER
    # ========================================================

    trainer = (
        Trainer.objects
        .filter(user=request.user)
        .first()
    )

    # Fallback: match trainer by email
    if not trainer:
        trainer = (
            Trainer.objects
            .filter(email__iexact=request.user.email)
            .first()
        )

    if not trainer:

        messages.error(
            request,
            "Your account is not linked to a Trainer profile."
        )

        return redirect("dashboard")

    # ========================================================
    # EVENT COLORS
    # ========================================================

    event_colors = {

        "workshop": "#198754",
        "office_training": "#0d6efd",
        "fdp": "#dc3545",
        "online_workshop": "#20c997",
        "office": "#0d6efd",
        "guest_training": "#fd7e14",
        "meeting": "#6f42c1",
        "task": "#475569",
        "other": "#6c757d",

    }

    events = []

    # ========================================================
    # 1. WORKSHOPS ASSIGNED TO THIS TRAINER
    # ========================================================

    workshops = (
        Workshop.objects
        .filter(
            assigned_trainers=trainer
        )
        .select_related("college")
        .order_by("start_date")
    )

    for workshop in workshops:

        trainer_names = ", ".join(
            t.Name
            for t in workshop.assigned_trainers.all()
        )

        events.append({

            "id": f"workshop-{workshop.pk}",

            "title": f"📚 {workshop.title}",

            "start": (
                workshop.start_date.strftime("%Y-%m-%d")
                if workshop.start_date
                else None
            ),

            # FullCalendar end date is exclusive
            "end": (
                (
                    workshop.end_date +
                    timedelta(days=1)
                ).strftime("%Y-%m-%d")
                if workshop.end_date
                else None
            ),

            "allDay": True,

            "backgroundColor":
                event_colors["workshop"],

            "borderColor":
                event_colors["workshop"],

            # Trainer cannot move workshop
            "editable": False,

            "extendedProps": {

                "source": "Workshop",

                "trainers":
                    trainer_names,

                "event_type":
                    "Workshop",

                "college":
                    workshop.college.name
                    if workshop.college
                    else "—",

                "workshop":
                    workshop.title,

                "department":
                    workshop.departments or "—",

                "location":
                    workshop.college.name
                    if workshop.college
                    else "—",

                "status":
                    workshop.get_status_display(),

                "description":
                    workshop.remarks or "",

            },
        })

    # ========================================================
    # 2. OFFICE TRAINING ASSIGNED TO THIS TRAINER
    # ========================================================

    office_trainings = (
        OfficeTraining.objects
        .filter(
            trainers=trainer
        )
        .prefetch_related("trainers")
        .order_by("start_date")
    )

    for training in office_trainings:

        trainer_names = ", ".join(
            t.Name
            for t in training.trainers.all()
        )

        location = (
            training.hall
            if training.hall
            else "Mevi Technologies"
        )

        events.append({

            "id": f"office-{training.pk}",

            "title":
                f"🏢 {training.name}",

            "start": (
                training.start_date.strftime("%Y-%m-%d")
            ),

            "end": (
                (
                    training.end_date +
                    timedelta(days=1)
                ).strftime("%Y-%m-%d")
            ),

            "allDay": True,

            "backgroundColor":
                event_colors["office_training"],

            "borderColor":
                event_colors["office_training"],

            "editable": False,

            "extendedProps": {

                "source":
                    "Office Training",

                "trainers":
                    trainer_names,

                "event_type":
                    "Office Training",

                "college":
                    "Mevi Technologies",

                "workshop":
                    "—",

                "department":
                    "—",

                "location":
                    location,

                "status":
                    "Scheduled",

                "description":
                    (
                        f"Batch: {training.batch_id} | "
                        f"Mode: {training.get_mode_display()}"
                    ),

            },
        })

    # ========================================================
    # 3. CALENDAR EVENTS ASSIGNED TO THIS TRAINER
    # ========================================================

    calendar_events = (
        CalendarEvent.objects
        .filter(
            trainers=trainer
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

    for event in calendar_events:

        trainer_names = ", ".join(
            t.Name
            for t in event.trainers.all()
        )

        # -----------------------------------------------
        # START
        # -----------------------------------------------

        if event.start_time:

            start = (
                f"{event.date}T"
                f"{event.start_time}"
            )

        else:

            start = str(event.date)

        # -----------------------------------------------
        # END
        # -----------------------------------------------

        if event.end_time:

            end = (
                f"{event.date}T"
                f"{event.end_time}"
            )

        else:

            end = None

        event_type_key = (
            event.event_type
            if event.event_type
            else "other"
        )

        color = event_colors.get(
            event_type_key,
            event_colors["other"]
        )

        events.append({

            "id":
                f"event-{event.pk}",

            "title":
                f"📅 {event.title}",

            "start":
                start,

            "end":
                end,

            "allDay":
                not bool(event.start_time),

            "backgroundColor":
                color,

            "borderColor":
                color,

            "editable":
                False,

            "durationEditable":
                False,

            "startEditable":
                False,

            "extendedProps": {

                "source":
                    "Calendar Event",

                "trainers":
                    trainer_names,

                "event_type":
                    event.get_event_type_display(),

                "college":
                    (
                        event.college.name
                        if event.college
                        else "—"
                    ),

                "workshop":
                    (
                        event.workshop.title
                        if event.workshop
                        else "—"
                    ),

                "department":
                    event.department or "—",

                "location":
                    event.location or "—",

                "guest_faculty":
                    getattr(
                        event,
                        "guest_faculty",
                        ""
                    ),

                "status":
                    "Scheduled",

                "description":
                    event.description or "",

            },
        })

    # ========================================================
    # 4. TODO / DAILY WORK ASSIGNED TO THIS TRAINER
    # ========================================================

    tasks = (
        TodoTask.objects
        .filter(
            trainer=trainer
        )
        .select_related(
            "workshop",
            "office_training",
            "calendar_event"
        )
        .order_by(
            "for_date",
            "created_on"
        )
    )

    for task in tasks:

        # -----------------------------------------------
        # Determine task color
        # -----------------------------------------------

        if task.status == "completed":

            task_color = "#16a34a"

        elif task.status == "in_progress":

            task_color = "#f59e0b"

        else:

            task_color = event_colors["task"]

        # -----------------------------------------------
        # Determine linked work
        # -----------------------------------------------

        linked_work = "Independent Task"

        if task.workshop:

            linked_work = (
                f"Workshop: "
                f"{task.workshop.title}"
            )

        elif task.office_training:

            linked_work = (
                f"Office Training: "
                f"{task.office_training.name}"
            )

        elif task.calendar_event:

            linked_work = (
                f"Event: "
                f"{task.calendar_event.title}"
            )

        # -----------------------------------------------
        # Task event
        # -----------------------------------------------

        events.append({

            "id":
                f"task-{task.pk}",

            "title":
                f"✓ {task.task}",

            "start":
                str(task.for_date),

            "end":
                None,

            "allDay":
                True,

            "backgroundColor":
                task_color,

            "borderColor":
                task_color,

            "editable":
                False,

            "extendedProps": {

                "source":
                    "Daily Work",

                "trainers":
                    trainer.Name,

                "event_type":
                    "Assigned Work",

                "college":
                    "—",

                "workshop":
                    (
                        task.workshop.title
                        if task.workshop
                        else "—"
                    ),

                "department":
                    "—",

                "location":
                    "—",

                "status":
                    task.get_status_display(),

                "priority":
                    task.get_priority_display(),

                "linked_work":
                    linked_work,

                "description":
                    task.description or "",

            },
        })

    # ========================================================
    # SEND TO CALENDAR
    # ========================================================

    return render(
        request,
        "trainer_schedule.html",
        {
            "trainer": trainer,
            "events_json":
                json.dumps(
                    events,
                    default=str
                ),
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
def add_subtask(request, task_id):

    task = get_object_or_404(
        TodoTask,
        id=task_id
    )

    if request.method == "POST":

        title = request.POST.get("title", "").strip()

        if title:
            SubTask.objects.create(
                parent_task=task,
                title=title,
                is_completed=False
            )

            messages.success(
                request,
                "Subtask added successfully."
            )

        return redirect(
            "task_detail",
            task_id=task.id
        )

    return render(
        request,
        "todo/add_subtask.html",
        {
            "task": task
        }
    )
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
@user_passes_test(is_superuser)
def edit_subtask(request, subtask_id):

    subtask = get_object_or_404(
        SubTask,
        id=subtask_id
    )

    if request.method == "POST":

        title = request.POST.get("title", "").strip()

        if title:

            subtask.title = title
            subtask.save(
                update_fields=["title"]
            )

            messages.success(
                request,
                "Subtask updated successfully."
            )

            return redirect(
                "task_detail",
                task_id=subtask.parent_task.id
            )

        messages.error(
            request,
            "Subtask title cannot be empty."
        )

    return render(
        request,
        "todo/edit_subtask.html",
        {
            "subtask": subtask
        }
    )
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
from .models import DailyLearning
from .forms import DailyLearningForm
@login_required
def add_daily_learning(request):

    trainer = (
        Trainer.objects
        .filter(user=request.user)
        .first()
    )

    if not trainer:
        trainer = (
            Trainer.objects
            .filter(email=request.user.email)
            .first()
        )

    if not trainer:
        messages.error(
            request,
            "Your account is not linked to a Trainer profile."
        )
        return redirect("dashboard")

    today = timezone.localdate()

    learning, created = DailyLearning.objects.get_or_create(
        trainer=trainer,
        date=today,
        defaults={
            "learning": ""
        }
    )

    if request.method == "POST":

        form = DailyLearningForm(
            request.POST,
            instance=learning
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Today's learning has been saved successfully."
            )

            return redirect("trainer_dashboard")

    else:

        form = DailyLearningForm(
            instance=learning
        )

    return render(
        request,
        "todo/daily_learning.html",
        {
            "trainer": trainer,
            "today": today,
            "form": form,
            "learning": learning,
        }
    )

@login_required
def my_learning_history(request):

    trainer = (
        Trainer.objects
        .filter(user=request.user)
        .first()
    )

    if not trainer:
        trainer = (
            Trainer.objects
            .filter(email=request.user.email)
            .first()
        )

    if not trainer:
        messages.error(
            request,
            "Your account is not linked to a Trainer profile."
        )
        return redirect("dashboard")

    learnings = (
        DailyLearning.objects
        .filter(trainer=trainer)
        .order_by("-date")
    )

    return render(
        request,
        "todo/my_learning_history.html",
        {
            "trainer": trainer,
            "learnings": learnings,
        }
    )

# =====================================================
# FULL-TIME TRAINER WEEKLY WORK LIST
# =====================================================

@login_required
def full_time_work_list(request):

    today = timezone.localdate()

    # -------------------------------------------------
    # SELECT WEEK
    # -------------------------------------------------

    week_param = request.GET.get("week")

    if week_param:
        try:
            selected_date = date.fromisoformat(
                week_param
            )
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    week_start = (
        selected_date -
        timedelta(days=selected_date.weekday())
    )

    week_end = week_start + timedelta(days=6)

    # -------------------------------------------------
    # FULL-TIME TRAINERS
    # -------------------------------------------------

    trainers = (
        Trainer.objects
        .filter(is_full_time=True)
        .order_by("Name")
    )

    # -------------------------------------------------
    # OPTIONAL TRAINER FILTER
    # -------------------------------------------------

    trainer_id = request.GET.get("trainer")

    # -------------------------------------------------
    # WORKSHOPS
    # SOURCE: WORKSHOP LIST
    # -------------------------------------------------

    workshops = (
        Workshop.objects
        .filter(
            assigned_trainers__is_full_time=True,
            start_date__lte=week_end,
            end_date__gte=week_start
        )
        .select_related("college")
        .prefetch_related("assigned_trainers")
        .distinct()
        .order_by(
            "start_date",
            "title"
        )
    )

    if trainer_id:
        workshops = workshops.filter(
            assigned_trainers__id=trainer_id
        )

    # -------------------------------------------------
    # CALENDAR EVENTS
    # FDP / ONLINE WORKSHOP /
    # GUEST FACULTY / MEETING / OTHER
    # -------------------------------------------------

    events = (
        CalendarEvent.objects
        .filter(
            trainers__is_full_time=True,
            date__gte=week_start,
            date__lte=week_end
        )
        .select_related(
            "college",
            "workshop"
        )
        .prefetch_related("trainers")
        .distinct()
        .order_by(
            "date",
            "start_time"
        )
    )

    if trainer_id:
        events = events.filter(
            trainers__id=trainer_id
        )

    # -------------------------------------------------
    # BUILD TABLE ROWS
    # -------------------------------------------------

    schedule = []

    # =================================================
    # WORKSHOPS
    # =================================================

    for workshop in workshops:

        current_day = max(
            workshop.start_date,
            week_start
        )

        final_day = min(
            workshop.end_date,
            week_end
        )

        while current_day <= final_day:

            assigned_trainers = [
                trainer
                for trainer
                in workshop.assigned_trainers.all()
                if trainer.is_full_time
            ]

            if trainer_id:

                assigned_trainers = [
                    trainer
                    for trainer
                    in assigned_trainers
                    if str(trainer.id) == str(trainer_id)
                ]

            for trainer in assigned_trainers:

                schedule.append({
                    "date": current_day,
                    "trainer": trainer,
                    "title": workshop.title,
                    "type": "Workshop",
                    "college": (
                        workshop.college.name
                        if workshop.college
                        else "-"
                    ),
                    "time": "-",
                    "location": (
                        workshop.college.name
                        if workshop.college
                        else "-"
                    ),
                    "status": workshop.get_status_display(),
                    "source": "Workshop",
                    "source_id": workshop.id,
                })

            current_day += timedelta(days=1)

    # =================================================
    # CALENDAR EVENTS
    # =================================================

    for event in events:

        # Avoid duplicating normal workshop events
        # that are already coming from Workshop List.

        if (
            event.event_type == "workshop"
            and event.workshop
        ):
            continue

        time_text = "-"

        if event.start_time and event.end_time:

            time_text = (
                f"{event.start_time.strftime('%I:%M %p')}"
                f" - "
                f"{event.end_time.strftime('%I:%M %p')}"
            )

        elif event.start_time:

            time_text = (
                event.start_time.strftime("%I:%M %p")
            )

        event_trainers = [
            trainer
            for trainer in event.trainers.all()
            if trainer.is_full_time
        ]

        if trainer_id:

            event_trainers = [
                trainer
                for trainer in event_trainers
                if str(trainer.id) == str(trainer_id)
            ]

        for trainer in event_trainers:

            schedule.append({
                "date": event.date,
                "trainer": trainer,
                "title": event.title,
                "type": event.get_event_type_display(),
                "college": (
                    event.college.name
                    if event.college
                    else "-"
                ),
                "time": time_text,
                "location": event.location or "-",
                "status": "Scheduled",
                "source": "Calendar",
                "source_id": event.id,
            })

    # -------------------------------------------------
    # SORT
    # -------------------------------------------------

    schedule.sort(
        key=lambda item: (
            item["date"],
            item["trainer"].Name.lower(),
            item["time"]
        )
    )

    # -------------------------------------------------
    # WEEK NAVIGATION
    # -------------------------------------------------

    previous_week = (
        week_start -
        timedelta(days=7)
    )

    next_week = (
        week_start +
        timedelta(days=7)
    )

    # -------------------------------------------------
    # RENDER
    # -------------------------------------------------

    return render(
        request,
        "todo/full_time_work_list.html",
        {
            "schedule": schedule,
            "trainers": trainers,

            "selected_trainer":
                trainer_id,

            "week_start":
                week_start,

            "week_end":
                week_end,

            "previous_week":
                previous_week,

            "next_week":
                next_week,

            "today":
                today,
        }
    )

