# Generated by Django 2.2.2 on 2019-09-07 18:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('banner', '0002_courseoffering_ichair_id'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='offeringinstructor',
            options={'ordering': ['instructor__last_name', 'instructor__first_name']},
        ),
    ]
