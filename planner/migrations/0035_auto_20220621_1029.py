# Generated by Django 3.2.13 on 2022-06-21 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0034_alter_scheduledclass_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='deltacourseoffering',
            name='manually_marked_OK',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='deltacourseoffering',
            name='note_to_self',
            field=models.CharField(blank=True, help_text='(optional note to self)', max_length=700, null=True),
        ),
        migrations.AlterField(
            model_name='deltacourseoffering',
            name='requested_action',
            field=models.IntegerField(choices=[(0, 'Create'), (1, 'Update'), (2, 'Delete'), (3, 'No Action')], default=1),
        ),
    ]
