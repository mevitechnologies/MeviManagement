from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta, date
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Workshop, TodoTask,College

from .models import (
    Workshop, Trainer, FollowUp,
    TodoTask, SubTask, OfficeTraining,College
)
from .forms import (
    WorkshopForm, TrainerForm, FollowUpForm,
    TodoTaskForm, SubTaskForm, SubTaskFormSet,
    OfficeTrainingForm,CollegeForm
)

# =====================================================
# HELPERS
# =====================================================

def is_admin(user):
    return user.is_staff or user.is_superuser


# =====================================================
# AUTH
# =====================================================

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username").strip().lower()
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            # Redirect safely
            next_url = request.GET.get("next")
            return redirect(next_url or "dashboard")

        else:
            messages.error(
                request,
                "❌ Invalid email or password"
            )

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
    today = timezone.now().date()

    # ===============================
    # WORKSHOP STATUS COLUMNS
    # ===============================
    status_columns = [
        ("Tentative", "tentative", "warning"),
        ("Fixed", "fixed", "success"),
        ("Postponed", "postponed", "info"),
        ("Cancelled", "cancelled", "secondary"),
        ("Completed", "completed", "dark"),
    ]

    columns = []
    for label, status, color in status_columns:
        columns.append({
            "label": label,
            "color": color,
            "workshops": Workshop.objects.filter(
                status=status
            ).order_by("start_date")
        })

    # ===============================
    # TODAY TASKS (FOR ALL USERS)
    # ===============================
    if request.user.is_staff:
        today_tasks = TodoTask.objects.filter(for_date=today)
    else:
        trainer = getattr(request.user, "trainer", None)
        today_tasks = (
            TodoTask.objects.filter(for_date=today, trainer=trainer)
            if trainer else TodoTask.objects.none()
        )

    return render(request, "dashboard.html", {
        "status_columns": columns,
        "today": today,
        "today_tasks": today_tasks,
    })


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
    return render(
        request,
        "workshop_detail.html",
        {"workshop": get_object_or_404(Workshop, pk=pk)}
    )


@login_required
@user_passes_test(is_admin)
def add_workshop(request):
    form = WorkshopForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Workshop added successfully")
        return redirect("workshop_list")
    return render(request, "add_workshop.html", {"form": form})


@login_required
@user_passes_test(is_admin)
def edit_workshop(request, pk):
    workshop = get_object_or_404(Workshop, pk=pk)
    form = WorkshopForm(request.POST or None, instance=workshop)
    if form.is_valid():
        form.save()
        messages.success(request, "Workshop updated")
        return redirect("workshop_list")
    return render(request, "edit_workshop.html", {"form": form})


@login_required
@user_passes_test(is_admin)
def delete_workshop(request, pk):
    get_object_or_404(Workshop, pk=pk).delete()
    messages.success(request, "Workshop deleted")
    return redirect("workshop_list")


@login_required
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
def trainer_list(request):
    trainers = Trainer.objects.all().order_by("Name")
    paginator = Paginator(trainers, 6)
    return render(request, "trainer_list.html", {
        "trainers": paginator.get_page(request.GET.get("page"))
    })


@login_required
@user_passes_test(is_admin)
def add_trainer(request):
    form = TrainerForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect("trainer_list")
    return render(request, "add_trainer.html", {"form": form})


