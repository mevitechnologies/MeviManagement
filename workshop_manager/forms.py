from django import forms
from .models import Trainer, Workshop
from django.utils.safestring import mark_safe
from .models import FollowUp
from datetime import datetime
from .models import OfficeTraining
from .models import TodoTask, SubTask
from django.forms import modelformset_factory


class TrainerForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = ['Name', 'email', 'phone', 'expertise', 'is_available', 'cv', 'is_full_time']
        widgets = {
            'Name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'expertise': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Expertise areas'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cv': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_full_time': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

        }


from .models import Workshop, Trainer, College, Department

class WorkshopForm(forms.ModelForm):
    class Meta:
        model = Workshop
        fields = [
            'title',
            'college',
            'departments',
            'start_date',
            'end_date',
            'status',
            'remarks',
            'assigned_trainers',
            'report'
        ]

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'college': forms.Select(attrs={'class': 'form-select'}),  # ✅ dropdown
            'departments': forms.Select(attrs={'class': 'form-select'})  ,           # ✅ multi dept
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_trainers': forms.CheckboxSelectMultiple(),
            'report': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.conflict_trainers = []

        start_date = self.data.get('start_date')
        end_date = self.data.get('end_date')

        trainers = Trainer.objects.all()
        choices = []

        for trainer in trainers:
            conflict = False
            if start_date and end_date:
                conflict = Workshop.objects.filter(
                    assigned_trainers=trainer,
                    status='fixed',
                    start_date__lte=end_date,
                    end_date__gte=start_date
                ).exists()

            label = f"{trainer.Name} {'❌ Conflict' if conflict else ''}"
            choices.append((trainer.id, mark_safe(label)))

        self.fields['assigned_trainers'].choices = choices

# workshop_manager/forms.py

from django import forms
from .models import FollowUp


class FollowUpForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        fields = [
            'college',
            'workshop',
            'follow_up_type',
            'description',
            'follow_from',
            'follow_to',
            'assigned_to',
            'reminder_date',
            'is_completed',
        ]

        widgets = {
            'college': forms.Select(attrs={'class': 'form-select'}),
            'workshop': forms.Select(attrs={'class': 'form-select'}),
            'follow_up_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes / discussion points / next steps'
            }),
            'follow_from': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'follow_to': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'reminder_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class OfficeTrainingForm(forms.ModelForm):
    class Meta:
        model = OfficeTraining
        fields = '__all__'
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'trainers': forms.CheckboxSelectMultiple(),
        }

class TodoTaskForm(forms.ModelForm):
    class Meta:
        model = TodoTask
        fields = ['trainer', 'task', 'description', 'for_date', 'priority', 'estimated_hours']
        widgets = {
            'trainer': forms.Select(attrs={'class': 'form-select'}),
            'task': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter task'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'for_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
        }

class SubTaskForm(forms.ModelForm):
    class Meta:
        model = SubTask
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subtask title'})
        }
class TodoTaskForm(forms.ModelForm):
    class Meta:
        model = TodoTask
        fields = ['trainer', 'task', 'description', 'priority', 'estimated_hours', 'for_date']
        widgets = {
            'for_date': forms.DateInput(attrs={'type': 'date'}),
        }



SubTaskFormSet = modelformset_factory(
    SubTask,
    fields=('title',),
    extra=3,  # number of empty subtask fields by default
    widgets={
        'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subtask title'})
    }
)
from .models import College

class CollegeForm(forms.ModelForm):
    class Meta:
        model = College
        fields = "__all__"
