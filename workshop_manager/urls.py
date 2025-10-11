from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Workshops
    path('workshops/', views.workshop_list, name='workshop_list'),
    path('workshops/add/', views.add_workshop, name='add_workshop'),
    path('workshops/<int:pk>/', views.workshop_detail, name='workshop_detail'),
    path('workshops/edit/<int:pk>/', views.edit_workshop, name='edit_workshop'),
    path('workshops/delete/<int:pk>/', views.delete_workshop, name='delete_workshop'),

    # Trainers
    path('trainers/', views.trainer_list, name='trainer_list'),
    path('trainers/add/', views.add_trainer, name='add_trainer'),
    path('trainers/edit/<int:pk>/', views.edit_trainer, name='edit_trainer'),
    path('trainers/delete/<int:pk>/', views.delete_trainer, name='delete_trainer'),

    # Trainer Schedule & Calendar
    path('trainer-schedule/', views.trainer_schedule, name='trainer_schedule'),
    path('calendar/', views.calendar_view, name='calendar_view'),
    path('api/availability/', views.availability_json, name='availability_json'),
    path('update-status/<int:pk>/<str:status>/', views.update_status, name='update_status'),

    # Follow-ups
    path('followups/', views.follow_ups, name='follow_ups'),
    path('followups/add/', views.add_followup, name='add_followup'),
    path('followups/edit/<int:pk>/', views.edit_followup, name='edit_followup'),
    path('followups/delete/<int:pk>/', views.delete_followup, name='delete_followup'),

    # Office Trainings
    path('office-trainings/', views.office_training_list, name='office_training_list'),
    path('office-trainings/add/', views.add_office_training, name='add_office_training'),
    path('office-trainings/edit/<int:pk>/', views.edit_office_training, name='edit_office_training'),
    path('office-trainings/view/<int:pk>/', views.view_office_training, name='view_office_training'),
    path('office-trainings/delete/<int:pk>/', views.delete_office_training, name='delete_office_training'),

    # -------------------------
    # ✅ To-Do Management URLs
    # -------------------------


    # ✅ New routes for enhanced task system
# Task Management
path('admin-task-board/', views.admin_task_dashboard, name='admin_task_dashboard'),
path('add-task/', views.add_task_page, name='add_task_page'),  # ✅ new page for creating a full task
    path('trainer-dashboard/', views.trainer_dashboard, name='trainer_dashboard'),
    path('change-task-status/<int:task_id>/', views.change_task_status, name='change_task_status'),
    path('add-subtask/<int:task_id>/', views.add_subtask, name='add_subtask'),
    path('task-history/', views.task_history, name='task_history'),


    # 🔁 Task Actions
    path('task/<int:trainer_id>/<int:task_id>/mark-done/', views.mark_task_done, name='mark_task_done'),
    path('task/<int:trainer_id>/<int:task_id>/undo/', views.undo_task_done, name='undo_task_done'),
path('task/<int:task_id>/<int:subtask_id>/toggle/', views.toggle_subtask_done, name='toggle_subtask_done'),
path('task/<int:task_id>/', views.task_detail, name='task_detail'),
path('delete-task/<int:task_id>/', views.delete_task, name='delete_task'),

   # 🔑 Auth Views
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]



# Serve media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
