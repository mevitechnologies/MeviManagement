from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workshop_manager", "0006_alter_todotask_for_date_calendarevent_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="calendarevent",
            name="guest_faculty",
            field=models.CharField(
                max_length=200,
                blank=True,
                default="",
            ),
            preserve_default=False,
        ),
    ]