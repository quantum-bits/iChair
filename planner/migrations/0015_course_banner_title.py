# Generated by Django 2.2.2 on 2019-09-02 14:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0014_auto_20190831_1336'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='banner_title',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
    ]
