# Generated by Django 2.2.2 on 2020-01-18 19:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0020_courseofferingpubliccomment'),
    ]

    operations = [
        migrations.AddField(
            model_name='deltacourseoffering',
            name='update_public_comments',
            field=models.BooleanField(default=False),
        ),
    ]
