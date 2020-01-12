# Generated by Django 2.2.2 on 2020-01-12 00:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0019_auto_20190923_2137'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseOfferingPublicComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('text', models.CharField(max_length=60)),
                ('sequence_number', models.DecimalField(decimal_places=20, max_digits=23)),
                ('course_offering', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offering_comments', to='planner.CourseOffering')),
            ],
            options={
                'ordering': ['sequence_number'],
            },
        ),
    ]
