# Generated by Django 2.2.2 on 2019-08-02 14:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0012_subject_trusted_departments'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='department',
            name='trusted_departments',
        ),
    ]