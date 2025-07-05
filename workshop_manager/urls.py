# workshop_manager/urls.py

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('workshops/<int:pk>/', views.workshop_detail, name='workshop_detail'),
    path('followups/', views.follow_ups, name='follow_ups'),
        path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # urls.py
path('calendar/', views.calendar_view, name='calendar_view'),
path('api/availability/', views.availability_json, name='availability_json'),

    # urls.py
path('update-status/<int:pk>/<str:status>/', views.update_status, name='update_status'),
path('trainer-schedule/', views.trainer_schedule, name='trainer_schedule'),

    # Trainer URLs
    path('trainers/', views.trainer_list, name='trainer_list'),
    path('trainers/add/', views.add_trainer, name='add_trainer'),
    path('trainers/edit/<int:pk>/', views.edit_trainer, name='edit_trainer'),

    # Workshop URLs
    path('workshops/', views.workshop_list, name='workshop_list'),
    path('workshops/add/', views.add_workshop, name='add_workshop'),
    path('workshops/edit/<int:pk>/', views.edit_workshop, name='edit_workshop'),
    path('trainers/delete/<int:pk>/', views.delete_trainer, name='delete_trainer'),
path('workshops/delete/<int:pk>/', views.delete_workshop, name='delete_workshop'),

# FollowUp URLs
path('followups/', views.follow_ups, name='follow_ups'),
path('followups/add/', views.add_followup, name='add_followup'),
path('followups/edit/<int:pk>/', views.edit_followup, name='edit_followup'),
path('followups/delete/<int:pk>/', views.delete_followup, name='delete_followup'),

    path('office-trainings/', views.office_training_list, name='office_training_list'),
    path('office-trainings/add/', views.add_office_training, name='add_office_training'),
    path('office-trainings/edit/<int:pk>/', views.edit_office_training, name='edit_office_training'),
        path('office-trainings/view/<int:pk>/', views.view_office_training, name='view_office_training'),

    path('office-trainings/delete/<int:pk>/', views.delete_office_training, name='delete_office_training'),
    path('todo/', views.trainer_todo, name='trainer_todo'),

      # To-Do URLs
   path('todo/', views.trainer_todo, name='trainer_todo'),  # for dashboard with ?trainer=
    path('todo/<int:trainer_id>/done/<int:task_id>/', views.mark_task_done, name='mark_task_done'),
    path('todo/<int:trainer_id>/undo/<int:task_id>/', views.undo_task_done, name='undo_task_done'),
    path('todo/<int:trainer_id>/edit/<int:task_id>/', views.edit_task, name='edit_task'),
    path('todo/<int:trainer_id>/delete/<int:task_id>/', views.delete_task, name='delete_task'),
    path('todo/history/', views.todo_history, name='todo_history'),

]