@login_required
@user_passes_test(is_admin)
def edit_trainer(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    form = TrainerForm(request.POST or None, instance=trainer)
    if form.is_valid():
        form.save()
        return redirect("trainer_list")
    return render(request, "edit_trainer.html", {"form": form})


@login_required
@user_passes_test(is_admin)
def delete_trainer(request, pk):
    get_object_or_404(Trainer, pk=pk).delete()
    return redirect("trainer_list")


# =====================================================
# ADMIN TASK DASHBOARD
# =====================================================

@login_required
@user_passes_test(is_admin)
def admin_task_dashboard(request):
    today = timezone.now().date()
    one_week_ago = today - timedelta(days=7)

    tasks = TodoTask.objects.filter(
        for_date__gte=one_week_ago
    ).select_related("trainer")

    form = TodoTaskForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("admin_task_dashboard")

    return render(request, "todo/admin_dashboard.html", {
        "form": form,
        "grouped_tasks": {
            "pending": tasks.filter(status="pending"),
            "in_progress": tasks.filter(status="in_progress"),
            "completed": tasks.filter(status="completed"),
        }
    })


@login_required
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
def toggle_subtask_done(request, task_id, subtask_id):
    sub = get_object_or_404(SubTask, id=subtask_id, parent_task_id=task_id)
    sub.is_completed = not sub.is_completed
    sub.save()
    return redirect("task_detail", task_id=task_id)


@login_required
@user_passes_test(is_admin)
def delete_task(request, task_id):
    get_object_or_404(TodoTask, id=task_id).delete()
    return redirect("task_history")

@login_required
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
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
    trainer = getattr(request.user, "trainer", None)
    if not trainer:
        messages.error(request, "Trainer profile not found")
        return redirect("dashboard")

    tasks = TodoTask.objects.filter(trainer=trainer)

    return render(request, "todo/trainer_dashboard.html", {
        "trainer": trainer,
        "tasks": tasks
    })

@login_required
def trainer_schedule(request):
    """
    Shows trainer-wise workshop schedule.
    View-only for all users.
    Highlights overlapping workshops.
    """
    trainer_workshops = []

    trainers = Trainer.objects.all().order_by("Name")

    for trainer in trainers:
        workshops = Workshop.objects.filter(
            assigned_trainers=trainer,
            status="fixed"
        ).order_by("start_date")

        overlapping_ids = set()
        workshop_list = list(workshops)

        for i in range(len(workshop_list)):
            for j in range(i + 1, len(workshop_list)):
                w1 = workshop_list[i]
                w2 = workshop_list[j]
                if (
                    w1.start_date <= w2.end_date
                    and w2.start_date <= w1.end_date
                ):
                    overlapping_ids.add(w1.id)
                    overlapping_ids.add(w2.id)

        trainer_workshops.append({
            "trainer": trainer,
            "workshops": workshop_list,
            "overlapping_ids": overlapping_ids
        })

    return render(request, "trainer_schedule.html", {
        "trainer_workshops": trainer_workshops
    })

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

def calendar_view(request):
    events = []
    for w in Workshop.objects.filter(status="fixed"):
        events.append({
            "title": w.title,
            "start": w.start_date.isoformat(),
            "end": (w.end_date + timedelta(days=1)).isoformat()
        })
    return render(request, "calendar.html", {"events": events})

@login_required
def trainer_dashboard(request):
    """
    Trainer dashboard – view only.
    """
    trainer = Trainer.objects.filter(email=request.user.email).first()

    if not trainer:
        messages.error(request, "Trainer profile not found.")
        return redirect("dashboard")

    tasks = TodoTask.objects.filter(trainer=trainer).order_by("-for_date")

    return render(request, "todo/trainer_dashboard.html", {
        "trainer": trainer,
        "tasks": tasks,
    })

# =====================================================
# OFFICE TRAININGS
# =====================================================

@login_required
def office_training_list(request):
    """
    View all office trainings.
    Admin: full access
    Others: view only
    """
    today = timezone.now().date()

    trainings = OfficeTraining.objects.all().order_by("-start_date")

    ongoing = trainings.filter(start_date__lte=today, end_date__gte=today)
    upcoming = trainings.filter(start_date__gt=today)
    completed = trainings.filter(end_date__lt=today)

    return render(request, "office_training/list.html", {
        "ongoing": ongoing,
        "upcoming": upcoming,
        "completed": completed,
        "today": today,
        "is_admin": request.user.is_staff,
    })


@login_required
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
def delete_office_training(request, pk):
    training = get_object_or_404(OfficeTraining, pk=pk)
    training.delete()
    messages.success(request, "Office training deleted.")
    return redirect("office_training_list")


@login_required
def view_office_training(request, pk):
    training = get_object_or_404(OfficeTraining, pk=pk)
    return render(request, "office_training/view.html", {
        "training": training
    })
# =====================================================
# TASK HISTORY (ADMIN ONLY)
# =====================================================

@login_required
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
def add_college(request):
    form = CollegeForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "College added successfully")
        return redirect("college_list")
    return render(request, "college/form.html", {"form": form, "title": "Add College"})


@login_required
@user_passes_test(is_admin)
def edit_college(request, pk):
    college = get_object_or_404(College, pk=pk)
    form = CollegeForm(request.POST or None, instance=college)
    if form.is_valid():
        form.save()
        messages.success(request, "College updated successfully")
        return redirect("college_list")
    return render(request, "college/form.html", {"form": form, "title": "Edit College"})


@login_required
@user_passes_test(is_admin)
def delete_college(request, pk):
    college = get_object_or_404(College, pk=pk)
    college.delete()
    messages.success(request, "College deleted")
    return redirect("college_list")
