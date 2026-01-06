from django.urls import path
from . import views

urlpatterns = [

    # ===============================
    # AUTH
    # ===============================
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # ===============================
    # DASHBOARD
    # ===============================
    path("", views.dashboard, name="dashboard"),

    # ===============================
    # WORKSHOPS
    # ===============================
    path("workshops/", views.workshop_list, name="workshop_list"),
    path("workshop/<int:pk>/", views.workshop_detail, name="workshop_detail"),
    path("workshop/add/", views.add_workshop, name="add_workshop"),
    path("workshop/<int:pk>/edit/", views.edit_workshop, name="edit_workshop"),
    path("workshop/<int:pk>/delete/", views.delete_workshop, name="delete_workshop"),
    path(
        "workshop/<int:pk>/status/<str:status>/",
        views.update_workshop_status,
        name="update_workshop_status"
    ),

    # ===============================
    # TRAINERS (ADMIN)
    # ===============================
    path("trainers/", views.trainer_list, name="trainer_list"),
    path("trainer/add/", views.add_trainer, name="add_trainer"),
    path("trainer/<int:pk>/edit/", views.edit_trainer, name="edit_trainer"),
    path("trainer/<int:pk>/delete/", views.delete_trainer, name="delete_trainer"),

    # ===============================
    # TRAINER DASHBOARD & SCHEDULE
    # ===============================
    path("trainer/dashboard/", views.trainer_dashboard, name="trainer_dashboard"),
    path("trainer/schedule/", views.trainer_schedule, name="trainer_schedule"),

    # ===============================
    # TASKS – ADMIN
    # ===============================
    path("admin/tasks/", views.admin_task_dashboard, name="admin_task_dashboard"),
    path("admin/tasks/add/", views.add_task_page, name="add_task_page"),
    path("task/<int:task_id>/delete/", views.delete_task, name="delete_task"),

    # ===============================
    # TASK DETAILS & SUBTASKS
    # ===============================
    path("task/<int:task_id>/", views.task_detail, name="task_detail"),
    path(
        "task/<int:task_id>/subtask/<int:subtask_id>/toggle/",
        views.toggle_subtask_done,
        name="toggle_subtask_done"
    ),

    # ===============================
    # FOLLOW-UPS
    # ===============================
    path("followups/", views.follow_ups, name="follow_ups"),
    path("followup/add/", views.add_followup, name="add_followup"),
    path("followup/<int:pk>/edit/", views.edit_followup, name="edit_followup"),
    path("followup/<int:pk>/delete/", views.delete_followup, name="delete_followup"),

    # ===============================
    # ===============================
# ===============================
# OFFICE TRAININGS
# ===============================
path("office-trainings/", views.office_training_list, name="office_training_list"),
path("office-training/add/", views.add_office_training, name="add_office_training"),
path("office-training/<int:pk>/edit/", views.edit_office_training, name="edit_office_training"),
path("office-training/<int:pk>/delete/", views.delete_office_training, name="delete_office_training"),
path("office-training/<int:pk>/view/", views.view_office_training, name="view_office_training"),
# ===============================
# TASKS
# ===============================
 path('tasks/', views.admin_task_dashboard, name='admin_task_dashboard'),
    path('tasks/add/', views.add_task_page, name='add_task_page'),
    path('tasks/history/', views.task_history, name='task_history'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('task/<int:task_id>/subtask/<int:subtask_id>/toggle/', views.toggle_subtask_done, name='toggle_subtask_done'),

# ===============================
# CALENDAR
# ===============================
path("calendar/", views.calendar_view, name="calendar_view"),
path('workshops/completed/', views.completed_workshops, name='completed_workshops'),
# Colleges
path("colleges/", views.college_list, name="college_list"),
path("colleges/add/", views.add_college, name="add_college"),
path("colleges/<int:pk>/edit/", views.edit_college, name="edit_college"),
path("colleges/<int:pk>/delete/", views.delete_college, name="delete_college"),

]
