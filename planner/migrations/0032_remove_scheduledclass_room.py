# Generated by Django 3.2.4 on 2021-06-25 23:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0031_auto_20210614_1541'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scheduledclass',
            name='room',
        ),
    ]
