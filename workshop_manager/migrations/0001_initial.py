# Generated by Django 5.2.4 on 2025-07-03 14:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FollowUp",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "follow_up_type",
                    models.CharField(
                        choices=[
                            ("proposal", "Send Proposal"),
                            ("call", "Follow-up Call"),
                            ("meeting", "HOD Meeting"),
                        ],
                        max_length=100,
                    ),
                ),
                ("due_date", models.DateField()),
                ("is_completed", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("notify_on", models.DateTimeField()),
                ("sent", models.BooleanField(default=False)),
                (
                    "follow_up",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="workshop_manager.followup",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Trainer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("phone", models.CharField(max_length=15)),
                ("email", models.EmailField(max_length=254)),
                ("expertise", models.CharField(blank=True, max_length=200)),
                ("is_available", models.BooleanField(default=True)),
                (
                    "cv",
                    models.FileField(blank=True, null=True, upload_to="trainer_cvs/"),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Workshop",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("college", models.CharField(max_length=200)),
                ("department", models.CharField(max_length=100)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("tentative", "Tentative"),
                            ("fixed", "Fixed"),
                            ("postponed", "Postponed"),
                            ("cancelled", "Cancelled"),
                            ("completed", "Completed"),
                        ],
                        default="tentative",
                        max_length=20,
                    ),
                ),
                ("remarks", models.TextField(blank=True)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "report",
                    models.FileField(
                        blank=True, null=True, upload_to="workshop_reports/"
                    ),
                ),
                (
                    "assigned_trainers",
                    models.ManyToManyField(blank=True, to="workshop_manager.trainer"),
                ),
            ],
        ),
        migrations.AddField(
            model_name="followup",
            name="workshop",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="workshop_manager.workshop",
            ),
        ),
    ]
