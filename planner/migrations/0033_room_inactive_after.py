# Generated by Django 3.2.4 on 2021-08-23 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0032_remove_scheduledclass_room'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='inactive_after',
            field=models.DateField(blank=True, null=True),
        ),
    ]
