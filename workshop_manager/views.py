from django.shortcuts import render, get_object_or_404, redirect
from .models import Workshop, Trainer, FollowUp
from .forms import TrainerForm, WorkshopForm
from datetime import date
from collections import defaultdict
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
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
        'calendar_followups': followups,
        "calendar_workshops": all_workshops
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
    query = request.GET.get('q')
    workshops = Workshop.objects.all()
    if query:
        workshops = workshops.filter(title__icontains=query)

    paginator = Paginator(workshops, 5)
    page = request.GET.get('page')
    workshops = paginator.get_page(page)

    return render(request, 'workshop_list.html', {'workshops': workshops})
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

@login_required
## 📝 Dashboard View - Add, View today's & carry forward tasks
def trainer_todo(request):
    today = timezone.now().date()
    trainers = Trainer.objects.filter(is_full_time=True)
    selected_trainer_id = request.GET.get('trainer') or request.POST.get('trainer')

    if selected_trainer_id:
        trainer = get_object_or_404(Trainer, id=selected_trainer_id)

        # 🔁 Carry forward yesterday's tasks if today's not created
        if not TodoTask.objects.filter(trainer=trainer, for_date=today).exists():
            yesterday = today - timedelta(days=1)
            incomplete_yesterday = TodoTask.objects.filter(
                trainer=trainer, for_date=yesterday, is_done=False
            )
            for task in incomplete_yesterday:
                TodoTask.objects.create(trainer=trainer, task=task.task, for_date=today)

        # ➕ Add new task
        if request.method == 'POST':
            form = TodoTaskForm(request.POST)
            if form.is_valid():
                task = form.save(commit=False)
                task.trainer = trainer
                task.for_date = today
                task.save()
                return redirect(f'/todo/?trainer={trainer.id}')
        else:
            form = TodoTaskForm()

        tasks = TodoTask.objects.filter(trainer=trainer, for_date=today)
        return render(request, 'todo/todo_dashboard.html', {
            'trainers': trainers,
            'trainer': trainer,
            'form': form,
            'tasks': tasks,
            'today': today,
        })

    return render(request, 'todo/todo_dashboard.html', {
        'trainers': trainers,
        'trainer': None
    })


# ✅ Mark Task as Done
def mark_task_done(request, trainer_id, task_id):
    task = get_object_or_404(TodoTask, id=task_id, trainer_id=trainer_id)
    task.is_done = True
    task.save()
    return redirect(f'/todo/?trainer={trainer_id}')


# ↩️ Undo Task (Mark as Not Done)
def undo_task_done(request, trainer_id, task_id):
    task = get_object_or_404(TodoTask, id=task_id, trainer_id=trainer_id)
    task.is_done = False
    task.save()
    return redirect(f'/todo/?trainer={trainer_id}')


# 🗑️ Delete Task
def delete_task(request, trainer_id, task_id):
    task = get_object_or_404(TodoTask, id=task_id, trainer_id=trainer_id)

    if request.method == 'POST':
        task.delete()
        messages.success(request, "Task deleted successfully.")
        return redirect(f'/todo/?trainer={trainer_id}')

    return render(request, 'todo/delete_task.html', {
        'task': task,
        'trainer_id': trainer_id,
    })


# ✏️ Edit Task
def edit_task(request, trainer_id, task_id):
    task = get_object_or_404(TodoTask, id=task_id, trainer_id=trainer_id)

    if request.method == 'POST':
        form = TodoTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated successfully.")
            return redirect(f'/todo/?trainer={trainer_id}')
    else:
        form = TodoTaskForm(instance=task)

    return render(request, 'todo/edit_task.html', {
        'form': form,
        'trainer': task.trainer,
        'task': task,
    })


# 📅 Task History View
def todo_history(request):
    all_tasks = TodoTask.objects.exclude(for_date=timezone.now().date()).order_by('-for_date')
    grouped = {}

    for task in all_tasks:
        grouped.setdefault(task.for_date, []).append(task)

    return render(request, 'todo/todo_history.html', {
        'grouped_tasks': grouped
    })