# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0002_auto_20151015_1710'),
    ]

    operations = [
        migrations.AddField(
            model_name='facultymember',
            name='inactive_starting',
            field=models.ForeignKey(related_name='faculty', blank=True, to='planner.AcademicYear', null=True),
        ),
    ]
