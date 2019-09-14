# Generated by Django 2.2.2 on 2019-08-31 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0013_remove_department_trusted_departments'),
    ]

    operations = [
        migrations.AddField(
            model_name='offeringinstructor',
            name='is_primary',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='first_name',
            field=models.CharField(max_length=60),
        ),
        migrations.AlterField(
            model_name='person',
            name='last_name',
            field=models.CharField(max_length=60),
        ),
        migrations.AlterField(
            model_name='person',
            name='nickname',
            field=models.CharField(blank=True, max_length=60),
        ),
    ]