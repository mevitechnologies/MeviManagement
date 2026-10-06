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

# ============================================================
# MEVI COMMAND CENTER / ADMIN DASHBOARD
# ============================================================
@login_required
def dashboard(request):

    today = timezone.localdate()

    # ============================================================
    # TASKS — TODAY ONLY FOR DASHBOARD
    # ============================================================

    today_tasks = (
        TodoTask.objects
        .filter(for_date=today)
        .select_related("trainer")
        .prefetch_related("subtasks")
        .order_by("-created_on")
    )

    today_pending = today_tasks.filter(
        status="pending"
    )

    today_in_progress = today_tasks.filter(
        status="in_progress"
    )

    today_completed = today_tasks.filter(
        status="completed"
    )

    # ============================================================
    # ALL TASK STATUS COUNTS
    # These are kept for the statistics cards.
    # ============================================================

    all_tasks = TodoTask.objects.all()

    pending_tasks = all_tasks.filter(
        status="pending"
    )

    in_progress_tasks = all_tasks.filter(
        status="in_progress"
    )

    completed_tasks = all_tasks.filter(
        status="completed"
    )

    # ============================================================
    # WORKSHOPS
    #
    # ACTIVE:
    # start <= today <= end
    #
    # UPCOMING:
    # start > today
    #
    # PAST WORKSHOPS ARE NOT SHOWN
    # ============================================================

    base_workshops = (
        Workshop.objects
        .select_related("college")
        .prefetch_related("assigned_trainers")
    )

    active_workshops = (
        base_workshops
        .filter(
            start_date__lte=today,
            end_date__gte=today
        )
        .exclude(
            status__in=[
                "cancelled",
                "postponed",
            ]
        )
        .order_by(
            "end_date",
            "title"
        )
    )

    upcoming_workshops = (
        base_workshops
        .filter(
            start_date__gt=today
        )
        .exclude(
            status__in=[
                "cancelled",
                "postponed",
            ]
        )
        .order_by(
            "start_date",
            "title"
        )[:10]
    )

    # ============================================================
    # CALENDAR EVENTS
    #
    # TODAY:
    # date == today
    #
    # UPCOMING:
    # date > today
    #
    # PAST EVENTS ARE NOT SHOWN
    # ============================================================

    base_events = (
        CalendarEvent.objects
        .select_related(
            "college",
            "workshop"
        )
        .prefetch_related("trainers")
    )

    todays_events = (
        base_events
        .filter(
            date=today
        )
        .order_by(
            "start_time",
            "title"
        )
    )

    upcoming_events = (
        base_events
        .filter(
            date__gt=today
        )
        .order_by(
            "date",
            "start_time",
            "title"
        )[:15]
    )

    # ============================================================
    # TRAINERS
    # ============================================================

    trainers = (
        Trainer.objects
        .select_related("user")
        .order_by("Name")
    )

    full_time_trainers = trainers.filter(
        is_full_time=True
    )

    # ============================================================
    # TODAY ATTENDANCE
    # ============================================================

    attendance_records = (
        DailyAttendance.objects
        .filter(
            date=today,
            trainer__is_full_time=True
        )
        .select_related("trainer")
    )

    attendance_map = {
        record.trainer_id: record
        for record in attendance_records
    }

    checked_in_count = sum(
        1
        for record in attendance_records
        if record.check_in
    )

    working_count = sum(
        1
        for record in attendance_records
        if record.check_in and not record.check_out
    )

    checked_out_count = sum(
        1
        for record in attendance_records
        if record.check_out
    )

    not_checked_in_count = max(
        full_time_trainers.count()
        - checked_in_count,
        0
    )

    # ============================================================
    # TRAINER STATUS
    # ============================================================

    trainer_status = []

    for trainer in full_time_trainers:

        attendance = attendance_map.get(
            trainer.id
        )

        trainer_today_tasks = today_tasks.filter(
            trainer=trainer
        )

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

            "task_count":
                trainer_today_tasks.count(),

            "completed_count":
                trainer_today_tasks.filter(
                    status="completed"
                ).count(),
        })

    # ============================================================
    # SUPER ADMIN TASK FORM
    # ============================================================

    form = None

    if request.user.is_superuser:

        form = TodoTaskForm(
            request.POST or None
        )

        if (
            request.method == "POST"
            and form.is_valid()
        ):

            form.save()

            messages.success(
                request,
                "Task created successfully."
            )

            return redirect(
                "admin_task_dashboard"
            )

    # ============================================================
    # MOTIVATIONAL STORIES
    # ============================================================

    stories = [

        {
            "title": "The Extra Mile",
            "text": (
                "A trainer once stayed back after a session "
                "because one student still had a question. "
                "That one extra conversation changed the student's "
                "confidence completely. Sometimes impact is created "
                "after the official work is already finished."
            )
        },

        {
            "title": "Small Steps Become Big Journeys",
            "text": (
                "A workshop does not become successful in one moment. "
                "It starts with one idea, one preparation task, one "
                "trainer, one classroom and one learner at a time. "
                "Every small task completed today contributes to "
                "tomorrow's bigger achievement."
            )
        },

        {
            "title": "Teach Beyond the Syllabus",
            "text": (
                "Students may forget a topic, a command or a syntax. "
                "But they remember the person who encouraged them "
                "when they were struggling. Great training is not "
                "only about completing content. It is about building confidence."
            )
        },

        {
            "title": "The Mevi Way",
            "text": (
                "Learn continuously. Share generously. "
                "Build patiently. Help genuinely. "
                "Every workshop, every project and every conversation "
                "is an opportunity to create meaningful impact."
            )
        },

        {
            "title": "One Student Can Change Everything",
            "text": (
                "Behind every successful learner is often a trainer "
                "who decided to explain something one more time. "
                "Never underestimate the value of patience, clarity "
                "and encouragement."
            )
        },

        {
            "title": "Progress Over Perfection",
            "text": (
                "Some days everything goes according to plan. "
                "Some days nothing does. What matters is that the team "
                "keeps moving, keeps learning and keeps improving."
            )
        },

        {
            "title": "Build People, Not Just Projects",
            "text": (
                "A completed project is an achievement. "
                "A student who gains confidence because of that project "
                "is an impact. The strongest teams create both."
            )
        },

        {
            "title": "Today's Work Becomes Tomorrow's Reputation",
            "text": (
                "Every training session, every document, every follow-up "
                "and every small responsibility contributes to the reputation "
                "of the entire team. Do today's work with tomorrow in mind."
            )
        },
    ]

    story = stories[
        today.toordinal() % len(stories)
    ]

    # ============================================================
    # RENDER
    # ============================================================

    return render(
        request,
        "todo/admin_dashboard.html",
        {

            # ----------------------------------------------------
            # DATE
            # ----------------------------------------------------

            "today": today,

            # ----------------------------------------------------
            # TASKS
            # ----------------------------------------------------

            "today_tasks":
                today_tasks,

            "today_pending":
                today_pending,

            "today_in_progress":
                today_in_progress,

            "today_completed":
                today_completed,

            "today_pending_count":
                today_pending.count(),

            "today_in_progress_count":
                today_in_progress.count(),

            "today_completed_count":
                today_completed.count(),

            # All task statistics
            "tasks":
                all_tasks,

            "pending_tasks":
                pending_tasks,

            "in_progress_tasks":
                in_progress_tasks,

            "completed_tasks":
                completed_tasks,

            "pending_count":
                pending_tasks.count(),

            "in_progress_count":
                in_progress_tasks.count(),

            "completed_count":
                completed_tasks.count(),

            # ----------------------------------------------------
            # WORKSHOPS
            # ----------------------------------------------------

            "active_workshops":
                active_workshops,

            "upcoming_workshops":
                upcoming_workshops,

            "active_workshop_count":
                active_workshops.count(),

            # ----------------------------------------------------
            # EVENTS
            # ----------------------------------------------------

            "todays_events":
                todays_events,

            "upcoming_events":
                upcoming_events,

            "upcoming_event_count":
                upcoming_events.count(),

            # ----------------------------------------------------
            # TRAINERS
            # ----------------------------------------------------

            "trainers":
                trainers,

            "full_time_trainers":
                full_time_trainers,

            "full_time_trainer_count":
                full_time_trainers.count(),

            "total_trainers":
                trainers.count(),

            "trainer_status":
                trainer_status,

            # ----------------------------------------------------
            # ATTENDANCE
            # ----------------------------------------------------

            "checked_in_count":
                checked_in_count,

            "working_count":
                working_count,

            "checked_out_count":
                checked_out_count,

            "not_checked_in_count":
                not_checked_in_count,

            # ----------------------------------------------------
            # FORM
            # ----------------------------------------------------

            "form":
                form,

            # ----------------------------------------------------
            # MOTIVATION
            # ----------------------------------------------------

            "story":
                story,
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

    # =====================================================
    # FILTER VALUES FROM URL
    # =====================================================

    search = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()
    college_filter = request.GET.get("college", "").strip()
    trainer_filter = request.GET.get("trainer", "").strip()
    start_date = request.GET.get("start_date", "").strip()
    end_date = request.GET.get("end_date", "").strip()


    # =====================================================
    # BASE QUERY
    # =====================================================

    workshops = (
        Workshop.objects
        .select_related("college")
        .prefetch_related("assigned_trainers")
        .all()
    )


    # =====================================================
    # SEARCH
    # =====================================================

    if search:

        workshops = workshops.filter(
            Q(title__icontains=search) |
            Q(college__name__icontains=search) |
            Q(departments__icontains=search) |
            Q(assigned_trainers__Name__icontains=search)
        ).distinct()


    # =====================================================
    # STATUS FILTER
    # =====================================================

    if status_filter:

        workshops = workshops.filter(
            status=status_filter
        )


    # =====================================================
    # COLLEGE FILTER
    # =====================================================

    if college_filter:

        workshops = workshops.filter(
            college_id=college_filter
        )


    # =====================================================
    # TRAINER FILTER
    # =====================================================

    if trainer_filter:

        workshops = workshops.filter(
            assigned_trainers__id=trainer_filter
        ).distinct()


    # =====================================================
    # START DATE
    # =====================================================

    if start_date:

        workshops = workshops.filter(
            start_date__gte=start_date
        )


    # =====================================================
    # END DATE
    # =====================================================

    if end_date:

        workshops = workshops.filter(
            end_date__lte=end_date
        )


    # =====================================================
    # CATEGORISE WORKSHOPS
    # =====================================================

    upcoming = workshops.filter(
        start_date__gt=today
    ).exclude(
        status__in=["cancelled", "postponed"]
    ).order_by("start_date")


    ongoing = workshops.filter(
        start_date__lte=today,
        end_date__gte=today
    ).exclude(
        status__in=["cancelled", "postponed"]
    ).order_by("start_date")


    tentative = workshops.filter(
        status="tentative",
        start_date__gte=today
    ).order_by("start_date")


    fixed = workshops.filter(
        status="fixed",
        start_date__gte=today
    ).order_by("start_date")


    post_workshop = workshops.filter(
        end_date__lt=today
    ).exclude(
        status__in=[
            "completed",
            "cancelled",
            "postponed"
        ]
    ).order_by("-end_date")


    completed = workshops.filter(
        status="completed"
    ).order_by("-end_date")


    postponed = workshops.filter(
        status="postponed"
    ).order_by("-start_date")


    cancelled = workshops.filter(
        status="cancelled"
    ).order_by("-start_date")


    # =====================================================
    # FILTER OPTIONS
    # =====================================================

    colleges = College.objects.all().order_by("name")

    trainers = Trainer.objects.all().order_by("Name")


    # =====================================================
    # RETURN
    # =====================================================

    return render(
        request,
        "workshop_list.html",
        {

            "upcoming": upcoming,
            "ongoing": ongoing,
            "tentative": tentative,
            "fixed": fixed,
            "post_workshop": post_workshop,
            "completed": completed,
            "postponed": postponed,
            "cancelled": cancelled,

            # Filter options
            "colleges": colleges,
            "trainers": trainers,

            # Current filters
            "search": search,
            "status_filter": status_filter,
            "college_filter": college_filter,
            "trainer_filter": trainer_filter,
            "start_date": start_date,
            "end_date": end_date,

            "today": today,
            "is_admin": request.user.is_staff,
        }
    )

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

# ============================================================
# MEVI COMMAND CENTER / ADMIN DASHBOARD
# ============================================================

@login_required
def admin_task_dashboard(request):

    today = timezone.localdate()

    # ========================================================
    # TASKS
    # ========================================================

    tasks = (
        TodoTask.objects
        .select_related("trainer")
        .prefetch_related("subtasks")
        .order_by("for_date", "-created_on")
    )

    pending_tasks = tasks.filter(
        status="pending"
    )

    in_progress_tasks = tasks.filter(
        status="in_progress"
    )

    completed_tasks = tasks.filter(
        status="completed"
    )

    today_tasks = tasks.filter(
        for_date=today
    )

    # ========================================================
    # WORKSHOPS
    # ========================================================

    workshops = (
        Workshop.objects
        .select_related("college")
        .prefetch_related("assigned_trainers")
        .order_by("start_date", "title")
    )

    upcoming_workshops = workshops.filter(
        end_date__gte=today
    ).exclude(
        status="cancelled"
    )[:10]

    active_workshops = workshops.filter(
        start_date__lte=today,
        end_date__gte=today
    ).exclude(
        status="cancelled"
    )

    # ========================================================
    # CALENDAR EVENTS
    # ========================================================

    events = (
        CalendarEvent.objects
        .select_related(
            "college",
            "workshop"
        )
        .prefetch_related("trainers")
        .filter(
            date__gte=today
        )
        .order_by(
            "date",
            "start_time"
        )[:15]
    )

    # ========================================================
    # TRAINERS
    # ========================================================

    trainers = (
        Trainer.objects
        .select_related("user")
        .order_by("Name")
    )

    full_time_trainers = trainers.filter(
        is_full_time=True
    )

    # ========================================================
    # TODAY ATTENDANCE
    # ========================================================

    attendance_records = (
        DailyAttendance.objects
        .filter(
            date=today,
            trainer__is_full_time=True
        )
        .select_related("trainer")
    )

    attendance_map = {
        record.trainer_id: record
        for record in attendance_records
    }

    checked_in_count = sum(
        1
        for record in attendance_records
        if record.check_in
    )

    working_count = sum(
        1
        for record in attendance_records
        if record.check_in and not record.check_out
    )

    checked_out_count = sum(
        1
        for record in attendance_records
        if record.check_out
    )

    not_checked_in_count = max(
        full_time_trainers.count() - checked_in_count,
        0
    )

    # ========================================================
    # TRAINER STATUS
    # ========================================================

    trainer_status = []

    for trainer in full_time_trainers:

        attendance = attendance_map.get(
            trainer.id
        )

        trainer_today_tasks = today_tasks.filter(
            trainer=trainer
        )

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
            "task_count": trainer_today_tasks.count(),
            "completed_count": trainer_today_tasks.filter(
                status="completed"
            ).count(),
        })

    # ========================================================
    # FORM
    # ========================================================

    form = None

    if request.user.is_superuser:

        form = TodoTaskForm(
            request.POST or None
        )

        if (
            request.method == "POST"
            and form.is_valid()
        ):

            form.save()

            messages.success(
                request,
                "Task created successfully."
            )

            return redirect(
                "admin_task_dashboard"
            )

    # ========================================================
    # MOTIVATIONAL STORIES
    # ========================================================

    stories = [

        {
            "title": "The Extra Mile",
            "text": (
                "A trainer once stayed back after a session "
                "because one student still had a question. "
                "That one extra conversation changed the student's "
                "confidence completely. Sometimes impact is created "
                "after the official work is already finished."
            )
        },

        {
            "title": "Small Steps Become Big Journeys",
            "text": (
                "A workshop does not become successful in one moment. "
                "It starts with one idea, one preparation task, one "
                "trainer, one classroom and one learner at a time. "
                "Every small task completed today contributes to "
                "tomorrow's bigger achievement."
            )
        },

        {
            "title": "Teach Beyond the Syllabus",
            "text": (
                "Students may forget a topic, a command or a syntax. "
                "But they remember the person who encouraged them "
                "when they were struggling. Great training is not "
                "only about completing content. It is about building confidence."
            )
        },

        {
            "title": "The Mevi Way",
            "text": (
                "Learn continuously. Share generously. "
                "Build patiently. Help genuinely. "
                "Every workshop, every project and every conversation "
                "is an opportunity to create meaningful impact."
            )
        },

        {
            "title": "One Student Can Change Everything",
            "text": (
                "Behind every successful learner is often a trainer "
                "who decided to explain something one more time. "
                "Never underestimate the value of patience, clarity "
                "and encouragement."
            )
        },

        {
            "title": "Progress Over Perfection",
            "text": (
                "Some days everything goes according to plan. "
                "Some days nothing does. What matters is that the team "
                "keeps moving, keeps learning and keeps improving."
            )
        },

        {
            "title": "Build People, Not Just Projects",
            "text": (
                "A completed project is an achievement. "
                "A student who gains confidence because of that project "
                "is an impact. The strongest teams create both."
            )
        },

        {
            "title": "Today's Work Becomes Tomorrow's Reputation",
            "text": (
                "Every training session, every document, every follow-up "
                "and every small responsibility contributes to the reputation "
                "of the entire team. Do today's work with tomorrow in mind."
            )
        },

    ]

    story = stories[
        today.toordinal() % len(stories)
    ]

    # ========================================================
    # RENDER
    # ========================================================

    return render(
        request,
        "todo/admin_dashboard.html",
        {
            "today": today,

            # Tasks
            "form": form,
            "tasks": tasks,
            "today_tasks": today_tasks,
            "pending_tasks": pending_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completed_tasks": completed_tasks,

            "grouped_tasks": {
                "pending": pending_tasks,
                "in_progress": in_progress_tasks,
                "completed": completed_tasks,
            },

            # Workshops
            "workshops": workshops,
            "upcoming_workshops": upcoming_workshops,
            "active_workshops": active_workshops,

            # Events
            "events": events,

            # Trainers
            "trainers": trainers,
            "full_time_trainers": full_time_trainers,
            "trainer_status": trainer_status,

            # Attendance
            "checked_in_count": checked_in_count,
            "working_count": working_count,
            "checked_out_count": checked_out_count,
            "not_checked_in_count": not_checked_in_count,

            # Statistics
            "total_trainers": trainers.count(),
            "full_time_trainer_count": full_time_trainers.count(),
            "total_tasks": tasks.count(),
            "pending_count": pending_tasks.count(),
            "in_progress_count": in_progress_tasks.count(),
            "completed_count": completed_tasks.count(),
            "active_workshop_count": active_workshops.count(),
            "upcoming_event_count": events.count(),

            # Motivation
            "story": story,
        }
    )

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
    # TRAINER CHECK
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
    # STATUS
    # ============================================================

    new_status = request.POST.get(
        "status"
    )

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

        return redirect(
            f"{reverse('trainer_dashboard')}?attendance_date={task.for_date.isoformat()}"
        )

    # ============================================================
    # UPDATE
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
    # MESSAGE
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
    # RETURN TO THE SAME DAY
    # ============================================================

    if request.user.is_superuser:

        return redirect(
            "admin_task_dashboard"
        )

    return redirect(
        f"{reverse('trainer_dashboard')}?attendance_date={task.for_date.isoformat()}"
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


# ============================================================
# TRAINER ATTENDANCE PAGE
# ============================================================

# ============================================================
# TRAINER ATTENDANCE + DAILY WORKSPACE
# ============================================================

# ============================================================
# TRAINER ATTENDANCE + DAILY WORKSPACE
# ============================================================

@login_required
def trainer_attendance(request):

    # --------------------------------------------------------
    # FIND LOGGED-IN TRAINER
    # --------------------------------------------------------

    trainer = (
        Trainer.objects
        .filter(user=request.user)
        .first()
    )

    if not trainer:
        trainer = (
            Trainer.objects
            .filter(
                email__iexact=request.user.email
            )
            .first()
        )

    if not trainer:
        messages.error(
            request,
            "Your account is not linked to a Trainer profile."
        )
        return redirect("dashboard")

    # --------------------------------------------------------
    # FULL-TIME TRAINERS ONLY
    # --------------------------------------------------------

    if not trainer.is_full_time:

        messages.error(
            request,
            "Attendance is available only for full-time trainers."
        )

        return redirect("trainer_dashboard")

    today = timezone.localdate()

    # --------------------------------------------------------
    # ATTENDANCE DATE RANGE
    # TODAY + PREVIOUS 2 DAYS
    # --------------------------------------------------------

    minimum_date = today - timedelta(days=2)
    maximum_date = today

    # --------------------------------------------------------
    # SELECTED DATE
    # --------------------------------------------------------

    selected_date = today

    date_value = request.GET.get(
        "attendance_date"
    )

    if date_value:

        try:

            selected_date = date.fromisoformat(
                date_value
            )

        except (
            ValueError,
            TypeError
        ):

            messages.error(
                request,
                "Invalid attendance date."
            )

            selected_date = today

    # --------------------------------------------------------
    # VALIDATE DATE
    # --------------------------------------------------------

    if selected_date < minimum_date:

        messages.warning(
            request,
            "You can manage attendance only for today and the previous two days."
        )

        selected_date = minimum_date

    elif selected_date > maximum_date:

        messages.warning(
            request,
            "Future attendance is not allowed."
        )

        selected_date = today

    # --------------------------------------------------------
    # GET / CREATE ATTENDANCE
    # --------------------------------------------------------

    attendance, created = (
        DailyAttendance.objects.get_or_create(
            trainer=trainer,
            date=selected_date
        )
    )

    # ========================================================
    # POST ACTIONS
    # ========================================================

    if request.method == "POST":

        action = (
            request.POST
            .get("action", "")
            .strip()
        )

        # ====================================================
        # CHECK IN NOW
        # ====================================================

        if action in (
            "check_in_now",
            "check_in"
        ):

            # -----------------------------------------------
            # ONLY TODAY
            # -----------------------------------------------

            if selected_date != today:

                messages.error(
                    request,
                    "Use manual time entry for previous days."
                )

            # -----------------------------------------------
            # ALREADY CHECKED IN
            # -----------------------------------------------

            elif attendance.check_in:

                messages.warning(
                    request,
                    "You have already checked in."
                )

            else:

                now = timezone.localtime()

                # -------------------------------------------
                # CHECK-IN CUTOFF
                # 8:30 PM
                # -------------------------------------------

                if now.time() >= time(20, 30):

                    messages.error(
                        request,
                        "Check-in is closed after 8:30 PM."
                    )

                else:

                    attendance.check_in = timezone.now()

                    # In case an old checkout exists,
                    # clear it when starting a fresh check-in.
                    attendance.check_out = None

                    attendance.save(
                        update_fields=[
                            "check_in",
                            "check_out"
                        ]
                    )

                    messages.success(
                        request,
                        "You have successfully checked in."
                    )

        # ====================================================
        # CHECK OUT NOW
        # ====================================================

        elif action in (
            "check_out_now",
            "check_out"
        ):

            # -----------------------------------------------
            # ONLY TODAY
            # -----------------------------------------------

            if selected_date != today:

                messages.error(
                    request,
                    "Use manual time entry for previous days."
                )

            # -----------------------------------------------
            # MUST CHECK IN FIRST
            # -----------------------------------------------

            elif not attendance.check_in:

                messages.error(
                    request,
                    "You must check in before checking out."
                )

            # -----------------------------------------------
            # ALREADY CHECKED OUT
            # -----------------------------------------------

            elif attendance.check_out:

                messages.warning(
                    request,
                    "You have already checked out."
                )

            else:

                now = timezone.localtime()

                # -------------------------------------------
                # MAXIMUM CHECKOUT = 8:30 PM
                # -------------------------------------------

                maximum_checkout_time = time(
                    20,
                    30
                )

                if now.time() > maximum_checkout_time:

                    local_checkout = datetime.combine(
                        today,
                        maximum_checkout_time
                    )

                    checkout_datetime = (
                        timezone.make_aware(
                            local_checkout,
                            timezone.get_current_timezone()
                        )
                    )

                else:

                    checkout_datetime = timezone.now()

                # -------------------------------------------
                # SAFETY CHECK
                # -------------------------------------------

                if checkout_datetime <= attendance.check_in:

                    messages.error(
                        request,
                        "Check-out time must be after check-in time."
                    )

                else:

                    attendance.check_out = (
                        checkout_datetime
                    )

                    attendance.save(
                        update_fields=[
                            "check_out"
                        ]
                    )

                    messages.success(
                        request,
                        "You have successfully checked out."
                    )

        # ====================================================
        # MANUAL PREVIOUS-DAY ATTENDANCE
        # ====================================================

        elif action == "save_manual_attendance":

            # ------------------------------------------------
            # TODAY USES LIVE BUTTONS
            # ------------------------------------------------

            if selected_date == today:

                messages.error(
                    request,
                    "For today, please use Check In Now / Check Out Now."
                )

            else:

                check_in_value = (
                    request.POST
                    .get(
                        "check_in_time",
                        ""
                    )
                    .strip()
                )

                check_out_value = (
                    request.POST
                    .get(
                        "check_out_time",
                        ""
                    )
                    .strip()
                )

                # --------------------------------------------
                # CHECK-IN REQUIRED
                # --------------------------------------------

                if not check_in_value:

                    messages.error(
                        request,
                        "Please enter the check-in time."
                    )

                else:

                    try:

                        # ------------------------------------
                        # CHECK-IN TIME
                        # ------------------------------------

                        check_in_clock = (
                            time.fromisoformat(
                                check_in_value
                            )
                        )

                        check_in_datetime = (
                            timezone.make_aware(
                                datetime.combine(
                                    selected_date,
                                    check_in_clock
                                ),
                                timezone.get_current_timezone()
                            )
                        )

                        # ------------------------------------
                        # CHECK-OUT TIME
                        # ------------------------------------

                        check_out_datetime = None
                        check_out_clock = None

                        if check_out_value:

                            check_out_clock = (
                                time.fromisoformat(
                                    check_out_value
                                )
                            )

                            check_out_datetime = (
                                timezone.make_aware(
                                    datetime.combine(
                                        selected_date,
                                        check_out_clock
                                    ),
                                    timezone.get_current_timezone()
                                )
                            )

                        # ------------------------------------
                        # CHECK-IN VALIDATION
                        # ------------------------------------

                        if check_in_clock >= time(
                            20,
                            30
                        ):

                            messages.error(
                                request,
                                "Check-in time cannot be 8:30 PM or later."
                            )

                        # ------------------------------------
                        # CHECK-OUT VALIDATION
                        # ------------------------------------

                        elif (
                            check_out_clock
                            and check_out_clock > time(
                                20,
                                30
                            )
                        ):

                            messages.error(
                                request,
                                "Check-out cannot be later than 8:30 PM."
                            )

                        # ------------------------------------
                        # CHECKOUT AFTER CHECKIN
                        # ------------------------------------

                        elif (
                            check_out_datetime
                            and check_out_datetime <=
                            check_in_datetime
                        ):

                            messages.error(
                                request,
                                "Check-out time must be after check-in time."
                            )

                        else:

                            attendance.check_in = (
                                check_in_datetime
                            )

                            attendance.check_out = (
                                check_out_datetime
                            )

                            attendance.save(
                                update_fields=[
                                    "check_in",
                                    "check_out"
                                ]
                            )

                            messages.success(
                                request,
                                "Attendance time saved successfully."
                            )

                    except (
                        ValueError,
                        TypeError
                    ):

                        messages.error(
                            request,
                            "Please enter a valid time."
                        )

        # ====================================================
        # ADD WORK
        # ====================================================

        elif action == "add_work":

            task_text = (
                request.POST
                .get(
                    "task",
                    ""
                )
                .strip()
            )

            description = (
                request.POST
                .get(
                    "description",
                    ""
                )
                .strip()
            )

            category = (
                request.POST
                .get(
                    "category",
                    "other"
                )
                .strip()
            )

            priority = (
                request.POST
                .get(
                    "priority",
                    "medium"
                )
                .strip()
            )

            estimated_hours_value = (
                request.POST
                .get(
                    "estimated_hours",
                    "1"
                )
                .strip()
            )

            # -----------------------------------------------
            # TASK REQUIRED
            # -----------------------------------------------

            if not task_text:

                messages.error(
                    request,
                    "Please enter the work/task."
                )

            # -----------------------------------------------
            # CHECK-IN REQUIRED
            #
            # IMPORTANT:
            # CHECKOUT DOES NOT BLOCK WORK.
            # -----------------------------------------------

            elif not attendance.check_in:

                messages.error(
                    request,
                    "Please record attendance before adding work."
                )

            else:

                # -------------------------------------------
                # ESTIMATED HOURS
                # -------------------------------------------

                try:

                    estimated_hours = Decimal(
                        estimated_hours_value
                    )

                except (
                    ValueError,
                    TypeError,
                    InvalidOperation
                ):

                    estimated_hours = Decimal(
                        "1"
                    )

                # -------------------------------------------
                # VALID CATEGORY
                # -------------------------------------------

                valid_categories = dict(
                    TodoTask.CATEGORY_CHOICES
                )

                if category not in valid_categories:

                    category = "other"

                # -------------------------------------------
                # VALID PRIORITY
                # -------------------------------------------

                valid_priorities = dict(
                    TodoTask.PRIORITY_CHOICES
                )

                if priority not in valid_priorities:

                    priority = "medium"

                # -------------------------------------------
                # CREATE WORK
                #
                # NO CHECKOUT RESTRICTION HERE
                # -------------------------------------------

                TodoTask.objects.create(
                    trainer=trainer,
                    task=task_text,
                    description=description,
                    category=category,
                    priority=priority,
                    estimated_hours=estimated_hours,
                    for_date=selected_date,
                    status="in_progress",
                    is_done=False,
                )

                messages.success(
                    request,
                    "Work has been added successfully."
                )

        # ====================================================
        # SAVE LEARNING
        # ====================================================

        elif action == "save_learning":

            learning_text = (
                request.POST
                .get(
                    "learning",
                    ""
                )
                .strip()
            )

            if not learning_text:

                messages.error(
                    request,
                    "Please enter your learning."
                )

            else:

                DailyLearning.objects.update_or_create(
                    trainer=trainer,
                    date=selected_date,
                    defaults={
                        "learning": learning_text
                    }
                )

                messages.success(
                    request,
                    "Daily learning saved successfully."
                )

        # ----------------------------------------------------
        # REDIRECT TO SAME DATE
        # ----------------------------------------------------

        return redirect(
            f"{reverse('trainer_attendance')}"
            f"?attendance_date="
            f"{selected_date.isoformat()}"
        )

    # ========================================================
    # GET CURRENT LEARNING
    # ========================================================

    learning = (
        DailyLearning.objects
        .filter(
            trainer=trainer,
            date=selected_date
        )
        .first()
    )

    # ========================================================
    # WORK FOR SELECTED DATE
    # ========================================================

    work_items = (
        TodoTask.objects
        .filter(
            trainer=trainer,
            for_date=selected_date
        )
        .order_by(
            "-created_on"
        )
    )

    # ========================================================
    # CALCULATE WORKED HOURS
    # ========================================================

    worked_hours = None

    if (
        attendance.check_in
        and attendance.check_out
    ):

        duration = (
            attendance.check_out
            - attendance.check_in
        )

        total_seconds = (
            duration.total_seconds()
        )

        worked_hours = round(
            total_seconds / 3600,
            2
        )

    # ========================================================
    # STATUS
    # ========================================================

    checked_in = bool(
        attendance.check_in
        and not attendance.check_out
    )

    checked_out = bool(
        attendance.check_out
    )

    # ========================================================
    # DATE OPTIONS
    # ========================================================

    date_options = []

    for offset in range(
        2,
        -1,
        -1
    ):

        day = (
            today
            - timedelta(days=offset)
        )

        day_attendance = (
            DailyAttendance.objects
            .filter(
                trainer=trainer,
                date=day
            )
            .first()
        )

        date_options.append({

            "date": day,

            "attendance":
                day_attendance,

            "is_today":
                day == today,

        })

    # ========================================================
    # RENDER
    # ========================================================

    return render(
        request,
        "todo/trainer_attendance.html",
        {
            "trainer":
                trainer,

            "attendance":
                attendance,

            "attendance_date":
                selected_date,

            "minimum_attendance_date":
                minimum_date,

            "maximum_attendance_date":
                maximum_date,

            "today":
                today,

            "checked_in":
                checked_in,

            "checked_out":
                checked_out,

            "worked_hours":
                worked_hours,

            "learning":
                learning,

            "work_items":
                work_items,

            "date_options":
                date_options,

            "category_choices":
                TodoTask.CATEGORY_CHOICES,

            "priority_choices":
                TodoTask.PRIORITY_CHOICES,
        }
    )
# ============================================================
# TRAINER DASHBOARD
# ============================================================

@login_required
def trainer_dashboard(request):

    # ============================================================
    # BASIC DATE
    # ============================================================

    today = timezone.localdate()

    # ============================================================
    # FIND TRAINER
    # ============================================================

    trainer = (
        Trainer.objects
        .filter(user=request.user)
        .first()
    )

    if not trainer:

        trainer = (
            Trainer.objects
            .filter(
                email__iexact=request.user.email
            )
            .first()
        )

    if not trainer:

        return render(
            request,
            "todo/trainer_dashboard.html",
            {
                "error":
                    "Your account is not linked to a Trainer profile."
            }
        )

    # ============================================================
    # ============================================================
    # ATTENDANCE
    # TODAY + PREVIOUS 2 DAYS
    # ============================================================
    # ============================================================

    minimum_attendance_date = (
        today - timedelta(days=2)
    )

    maximum_attendance_date = today

    # ------------------------------------------------------------
    # DATE SELECTED FROM DASHBOARD
    # ------------------------------------------------------------

    attendance_date_value = request.GET.get(
        "attendance_date"
    )

    attendance_date = today

    if attendance_date_value:

        try:

            attendance_date = date.fromisoformat(
                attendance_date_value
            )

        except (
            ValueError,
            TypeError
        ):

            attendance_date = today

    # ------------------------------------------------------------
    # NEVER ALLOW FUTURE DATE
    # NEVER ALLOW MORE THAN 2 DAYS OLD
    # ------------------------------------------------------------

    if attendance_date < minimum_attendance_date:

        messages.warning(
            request,
            "Attendance can only be opened for today or the previous 2 days."
        )

        attendance_date = today

    elif attendance_date > maximum_attendance_date:

        messages.warning(
            request,
            "Future attendance is not allowed."
        )

        attendance_date = today

    # ------------------------------------------------------------
    # GET ATTENDANCE FOR SELECTED DATE
    # ------------------------------------------------------------

    attendance, attendance_created = (
        DailyAttendance.objects.get_or_create(
            trainer=trainer,
            date=attendance_date
        )
    )

    # ------------------------------------------------------------
    # ATTENDANCE STATUS
    # ------------------------------------------------------------

    checked_in = bool(
        attendance.check_in
        and not attendance.check_out
    )

    checked_out = bool(
        attendance.check_out
    )

    # ============================================================
    # TODAY'S TASKS
    # ============================================================

    today_tasks = (
        TodoTask.objects
        .filter(
            trainer=trainer,
            for_date=today
        )
        .prefetch_related(
            "subtasks"
        )
        .order_by(
            "is_done",
            "-priority",
            "-created_on"
        )
    )

    # ============================================================
    # TODAY TASK STATISTICS
    # ============================================================

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

    # ============================================================
    # TODAY LEARNING
    # ============================================================

    daily_learning = (
        DailyLearning.objects
        .filter(
            trainer=trainer,
            date=today
        )
        .first()
    )

    # ============================================================
    # PREVIOUS 7 DAYS
    # ============================================================

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
        .prefetch_related(
            "subtasks"
        )
        .order_by(
            "-for_date",
            "-created_on"
        )
    )

    # ============================================================
    # OVERDUE WORK
    # ============================================================

    overdue_tasks = (
        TodoTask.objects
        .filter(
            trainer=trainer,
            for_date__lt=today
        )
        .exclude(
            status="completed"
        )
        .prefetch_related(
            "subtasks"
        )
        .order_by(
            "for_date",
            "-priority"
        )
    )

    # ============================================================
    # CURRENT MONTH
    # ============================================================

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

    # ============================================================
    # MONTHLY TASKS
    # ============================================================

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

    # ============================================================
    # MONTHLY CATEGORY STATISTICS
    # ============================================================

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

            "code":
                category_code,

            "name":
                category_name,

            "total":
                category_total,

            "completed":
                category_completed,

            "hours":
                category_hours,
        })

    # ============================================================
    # MONTHLY LEARNING
    # ============================================================

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

    # ============================================================
    # ASSIGNED WORKSHOPS
    # ============================================================

    assigned_workshops = (
        Workshop.objects
        .filter(
            assigned_trainers=trainer
        )
        .select_related(
            "college"
        )
        .order_by(
            "-start_date"
        )
    )

    # ============================================================
    # UPCOMING WORKSHOPS
    # ============================================================

    upcoming_workshops = (
        assigned_workshops
        .filter(
            start_date__gte=today
        )
        .exclude(
            status__in=[
                "cancelled",
                "postponed"
            ]
        )
        .order_by(
            "start_date"
        )[:5]
    )

    # ============================================================
    # ONGOING WORKSHOPS
    # ============================================================

    ongoing_workshops = (
        assigned_workshops
        .filter(
            start_date__lte=today,
            end_date__gte=today
        )
        .exclude(
            status__in=[
                "cancelled",
                "completed",
                "postponed"
            ]
        )
    )

    # ============================================================
    # ============================================================
    # ROLLING 7-DAY CALENDAR
    # ============================================================
    #
    # IMPORTANT:
    # Instead of Monday-Sunday, this uses:
    #
    # previous 2 days + today + next 4 days
    #
    # This guarantees that the attendance dates are ALWAYS visible.
    # ============================================================
    # ============================================================

    week_start = (
        today - timedelta(days=2)
    )

    week_end = (
        today + timedelta(days=4)
    )

    # ------------------------------------------------------------
    # CALENDAR EVENTS FOR TRAINER
    # ------------------------------------------------------------

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

    # ------------------------------------------------------------
    # WEEKLY SCHEDULE
    # ------------------------------------------------------------

    weekly_schedule = []

    for offset in range(7):

        current_date = (
            week_start
            + timedelta(days=offset)
        )

        day_events = [

            event

            for event
            in calendar_events

            if event.date == current_date
        ]

        day_workshops = [

            workshop

            for workshop
            in assigned_workshops

            if (
                workshop.start_date
                and workshop.end_date
                and
                workshop.start_date
                <= current_date
                <= workshop.end_date
            )
        ]

        weekly_schedule.append({

            "date":
                current_date,

            "events":
                day_events,

            "workshops":
                day_workshops,

        })

    # ============================================================
    # TODAY SUBTASK STATISTICS
    # ============================================================

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

    # ============================================================
    # FINAL CONTEXT
    # ============================================================

    context = {

        "trainer":
            trainer,

        # --------------------------------------------------------
        # ATTENDANCE
        # --------------------------------------------------------

        "attendance":
            attendance,

        "checked_in":
            checked_in,

        "checked_out":
            checked_out,

        "attendance_date":
            attendance_date,

        "minimum_attendance_date":
            minimum_attendance_date,

        "maximum_attendance_date":
            maximum_attendance_date,

        "is_full_time":
            trainer.is_full_time,

        # --------------------------------------------------------
        # DATE
        # --------------------------------------------------------

        "today":
            today,

        # --------------------------------------------------------
        # TODAY
        # --------------------------------------------------------

        "today_tasks":
            today_tasks,

        "daily_learning":
            daily_learning,

        "total_tasks":
            total_tasks,

        "completed_tasks":
            completed_tasks,

        "in_progress_tasks":
            in_progress_tasks,

        "pending_tasks":
            pending_tasks,

        "planned_hours":
            planned_hours,

        "completion_percentage":
            completion_percentage,

        # --------------------------------------------------------
        # PREVIOUS WORK
        # --------------------------------------------------------

        "previous_tasks":
            previous_tasks,

        "overdue_tasks":
            overdue_tasks,

        # --------------------------------------------------------
        # MONTHLY
        # --------------------------------------------------------

        "month_start":
            month_start,

        "monthly_total":
            monthly_total,

        "monthly_completed":
            monthly_completed,

        "monthly_in_progress":
            monthly_in_progress,

        "monthly_pending":
            monthly_pending,

        "monthly_planned_hours":
            monthly_planned_hours,

        "monthly_completion_percentage":
            monthly_completion_percentage,

        "monthly_category_stats":
            monthly_category_stats,

        # --------------------------------------------------------
        # LEARNING
        # --------------------------------------------------------

        "monthly_learning":
            monthly_learning,

        "monthly_learning_days":
            monthly_learning_days,

        # --------------------------------------------------------
        # WORKSHOPS
        # --------------------------------------------------------

        "assigned_workshops":
            assigned_workshops,

        "upcoming_workshops":
            upcoming_workshops,

        "ongoing_workshops":
            ongoing_workshops,

        # --------------------------------------------------------
        # CALENDAR
        # --------------------------------------------------------

        "week_start":
            week_start,

        "week_end":
            week_end,

        "weekly_schedule":
            weekly_schedule,

        # --------------------------------------------------------
        # SUBTASKS
        # --------------------------------------------------------

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

    # =========================================================
    # WORKSHOPS
    # =========================================================
    workshops = Workshop.objects.prefetch_related(
        "assigned_trainers"
    ).all()

    for w in workshops:

        trainer_names = ", ".join(
            trainer.Name
            for trainer in w.assigned_trainers.all()
        )

        events.append({
            "id": f"workshop-{w.pk}",
            "title": f"📚 {w.title}",

            "start": w.start_date.strftime("%Y-%m-%d"),
            "end": (
                w.end_date + timedelta(days=1)
            ).strftime("%Y-%m-%d"),

            "color": "#198754",

            "url": reverse(
                "workshop_detail",
                args=[w.pk]
            ),

            "extendedProps": {
                "event_type": "Workshop",
                "trainer": trainer_names,
                "college": str(w.college) if w.college else "",
                "department": w.departments or "",
                "status": getattr(w, "status", ""),
                "description": getattr(w, "remarks", ""),
            }
        })


    # =========================================================
    # OFFICE TRAININGS
    # =========================================================
    office_trainings = OfficeTraining.objects.prefetch_related(
        "trainers"
    ).all()

    for t in office_trainings:

        trainer_names = ", ".join(
            trainer.Name
            for trainer in t.trainers.all()
        )

        events.append({
            "id": f"office-{t.pk}",
            "title": f"🏢 {t.name}",

            "start": t.start_date.strftime("%Y-%m-%d"),
            "end": (
                t.end_date + timedelta(days=1)
            ).strftime("%Y-%m-%d"),

            "color": "#0d6efd",

            "url": reverse(
                "view_office_training",
                args=[t.pk]
            ),

            "extendedProps": {
                "event_type": "Office Training",
                "trainer": trainer_names,
                "college": "Mevi Technologies",
                "department": "",
                "status": "Scheduled",
                "description": f"Batch: {t.batch}",
                "mode": getattr(t, "mode", ""),
                "hall": getattr(t, "hall", ""),
            }
        })


    # =========================================================
    # RENDER CALENDAR
    # =========================================================
    return render(
        request,
        "calendar.html",
        {
            "events_json": json.dumps(
                events,
                default=str
            )
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
@login_required
@user_passes_test(is_superuser)
def add_calendar_event(request):

    selected_date = request.GET.get("date")
    selected_time = request.GET.get("time")

    if request.method == "POST":

        form = CalendarEventForm(request.POST)

        if form.is_valid():

            event_date = form.cleaned_data.get("date")

            # ==========================================
            # TWO-DAY BACKDATE CHECK
            # ==========================================

            if not is_within_two_day_window(event_date):

                messages.error(
                    request,
                    "You can only add events for today, "
                    "yesterday, or the day before yesterday."
                )

                return render(
                    request,
                    "calendar/add_event.html",
                    {
                        "form": form,
                        "title": "Add Calendar Event",
                    }
                )

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

            try:

                requested_date = date.fromisoformat(
                    selected_date
                )

                if is_within_two_day_window(
                    requested_date
                ):
                    initial["date"] = selected_date

            except ValueError:
                pass

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

    # ==========================================
    # EXISTING EVENT TOO OLD
    # ==========================================

    if not is_within_two_day_window(
        event.date
    ):

        messages.error(
            request,
            "This event is older than the allowed "
            "2-day editing window."
        )

        return redirect(
            "trainer_schedule"
        )

    if request.method == "POST":

        form = CalendarEventForm(
            request.POST,
            instance=event
        )

        if form.is_valid():

            new_date = form.cleaned_data.get(
                "date"
            )

            # ======================================
            # PREVENT MOVING INTO OLD DATE
            # ======================================

            if not is_within_two_day_window(
                new_date
            ):

                messages.error(
                    request,
                    "Events can only be scheduled from "
                    "the last 2 days onward."
                )

            else:

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
@require_POST
def delete_calendar_event(request, pk):

    event = get_object_or_404(
        CalendarEvent,
        pk=pk
    )

    # ==========================================
    # TWO-DAY DELETE WINDOW
    # ==========================================

    if not is_within_two_day_window(
        event.date
    ):

        messages.error(
            request,
            "This event is older than the allowed "
            "2-day deletion window."
        )

        return redirect(
            "trainer_schedule"
        )

    event_title = event.title

    event.delete()

    messages.success(
        request,
        f'"{event_title}" was deleted successfully.'
    )

    return redirect(
        "trainer_schedule"
    )

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

    # ==========================================
    # OLD EVENT CHECK
    # ==========================================

    if not is_within_two_day_window(
        event.date
    ):

        return JsonResponse(
            {
                "success": False,
                "error": (
                    "This event is older than "
                    "the 2-day editing window."
                )
            },
            status=403
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


# ============================================================
# DAILY ATTENDANCE
# ============================================================

# ============================================================
# TRAINER ATTENDANCE
# TODAY + PREVIOUS 2 DAYS
# ============================================================

@login_required
def daily_checkin(request):

    trainer = get_logged_in_trainer(request)

    if not trainer:

        messages.error(
            request,
            "Your account is not linked to a Trainer profile."
        )

        return redirect("dashboard")

    # --------------------------------------------------------
    # FULL-TIME TRAINERS ONLY
    # --------------------------------------------------------

    if not trainer.is_full_time:

        messages.error(
            request,
            "Only full-time trainers can manage attendance."
        )

        return redirect("trainer_dashboard")

    # --------------------------------------------------------
    # ALLOWED DATES
    # --------------------------------------------------------

    today, minimum_date = get_allowed_attendance_dates()

    attendance_date_raw = (
        request.POST.get("attendance_date")
        or
        request.GET.get("attendance_date")
    )

    if attendance_date_raw:

        try:

            attendance_date = date.fromisoformat(
                attendance_date_raw
            )

        except ValueError:

            messages.error(
                request,
                "Invalid attendance date."
            )

            return redirect(
                f"{reverse('daily_checkin')}?attendance_date={today}"
            )

    else:

        attendance_date = today

    # --------------------------------------------------------
    # DATE VALIDATION
    # --------------------------------------------------------

    if attendance_date < minimum_date:

        messages.error(
            request,
            "You can manage attendance only for today and the previous 2 days."
        )

        return redirect(
            f"{reverse('daily_checkin')}?attendance_date={today}"
        )

    if attendance_date > today:

        messages.error(
            request,
            "Future attendance is not allowed."
        )

        return redirect(
            f"{reverse('daily_checkin')}?attendance_date={today}"
        )

    # --------------------------------------------------------
    # GET / CREATE ATTENDANCE
    # --------------------------------------------------------

    attendance, created = (
        DailyAttendance.objects.get_or_create(
            trainer=trainer,
            date=attendance_date
        )
    )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        action = request.POST.get("action")

        # ====================================================
        # CHECK IN NOW
        # ====================================================

        if action == "check_in_now":

            if attendance.check_in:

                messages.info(
                    request,
                    "You have already checked in for this date."
                )

            else:

                now = timezone.now()

                # Safety: check-in cannot be after 8:30 PM.
                local_now = timezone.localtime(now)

                if attendance_date == today:

                    if local_now.time() >= time(20, 30):

                        messages.error(
                            request,
                            "Check-in is closed after 8:30 PM."
                        )

                    else:

                        attendance.check_in = now
                        attendance.check_out = None
                        attendance.save(
                            update_fields=[
                                "check_in",
                                "check_out"
                            ]
                        )

                        messages.success(
                            request,
                            "You are successfully checked in."
                        )

                else:

                    messages.error(
                        request,
                        "For previous dates, enter the actual check-in time."
                    )

        # ====================================================
        # CHECK IN AT SPECIFIC TIME
        # ====================================================

        elif action == "check_in_time":

            check_in_raw = request.POST.get("check_in_time")

            if attendance.check_in:

                messages.info(
                    request,
                    "Check-in time already exists for this date."
                )

            elif not check_in_raw:

                messages.error(
                    request,
                    "Please enter a check-in time."
                )

            else:

                try:

                    selected_time = time.fromisoformat(
                        check_in_raw
                    )

                    check_in_datetime = make_local_datetime(
                        attendance_date,
                        selected_time
                    )

                    # Do not allow future time.
                    if (
                        attendance_date == today
                        and check_in_datetime > timezone.now()
                    ):

                        messages.error(
                            request,
                            "Check-in time cannot be in the future."
                        )

                    elif selected_time >= time(20, 30):

                        messages.error(
                            request,
                            "Check-in must be before 8:30 PM."
                        )

                    else:

                        attendance.check_in = check_in_datetime
                        attendance.check_out = None

                        attendance.save(
                            update_fields=[
                                "check_in",
                                "check_out"
                            ]
                        )

                        messages.success(
                            request,
                            (
                                f"Check-in recorded at "
                                f"{selected_time.strftime('%I:%M %p')}."
                            )
                        )

                except ValueError:

                    messages.error(
                        request,
                        "Invalid check-in time."
                    )

        # ====================================================
        # CHECK OUT NOW
        # ====================================================

        elif action == "check_out_now":

            if not attendance.check_in:

                messages.error(
                    request,
                    "You must check in before checking out."
                )

            elif attendance.check_out:

                messages.info(
                    request,
                    "You have already checked out."
                )

            else:

                now = timezone.now()

                local_now = timezone.localtime(now)

                # Today cannot checkout after 8:30 PM manually.
                if attendance_date == today:

                    if local_now.time() >= time(20, 30):

                        # At/after 8:30 PM, use automatic checkout time.
                        checkout_datetime = make_local_datetime(
                            today,
                            time(20, 30)
                        )

                    else:

                        checkout_datetime = now

                else:

                    messages.error(
                        request,
                        "For previous dates, enter the actual checkout time."
                    )

                    checkout_datetime = None

                if checkout_datetime:

                    if checkout_datetime <= attendance.check_in:

                        messages.error(
                            request,
                            "Checkout time must be after check-in time."
                        )

                    else:

                        attendance.check_out = checkout_datetime

                        attendance.save(
                            update_fields=[
                                "check_out"
                            ]
                        )

                        messages.success(
                            request,
                            "You have successfully checked out."
                        )

        # ====================================================
        # CHECK OUT AT SPECIFIC TIME
        # ====================================================

        elif action == "check_out_time":

            check_out_raw = request.POST.get(
                "check_out_time"
            )

            if not attendance.check_in:

                messages.error(
                    request,
                    "You must enter check-in before checkout."
                )

            elif attendance.check_out:

                messages.info(
                    request,
                    "Checkout has already been recorded."
                )

            elif not check_out_raw:

                messages.error(
                    request,
                    "Please enter a checkout time."
                )

            else:

                try:

                    selected_time = time.fromisoformat(
                        check_out_raw
                    )

                    # ------------------------------------------------
                    # AUTO CHECKOUT LIMIT
                    # ------------------------------------------------

                    if selected_time > time(20, 30):

                        selected_time = time(20, 30)

                        messages.info(
                            request,
                            "Checkout time was limited to 8:30 PM."
                        )

                    checkout_datetime = make_local_datetime(
                        attendance_date,
                        selected_time
                    )

                    if (
                        attendance_date == today
                        and checkout_datetime > timezone.now()
                    ):

                        messages.error(
                            request,
                            "Checkout time cannot be in the future."
                        )

                    elif checkout_datetime <= attendance.check_in:

                        messages.error(
                            request,
                            "Checkout time must be after check-in time."
                        )

                    else:

                        attendance.check_out = checkout_datetime

                        attendance.save(
                            update_fields=[
                                "check_out"
                            ]
                        )

                        messages.success(
                            request,
                            (
                                f"Checkout recorded at "
                                f"{selected_time.strftime('%I:%M %p')}."
                            )
                        )

                except ValueError:

                    messages.error(
                        request,
                        "Invalid checkout time."
                    )

        # ====================================================
        # UNKNOWN ACTION
        # ====================================================

        else:

            messages.error(
                request,
                "Invalid attendance action."
            )

        return redirect(
            f"{reverse('daily_checkin')}?attendance_date={attendance_date}"
        )

    # --------------------------------------------------------
    # LEARNING FOR SELECTED DATE
    # --------------------------------------------------------

    learning = (
        DailyLearning.objects
        .filter(
            trainer=trainer,
            date=attendance_date
        )
        .first()
    )

    # --------------------------------------------------------
    # TODAY / PREVIOUS DATE FLAGS
    # --------------------------------------------------------

    is_today = attendance_date == today
    is_previous_date = attendance_date < today

    # --------------------------------------------------------
    # WORKED HOURS
    # --------------------------------------------------------

    worked_hours = None

    if attendance.check_in and attendance.check_out:

        seconds = (
            attendance.check_out
            - attendance.check_in
        ).total_seconds()

        worked_hours = round(
            seconds / 3600,
            2
        )

    # --------------------------------------------------------
    # RENDER
    # --------------------------------------------------------

    return render(
        request,
        "todo/daily_checkin.html",
        {
            "trainer": trainer,
            "attendance": attendance,
            "attendance_date": attendance_date,
            "today": today,
            "minimum_date": minimum_date,
            "is_today": is_today,
            "is_previous_date": is_previous_date,
            "worked_hours": worked_hours,
            "learning": learning,
        }
    )
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
# ============================================================
# ATTENDANCE HELPERS
# ============================================================

def get_logged_in_trainer(request):
    """
    Get Trainer profile connected to the logged-in user.
    Falls back to trainer email if user relation is missing.
    """

    trainer = (
        Trainer.objects
        .filter(user=request.user)
        .first()
    )

    if not trainer:
        trainer = (
            Trainer.objects
            .filter(email__iexact=request.user.email)
            .first()
        )

    return trainer


def get_allowed_attendance_dates():
    """
    Returns:
        today
        minimum_date = today - 2 days

    Trainers can manage:
        today
        yesterday
        day before yesterday
    """

    today = timezone.localdate()

    minimum_date = today - timedelta(days=2)

    return today, minimum_date

from datetime import date, datetime, time, timedelta
def make_local_datetime(selected_date, selected_time):
    """
    Convert selected date + time into timezone-aware datetime.
    """

    naive_datetime = datetime.combine(
        selected_date,
        selected_time
    )

    return timezone.make_aware(
        naive_datetime,
        timezone.get_current_timezone()
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
# ============================================================
# DAILY LEARNING
# TODAY + PREVIOUS 2 DAYS
# ============================================================

@login_required
def add_daily_learning(request):

    trainer = get_logged_in_trainer(request)

    if not trainer:

        messages.error(
            request,
            "Your account is not linked to a Trainer profile."
        )

        return redirect("dashboard")

    if not trainer.is_full_time:

        messages.error(
            request,
            "Only full-time trainers can add daily learning."
        )

        return redirect("trainer_dashboard")

    today, minimum_date = get_allowed_attendance_dates()

    # --------------------------------------------------------
    # SELECT DATE
    # --------------------------------------------------------

    date_raw = (
        request.POST.get("learning_date")
        or
        request.GET.get("learning_date")
    )

    if date_raw:

        try:

            learning_date = date.fromisoformat(
                date_raw
            )

        except ValueError:

            messages.error(
                request,
                "Invalid learning date."
            )

            return redirect("daily_checkin")

    else:

        learning_date = today

    # --------------------------------------------------------
    # DATE VALIDATION
    # --------------------------------------------------------

    if (
        learning_date < minimum_date
        or learning_date > today
    ):

        messages.error(
            request,
            "Learning can only be added for today or the previous 2 days."
        )

        return redirect("daily_checkin")

    # --------------------------------------------------------
    # GET / CREATE
    # --------------------------------------------------------

    learning, created = (
        DailyLearning.objects.get_or_create(
            trainer=trainer,
            date=learning_date,
            defaults={
                "learning": ""
            }
        )
    )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        form = DailyLearningForm(
            request.POST,
            instance=learning
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                (
                    f"Learning saved for "
                    f"{learning_date.strftime('%d %B %Y')}."
                )
            )

            return redirect(
                f"{reverse('daily_checkin')}?attendance_date={learning_date}"
            )

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
            "minimum_date": minimum_date,
            "learning_date": learning_date,
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

# =====================================================
# TWO-DAY BACKDATE PERMISSION
# =====================================================

def is_within_two_day_window(target_date):
    """
    Allows:
        Today
        Yesterday
        Day before yesterday
        Any future date

    Blocks:
        Anything older than 2 days
    """

    today = timezone.localdate()

    minimum_date = today - timedelta(days=2)

    return target_date >= minimum_date

# ============================================================
# ADD TODAY TASK
# ============================================================

@login_required
def add_today_task(request):

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

    if not trainer:

        messages.error(
            request,
            "Your account is not linked to a Trainer profile."
        )

        return redirect("dashboard")

    # ============================================================
    # FULL-TIME TRAINERS
    # ============================================================

    if not trainer.is_full_time:

        messages.error(
            request,
            "Only full-time trainers can add daily work."
        )

        return redirect("trainer_dashboard")

    # ============================================================
    # DATES
    # ============================================================

    today = timezone.localdate()

    minimum_date = today - timedelta(days=2)

    # ============================================================
    # GET WORK DATE
    # ============================================================

    work_date_raw = request.POST.get(
        "work_date"
    )

    if not work_date_raw:

        work_date_raw = request.POST.get(
            "attendance_date"
        )

    if not work_date_raw:

        work_date_raw = request.GET.get(
            "work_date"
        )

    if not work_date_raw:

        work_date_raw = request.GET.get(
            "attendance_date"
        )

    # ============================================================
    # DEFAULT = TODAY
    # ============================================================

    if not work_date_raw:

        work_date = today

    else:

        try:

            work_date = date.fromisoformat(
                work_date_raw
            )

        except ValueError:

            messages.error(
                request,
                "Invalid work date."
            )

            return redirect(
                f"{reverse('trainer_dashboard')}?attendance_date={today}"
            )

    # ============================================================
    # ONLY LAST 3 DAYS
    # ============================================================

    if (
        work_date < minimum_date
        or work_date > today
    ):

        messages.error(
            request,
            "Work can only be added for today, "
            "yesterday, or the day before yesterday."
        )

        return redirect(
            f"{reverse('trainer_dashboard')}?attendance_date={today}"
        )

    # ============================================================
    # ATTENDANCE FOR SELECTED DATE
    # ============================================================

    attendance = DailyAttendance.objects.filter(
        trainer=trainer,
        date=work_date
    ).first()

    # ============================================================
    # MUST CHECK IN FOR THAT DATE
    # ============================================================

    if not attendance or not attendance.check_in:

        messages.error(
            request,
            (
                f"Please check in for "
                f"{work_date.strftime('%d %b %Y')} "
                f"before adding work."
            )
        )

        return redirect(
            f"{reverse('trainer_dashboard')}?attendance_date={work_date.isoformat()}"
        )

    # ============================================================
    # AFTER CHECKOUT
    # ============================================================

    if attendance.check_out:

        messages.error(
            request,
            (
                f"You have already checked out for "
                f"{work_date.strftime('%d %b %Y')}. "
                f"New work cannot be added."
            )
        )

        return redirect(
            f"{reverse('trainer_dashboard')}?attendance_date={work_date.isoformat()}"
        )

    # ============================================================
    # POST
    # ============================================================

    if request.method != "POST":

        return redirect(
            f"{reverse('trainer_dashboard')}?attendance_date={work_date.isoformat()}"
        )

    # ============================================================
    # FORM DATA
    # ============================================================

    task_text = request.POST.get(
        "task",
        ""
    ).strip()

    description = request.POST.get(
        "description",
        ""
    ).strip()

    category = request.POST.get(
        "category",
        "other"
    )

    priority = request.POST.get(
        "priority",
        "medium"
    )

    estimated_hours_raw = request.POST.get(
        "estimated_hours",
        "1"
    )

    # ============================================================
    # TASK REQUIRED
    # ============================================================

    if not task_text:

        messages.error(
            request,
            "Please enter what you worked on."
        )

        return redirect(
            f"{reverse('trainer_dashboard')}?attendance_date={work_date.isoformat()}"
        )

    # ============================================================
    # VALID CATEGORY
    # ============================================================

    valid_categories = dict(
        TodoTask.CATEGORY_CHOICES
    )

    if category not in valid_categories:

        category = "other"

    # ============================================================
    # VALID PRIORITY
    # ============================================================

    valid_priorities = dict(
        TodoTask.PRIORITY_CHOICES
    )

    if priority not in valid_priorities:

        priority = "medium"

    # ============================================================
    # HOURS
    # ============================================================

    try:

        estimated_hours = Decimal(
            estimated_hours_raw
        )

    except (ValueError, TypeError, InvalidOperation):

        estimated_hours = Decimal("1")

    if estimated_hours < 0:

        estimated_hours = Decimal("1")

    # ============================================================
    # CREATE WORK
    # ============================================================

    TodoTask.objects.create(

        trainer=trainer,

        task=task_text,

        description=description,

        category=category,

        priority=priority,

        estimated_hours=estimated_hours,

        for_date=work_date,

        status="in_progress",

        is_done=False,
    )

    # ============================================================
    # SUCCESS
    # ============================================================

    messages.success(
        request,
        (
            f'Work "{task_text}" was added for '
            f'{work_date.strftime("%d %b %Y")}.'
        )
    )

    # ============================================================
    # KEEP SAME DATE SELECTED
    # ============================================================

    return redirect(
        f"{reverse('trainer_dashboard')}?attendance_date={work_date.isoformat()}"
    )