from django import forms

from .models import (
    Trainer,
    Workshop,
    College,
    Department,
    FollowUp,
    OfficeTraining,
    TodoTask,
    SubTask,
    CalendarEvent,
    WorkshopRemarks,
    MeetingNote,
)


# =========================================================
# TRAINER FORM
# =========================================================

class TrainerForm(forms.ModelForm):

    class Meta:
        model = Trainer
        fields = [
            "Name",
            "email",
            "phone",
            "expertise",
            "is_available",
            "cv",
            "is_full_time",
        ]

        widgets = {
            "Name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Full Name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Email address",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                }
            ),
            "expertise": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Expertise areas",
                }
            ),
            "is_available": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "cv": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "is_full_time": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }


# =========================================================
# WORKSHOP FORM
# =========================================================

class WorkshopForm(forms.ModelForm):

    class Meta:
        model = Workshop

        fields = [
            "title",
            "college",
            "departments",
            "start_date",
            "end_date",
            "status",
            "remarks",
            "assigned_trainers",
            "report",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Workshop title",
                }
            ),
            "college": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "departments": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Remarks",
                }
            ),
            "assigned_trainers": forms.CheckboxSelectMultiple(),
            "report": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.conflict_trainers = []

        start_date = self.data.get("start_date")
        end_date = self.data.get("end_date")

        trainers = Trainer.objects.all().order_by("Name")

        choices = []

        for trainer in trainers:

            conflict = False

            if start_date and end_date:
                conflict = Workshop.objects.filter(
                    assigned_trainers=trainer,
                    status="fixed",
                    start_date__lte=end_date,
                    end_date__gte=start_date,
                ).exists()

            if conflict:
                self.conflict_trainers.append(trainer.id)

            label = (
                f"{trainer.Name} "
                f"{'❌ Conflict' if conflict else ''}"
            )

            choices.append(
                (
                    trainer.id,
                    label,
                )
            )

        self.fields["assigned_trainers"].choices = choices

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            self.add_error(
                "end_date",
                "End date must be on or after the start date.",
            )

        return cleaned_data


# =========================================================
# FOLLOW-UP FORM
# =========================================================

class FollowUpForm(forms.ModelForm):

    class Meta:
        model = FollowUp

        fields = [
            "college",
            "workshop",
            "follow_up_type",
            "description",
            "follow_from",
            "follow_to",
            "assigned_to",
            "reminder_date",
            "is_completed",
        ]

        widgets = {
            "college": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "workshop": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "follow_up_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Notes / discussion points / next steps"
                    ),
                }
            ),
            "follow_from": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "follow_to": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "assigned_to": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "reminder_date": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                }
            ),
            "is_completed": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        follow_from = cleaned_data.get("follow_from")
        follow_to = cleaned_data.get("follow_to")

        if (
            follow_from
            and follow_to
            and follow_to < follow_from
        ):
            self.add_error(
                "follow_to",
                "Follow-up end date must be on or after the start date.",
            )

        return cleaned_data


# =========================================================
# OFFICE TRAINING FORM
# =========================================================

class OfficeTrainingForm(forms.ModelForm):

    class Meta:
        model = OfficeTraining

        fields = "__all__"

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Training name",
                }
            ),
            "batch_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Batch ID",
                }
            ),
            "batch": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "mode": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "hall": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "trainers": forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            self.add_error(
                "end_date",
                "End date must be on or after the start date.",
            )

        return cleaned_data


# =========================================================
# TODO TASK FORM
# =========================================================

class TodoTaskForm(forms.ModelForm):

    class Meta:
        model = TodoTask

        fields = [
            "trainer",
            "task",
            "description",
            "for_date",
            "priority",
            "estimated_hours",
        ]

        widgets = {
            "trainer": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "task": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter task",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Task description",
                }
            ),
            "for_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "estimated_hours": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.5",
                    "min": "0",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Defensive filtering in addition to the model's
        # limit_choices_to.
        self.fields["trainer"].queryset = (
            Trainer.objects
            .filter(is_full_time=True)
            .order_by("Name")
        )


# =========================================================
# SUBTASK FORM
# =========================================================

class SubTaskForm(forms.ModelForm):

    class Meta:
        model = SubTask

        fields = [
            "title",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter subtask title",
                }
            ),
        }


# =========================================================
# SUBTASK FORMSET
# =========================================================

SubTaskFormSet = forms.modelformset_factory(
    SubTask,
    form=SubTaskForm,
    extra=3,
)


# =========================================================
# COLLEGE FORM
# =========================================================

class CollegeForm(forms.ModelForm):

    class Meta:
        model = College
        fields = "__all__"

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "College name",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "City",
                }
            ),
            "state": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "State",
                }
            ),
            "contact_person": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Contact person",
                }
            ),
            "contact_phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Contact phone",
                }
            ),
            "contact_email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Contact email",
                }
            ),
        }


# =========================================================
# WORKSHOP REMARKS FORM
# =========================================================

class WorkshopRemarksForm(forms.ModelForm):

    class Meta:
        model = WorkshopRemarks

        exclude = [
            "workshop",
            "trainer",
            "created_at",
        ]

        widgets = {
            "topics_covered": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "activities_conducted": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "blockers_faced": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "learning_outcomes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "innovation_added": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "notes_prepared": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "notes_link": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://...",
                }
            ),
            "student_feedback": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "improvement_suggestions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "overall_rating": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "max": "5",
                }
            ),
        }

    def clean_overall_rating(self):
        rating = self.cleaned_data.get("overall_rating")

        if rating is not None and not 1 <= rating <= 5:
            raise forms.ValidationError(
                "Overall rating must be between 1 and 5."
            )

        return rating


# =========================================================
# MEETING NOTE FORM
# =========================================================

class MeetingNoteForm(forms.ModelForm):

    class Meta:
        model = MeetingNote

        fields = [
            "meeting_date",
            "title",
            "attendees",
            "discussion_points",
            "decisions_taken",
            "blockers",
            "action_items",
            "next_steps",
            "attachment",
        ]

        widgets = {
            "meeting_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Meeting title",
                }
            ),
            "attendees": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                    "size": "6",
                }
            ),
            "discussion_points": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Discussion points",
                }
            ),
            "decisions_taken": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "blockers": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "action_items": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "next_steps": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "attachment": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }


# =========================================================
# CALENDAR EVENT FORM
# =========================================================

class CalendarEventForm(forms.ModelForm):

    class Meta:
        model = CalendarEvent

        fields = [
            "title",
            "trainers",
            "event_type",
            "date",
            "start_time",
            "end_time",
            "workshop",
            "college",
            "department",
            "guest_faculty",
            "location",
            "description",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Event title",
                }
            ),
            "trainers": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                    "size": "6",
                }
            ),
            "event_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "start_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),
            "end_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),
            "workshop": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "college": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "department": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "guest_faculty": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Guest faculty name (optional)",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Room / Hall / Online",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Event details...",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")
        event_type = cleaned_data.get("event_type")
        guest_faculty = cleaned_data.get("guest_faculty")

        # Time validation
        if start and end and start >= end:
            self.add_error(
                "end_time",
                "End time must be after start time.",
            )

        # Guest faculty is relevant for guest training.
        if event_type == "guest_training" and not guest_faculty:
            self.add_error(
                "guest_faculty",
                "Please enter the guest faculty name.",
            )

        return cleaned_data
