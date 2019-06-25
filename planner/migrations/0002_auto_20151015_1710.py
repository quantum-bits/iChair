# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='schedule_semester',
            field=models.ManyToManyField(help_text=b'Semester(s) offered', to='planner.SemesterName', blank=True),
        ),
        migrations.AlterField(
            model_name='courseoffering',
            name='instructor',
            field=models.ManyToManyField(related_name='course_offerings', through='planner.OfferingInstructor', to='planner.FacultyMember', blank=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='majors',
            field=models.ManyToManyField(related_name='students', to='planner.Major', blank=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='minors',
            field=models.ManyToManyField(related_name='students', to='planner.Minor', blank=True),
        ),
        migrations.AlterField(
            model_name='userpreferences',
            name='faculty_to_view',
            field=models.ManyToManyField(related_name='user_preferences', to='planner.FacultyMember', blank=True),
        ),
        migrations.AlterField(
            model_name='userpreferences',
            name='other_load_types_to_view',
            field=models.ManyToManyField(related_name='user_preferences', to='planner.OtherLoadType', blank=True),
        ),
        migrations.AlterField(
            model_name='userpreferences',
            name='rooms_to_view',
            field=models.ManyToManyField(related_name='user_preferences', to='planner.Room', blank=True),
        ),
    ]
