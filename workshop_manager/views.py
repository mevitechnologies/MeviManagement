from django.shortcuts import render, get_object_or_404, redirect
from .models import Workshop, Trainer, FollowUp
from .forms import TrainerForm, WorkshopForm
from datetime import date
from collections import defaultdict
from django.forms import modelformset_factory
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.admin.views.decorators import staff_member_required
from .forms import TodoTaskForm, SubTaskForm, SubTaskFormSet
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Trainer, Workshop
from .forms import TrainerForm, WorkshopForm
from .models import FollowUp
from .forms import FollowUpForm
from django.core.paginator import Paginator
from datetime import timedelta
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.timezone import now
from django.http import HttpResponseRedirect
from django.urls import reverse
from itertools import chain
from .models import OfficeTraining
from .models import TodoTask, Trainer
from .forms import TodoTaskForm
from .forms import OfficeTrainingForm
from .models import Trainer, TodoTask, SubTask
from .forms import TodoTaskForm, SubTaskForm
# views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


@login_required
def update_status(request, pk, status):
    workshop = get_object_or_404(Workshop, pk=pk)
    workshop.status = status
    workshop.save()
    messages.success(request, f"Workshop '{workshop.title}' status updated to '{status}'")
    return redirect('dashboard')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials or not a superuser'})
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    today = now().date()

    status_columns = [
        {"label": "Tentative", "workshops": Workshop.objects.filter(status='tentative'), "color": "warning"},
        {"label": "Fixed", "workshops": Workshop.objects.filter(status='fixed'), "color": "success"},
        {"label": "Postponed", "workshops": Workshop.objects.filter(status='postponed'), "color": "info"},
        {"label": "Cancelled", "workshops": Workshop.objects.filter(status='cancelled'), "color": "secondary"},
        {"label": "Completed", "workshops": Workshop.objects.filter(status='completed'), "color": "dark"},
    ]

    ongoing = Workshop.objects.filter(start_date__lte=today, end_date__gte=today)
    upcoming = Workshop.objects.filter(start_date__gt=today)
    past = Workshop.objects.filter(end_date__lt=today)

    all_workshops = list(chain(ongoing, upcoming, past))
    followups = FollowUp.objects.select_related('workshop').all()
    followups_due = FollowUp.objects.filter(due_date__lte=today, is_completed=False)

    return render(request, "dashboard.html", {
        "status_columns": status_columns,
        "ongoing": ongoing,
        "upcoming": upcoming,
        "past": past,
        "followups_due": followups_due,
        "calendar_followups": followups,
        "calendar_workshops": all_workshops,
        "today": today,  # ✅ Add this line
    })
@login_required
def follow_ups(request):
    today = date.today()
    followups = FollowUp.objects.filter(is_completed=False, due_date__lte=today)
    return render(request, 'followups.html', {'followups': followups})

@login_required
def availability_json(request):
    events = []
    trainers = Trainer.objects.all()
    
    for trainer in trainers:
        workshops = Workshop.objects.filter(assigned_trainers=trainer, status='fixed')
        for workshop in workshops:
            events.append({
                "title": f"{workshop.title} – {trainer.Name}",
                "start": workshop.start_date.isoformat(),
                "end": (workshop.end_date + timedelta(days=1)).isoformat(),  # FullCalendar needs exclusive end
            })

    return JsonResponse(events, safe=False)


# Trainer views
@login_required
def trainer_list(request):
    query = request.GET.get('q')
    trainers = Trainer.objects.all()
    if query:
        trainers = trainers.filter(user__first_name__icontains=query)

    paginator = Paginator(trainers, 5)
    page = request.GET.get('page')
    trainers = paginator.get_page(page)

    return render(request, 'trainer_list.html', {'trainers': trainers})
@login_required
def add_trainer(request):
    if request.method == 'POST':
        form = TrainerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('trainer_list')
    else:
        form = TrainerForm()
    return render(request, 'add_trainer.html', {'form': form})
@login_required
def edit_trainer(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    form = TrainerForm(request.POST or None, request.FILES or None, instance=trainer)
    if form.is_valid():
        form.save()
        return redirect('trainer_list')
    return render(request, 'edit_trainer.html', {'form': form, 'trainer': trainer})

# Workshop views
@login_required
def workshop_list(request):
    query = request.GET.get('q', '')
    workshops = Workshop.objects.all()

    if query:
        workshops = workshops.filter(title__icontains=query)

    paginator = Paginator(workshops, 5)  # 5 workshops per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'workshops': page_obj,  # This variable name must match the template
        'query': query
    }
    return render(request, 'workshop_list.html', context)


