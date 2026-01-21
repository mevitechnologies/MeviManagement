# workshop_manager/models.py

from django.db import models
from django.contrib.auth.models import User


# models.py
DEPARTMENT_CHOICES = [
        ('CSE', 'CSE'),
        ('ISE', 'ISE'),
        ('AIML', 'AI & ML'),
        ('IOT', 'IoT'),
        ('CYBER', 'Cyber Security'),
        ('DS', 'Data Science'),
        ('EC', 'ECE'),
        ('CIVIL', 'Civil Engineering'),
        ('MECH', 'Mechanical Engineering'),
        ('CSA', 'CSA'),
        ('MCA', 'MCA'),
        ('BCA', 'BCA'),
        ('MBA', 'MBA'),
    ]
from django.utils import timezone
class Department(models.Model):
    DEPARTMENT_CHOICES = [
        ('CSE', 'CSE'),
        ('ISE', 'ISE'),
        ('AIML', 'AI & ML'),
        ('IOT', 'IoT'),
        ('CYBER', 'Cyber Security'),
        ('DS', 'Data Science'),
        ('EC', 'ECE'),
        ('CIVIL', 'Civil Engineering'),
        ('MECH', 'Mechanical Engineering'),
        ('CSA', 'CSA'),
        ('MCA', 'MCA'),
        ('BCA', 'BCA'),
        ('MBA', 'MBA'),
    ]

    code = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        unique=True
    )

    def __str__(self):
        return self.get_code_display()


class College(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)
    contact_email = models.EmailField(blank=True)

    def __str__(self):
        return self.name

class Trainer(models.Model):
    Name = models.CharField(max_length=35)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    expertise = models.CharField(max_length=200, blank=True)
    is_available = models.BooleanField(default=True)
    cv = models.FileField(upload_to='trainer_cvs/', blank=True, null=True)
    is_full_time = models.BooleanField(default=False)


    def __str__(self):
        return self.Name


class Workshop(models.Model):
    STATUS_CHOICES = [
        ('tentative', 'Tentative'),
        ('fixed', 'Fixed'),
        ('postponed', 'Postponed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(max_length=200)

    college = models.ForeignKey(
        'College',
        on_delete=models.CASCADE
    )

    departments = models.CharField(
        max_length=50,
        choices=DEPARTMENT_CHOICES,
        blank=True
    )

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='tentative'
    )

    remarks = models.TextField(blank=True)

    assigned_trainers = models.ManyToManyField(
        Trainer,
        blank=True
    )

    report = models.FileField(
        upload_to='workshop_reports/',
        blank=True,
        null=True
    )

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} @ {self.college}"


class FollowUp(models.Model):
    college = models.ForeignKey(
        'College',
        on_delete=models.CASCADE
    )

    workshop = models.ForeignKey(
        'Workshop',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    departments = models.ManyToManyField(
        Department,
        blank=True
    )

    person_met = models.CharField(
        max_length=100,
        help_text="HOD / Faculty / Coordinator name"
    )

    follow_up_type = models.CharField(
        max_length=50,
        choices=[
            ('proposal', 'Send Proposal'),
            ('call', 'Follow-up Call'),
            ('meeting', 'Meeting'),
        ]
    )

    description = models.TextField(blank=True)

    follow_from = models.DateField()
    follow_to = models.DateField()

    assigned_to = models.ForeignKey(
        Trainer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_full_time': True}
    )

    reminder_date = models.DateTimeField(null=True, blank=True)

    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.college} - {self.person_met}"


class Notification(models.Model):
    follow_up = models.ForeignKey(FollowUp, on_delete=models.CASCADE)
    notify_on = models.DateTimeField()
    sent = models.BooleanField(default=False)


BATCH_CHOICES = [
    ('morning', 'Morning'),
    ('afternoon', 'Afternoon'),
    ('evening', 'Evening'),
]

MODE_CHOICES = [
    ('online', 'Online'),
    ('offline', 'Offline'),
]

HALL_CHOICES = [
    ('hall1', 'Hall 1'),
    ('hall2', 'Hall 2'),
]

class OfficeTraining(models.Model):
    name = models.CharField(max_length=200)
    batch_id = models.CharField(max_length=50)
    batch = models.CharField(max_length=20, choices=BATCH_CHOICES)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    hall = models.CharField(max_length=10, choices=HALL_CHOICES, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    trainers = models.ManyToManyField('Trainer')  # Assuming Trainer model exists

    def __str__(self):
        return f"{self.name} - {self.batch_id}"
    



class TodoTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]


    trainer = models.ForeignKey('Trainer',on_delete=models.CASCADE,limit_choices_to={'is_full_time': True})  # ✅ restricts to full-time trainers
    task = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    for_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)
    is_done = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task} - {self.trainer.Name} ({self.for_date})"


class SubTask(models.Model):
    parent_task = models.ForeignKey(
        'TodoTask',
        on_delete=models.CASCADE,
        related_name='subtasks'   # ✅ important
    )
    title = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({'Done' if self.is_completed else 'Pending'})"

class FollowUpReminder(models.Model):
    followup = models.ForeignKey(
        FollowUp,
        on_delete=models.CASCADE,
        related_name="reminders"
    )
    remind_at = models.DateTimeField()
    message = models.CharField(max_length=255, blank=True)
    is_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"Reminder for {self.followup}"
