# Generated by Django 2.2.2 on 2019-09-05 12:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0015_course_banner_title'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='semester',
            options={'ordering': ['year', 'begin_on']},
        ),
    ]