@login_required
def add_workshop(request):
    form = WorkshopForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('workshop_list')
    return render(request, 'add_workshop.html', {'form': form})

@login_required
def edit_workshop(request, pk):
    workshop = get_object_or_404(Workshop, pk=pk)
    form = WorkshopForm(request.POST or None, request.FILES or None, instance=workshop)
    if form.is_valid():
        form.save()
        return redirect('workshop_list')
    return render(request, 'edit_workshop.html', {'form': form, 'workshop': workshop})

@login_required
def delete_trainer(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    trainer.delete()
    messages.success(request, "Trainer deleted successfully.")
    return redirect('trainer_list')
@login_required
def delete_workshop(request, pk):
    workshop = get_object_or_404(Workshop, pk=pk)
    workshop.delete()
    messages.success(request, "Workshop deleted successfully.")
    return redirect('workshop_list')

@login_required
def workshop_detail(request, pk):
    workshop = get_object_or_404(Workshop, pk=pk)
    return render(request, 'workshop_detail.html', {'workshop': workshop})

@login_required
def follow_ups(request):
    followups = FollowUp.objects.all()
    return render(request, 'followups.html', {'followups': followups})
@login_required
def add_followup(request):
    form = FollowUpForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('follow_ups')
    return render(request, 'followup_form.html', {'form': form, 'title': 'Add Follow-Up'})
@login_required
def edit_followup(request, pk):
    followup = get_object_or_404(FollowUp, pk=pk)
    form = FollowUpForm(request.POST or None, instance=followup)
    if form.is_valid():
        form.save()
        return redirect('follow_ups')
    return render(request, 'followup_form.html', {'form': form, 'title': 'Edit Follow-Up'})
@login_required
def delete_followup(request, pk):
    followup = get_object_or_404(FollowUp, pk=pk)
    followup.delete()
    return redirect('follow_ups')


@login_required
def calendar_view(request):
    events = []

    trainers = Trainer.objects.all()
    for trainer in trainers:
        workshops = Workshop.objects.filter(assigned_trainers=trainer, status='fixed')
        for workshop in workshops:
            events.append({
                "title": f"{workshop.title} – {trainer.Name}",
                "start": workshop.start_date.isoformat(),
                "end": (workshop.end_date + timedelta(days=1)).isoformat(),
            })

    return render(request, 'calendar.html', {'events': events})
@login_required
def trainer_schedule(request):
    trainer_workshops = []

    for trainer in Trainer.objects.all():
        workshops = Workshop.objects.filter(assigned_trainers=trainer, status='fixed').order_by('start_date')

        # Check for overlapping workshops
        overlapping_ids = set()
        workshop_list = list(workshops)

        for i in range(len(workshop_list)):
            for j in range(i + 1, len(workshop_list)):
                w1 = workshop_list[i]
                w2 = workshop_list[j]
                if (w1.start_date <= w2.end_date) and (w2.start_date <= w1.end_date):
                    overlapping_ids.add(w1.id)
                    overlapping_ids.add(w2.id)

        trainer_workshops.append({
            'trainer': trainer,
            'workshops': workshop_list,
            'overlapping_ids': overlapping_ids
        })

    return render(request, 'trainer_schedule.html', {
        'trainer_workshops': trainer_workshops
    })


def office_training_list(request):
    today = date.today()
    trainings = OfficeTraining.objects.all()
    ongoing = trainings.filter(start_date__lte=today, end_date__gte=today)
    scheduled = trainings.filter(start_date__gt=today)
    past = trainings.filter(end_date__lt=today)

    context = {
        'ongoing': ongoing,
        'scheduled': scheduled,
        'past': past,
        'calendar_trainings': trainings,
        'today': today,
    }
    return render(request, 'office_training/list.html', context)

def add_office_training(request):
    if request.method == 'POST':
        form = OfficeTrainingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('office_training_list')
    else:
        form = OfficeTrainingForm()
    return render(request, 'office_training/form.html', {'form': form})

def edit_office_training(request, pk):
    training = get_object_or_404(OfficeTraining, pk=pk)
    if request.method == 'POST':
        form = OfficeTrainingForm(request.POST, instance=training)
        if form.is_valid():
            form.save()
            return redirect('office_training_list')
    else:
        form = OfficeTrainingForm(instance=training)
    return render(request, 'office_training/form.html', {'form': form})

def delete_office_training(request, pk):
    training = get_object_or_404(OfficeTraining, pk=pk)
    training.delete()
    return redirect('office_training_list')

def view_office_training(request, pk):
    training = get_object_or_404(OfficeTraining, pk=pk)
    return render(request, 'office_training/view.html', {'training': training})

# ✅ Only Admin/Superuser access
# 🧩 Admin Task Board (Scrum View)
@user_passes_test(lambda u: u.is_staff)
@login_required
def admin_task_dashboard(request):
    """Show tasks from the past 7 days only"""
    today = timezone.now().date()
    one_week_ago = today - timedelta(days=7)

    # Get tasks within the past week
    tasks = TodoTask.objects.filter(for_date__gte=one_week_ago).select_related('trainer').order_by('-for_date', '-priority')

    # Handle Quick Add Task
    if request.method == 'POST' and 'add_task' in request.POST:
        form = TodoTaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Task assigned successfully!")
            return redirect('admin_task_dashboard')
        else:
            messages.error(request, "⚠️ Please fix the errors.")
    else:
        form = TodoTaskForm()

    grouped_tasks = {
        'pending': tasks.filter(status='pending'),
        'in_progress': tasks.filter(status='in_progress'),
        'completed': tasks.filter(status='completed'),
    }

    return render(request, 'todo/admin_dashboard.html', {
        'form': form,
        'grouped_tasks': grouped_tasks,
        'today': today,
    })

# 🔄 Change Task Status (Pending → In Progress → Completed)
@login_required
def change_task_status(request, task_id):
    task = get_object_or_404(TodoTask, id=task_id)
    status_cycle = ['pending', 'in_progress', 'completed']
    next_status = status_cycle[(status_cycle.index(task.status) + 1) % len(status_cycle)]
    task.status = next_status
    task.save()
    messages.info(request, f"🔁 Status changed to {task.get_status_display()}")
    return redirect('admin_task_dashboard')


# ➕ Add Subtask to a Task

# 👩‍🏫 Trainer Dashboard
@login_required
def trainer_dashboard(request):
    """
    Trainer’s personal dashboard showing only their own tasks and subtasks.
    Trainers can add subtasks under their assigned tasks.
    """
    trainer = getattr(request.user, 'trainer', None)
    if not trainer:
        messages.error(request, "No trainer profile found.")
        return redirect('dashboard')

    today = timezone.now().date()
    tasks = TodoTask.objects.filter(trainer=trainer).order_by('-for_date')

    # Add Subtask Inline
    if request.method == 'POST' and 'add_subtask' in request.POST:
        parent_id = request.POST.get('parent_task_id')
        parent = get_object_or_404(TodoTask, id=parent_id, trainer=trainer)
        form = SubTaskForm(request.POST)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.parent_task = parent
            sub.save()
            messages.success(request, "✅ Subtask added successfully!")
            return redirect('trainer_dashboard')
    else:
        form = SubTaskForm()

    return render(request, 'todo/trainer_dashboard.html', {
        'trainer': trainer,
        'tasks': tasks,
        'form': form,
        'today': today,
    })


# 🕓 Task History (Admin View)
@login_required
@user_passes_test(lambda u: u.is_staff)
def task_history(request):
    """Show tasks older than 7 days with filtering"""
    today = timezone.now().date()
    one_week_ago = today - timedelta(days=7)

    # Fetch tasks older than 7 days
    tasks = TodoTask.objects.filter(for_date__lt=one_week_ago).select_related('trainer')

    # Fetch all trainers for dropdown
    trainers = Trainer.objects.all().order_by('Name')

    # --- Filters ---
    query_trainer = request.GET.get('trainer')
    query_date = request.GET.get('date')
    query_priority = request.GET.get('priority')

    if query_trainer:
        tasks = tasks.filter(trainer_id=query_trainer)

    if query_date:
        tasks = tasks.filter(for_date=query_date)

    if query_priority:
        tasks = tasks.filter(priority=query_priority)

    # Sort tasks by most recent date first
    tasks = tasks.order_by('-for_date')

    return render(request, 'todo/task_history.html', {
        'tasks': tasks,
        'trainers': trainers,
        'query_trainer': query_trainer,
        'query_date': query_date,
        'query_priority': query_priority,
    })

# ✅ Mark Task as Done
@login_required
def mark_task_done(request, trainer_id, task_id):
    """
    Marks a task as completed.
    """
    task = get_object_or_404(TodoTask, id=task_id, trainer_id=trainer_id)
    task.status = 'completed'
    task.is_done = True
    task.save()
    messages.success(request, "✅ Task marked as completed.")
    return redirect('admin_task_dashboard')


# 🔁 Undo Task (Mark as Not Done)
@login_required
def undo_task_done(request, trainer_id, task_id):
    """
    Reverts a completed task back to pending.
    """
    task = get_object_or_404(TodoTask, id=task_id, trainer_id=trainer_id)
    task.status = 'pending'
    task.is_done = False
    task.save()
    messages.info(request, "↩️ Task reverted to pending.")
    return redirect('admin_task_dashboard')

# ✅ Define SubTaskFormSet (if not already in forms.py)


@login_required
@user_passes_test(lambda u: u.is_staff)
def add_task_page(request):
    """Create a full task with title, description, deadline, subtasks, and priority"""

    if request.method == "POST":
        form = TodoTaskForm(request.POST)
        formset = SubTaskFormSet(request.POST, prefix='subtasks')

        if form.is_valid() and formset.is_valid():
            task = form.save(commit=True)

            # ✅ Save all subtasks linked to this task
            for sub_form in formset:
                title = sub_form.cleaned_data.get('title')
                if title:
                    sub = sub_form.save(commit=False)
                    sub.parent_task = task
                    sub.save()

            messages.success(request, "✅ Task created successfully with subtasks!")
            return redirect('admin_task_dashboard')  # ✅ Redirect to dashboard
        else:
            print("❌ FORM ERRORS:", form.errors)
            print("❌ SUBTASK ERRORS:", formset.errors)
            messages.error(request, "⚠️ Please fix the form errors below.")
    else:
        form = TodoTaskForm()
        formset = SubTaskFormSet(queryset=SubTask.objects.none(), prefix='subtasks')

    return render(request, 'todo/add_task.html', {
        'form': form,
        'subtask_formset': formset,
    })
# 🧩 Toggle Subtask (Done / Not Done)
def add_subtask(request, task_id):
    parent = get_object_or_404(TodoTask, id=task_id)
    
    if request.method == "POST":
        form = SubTaskForm(request.POST)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.parent_task = parent  # ✅ link correctly
            sub.save()
            messages.success(request, "🧩 Subtask added successfully!")
            return redirect('task_detail', task_id=task_id)
    else:
        form = SubTaskForm()
    
    return render(request, 'todo/add_subtask.html', {'form': form, 'task': parent})

@login_required
def task_detail(request, task_id):
    # ✅ Fetch main task
    task = get_object_or_404(TodoTask, id=task_id)

    # ✅ Fetch subtasks linked to this task
    subtasks = task.subtasks.all().order_by('id')  # uses related_name='subtasks'

    # ✅ Calculate progress dynamically
    total = subtasks.count()
    done = subtasks.filter(is_completed=True).count()
    progress = round((done / total) * 100, 1) if total > 0 else 0

    # ✅ Attach computed attributes (for use in template)
    task.total_subtasks = total
    task.completed_subtasks = done
    task.progress = progress

    # ✅ Render page
    return render(request, 'todo/task_detail.html', {
        'task': task,
        'subtasks': subtasks,
    })

@login_required
def toggle_subtask_done(request, task_id, subtask_id, trainer_id=None):
    subtask = get_object_or_404(SubTask, id=subtask_id, parent_task_id=task_id)
    subtask.is_completed = not subtask.is_completed
    subtask.save()
    messages.success(request, "✅ Subtask status updated successfully.")

    # Redirect correctly
    if trainer_id:
        return redirect('trainer_todo', trainer_id=trainer_id)
    else:
        return redirect('task_detail', task_id=task_id)







@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_task(request, task_id):
    """Allow admin to delete a task and its subtasks"""
    task = get_object_or_404(TodoTask, id=task_id)
    task.delete()
    messages.success(request, "🗑️ Task deleted successfully!")
    return redirect('admin_task_dashboard')
