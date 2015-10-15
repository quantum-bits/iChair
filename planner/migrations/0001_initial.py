# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AcademicYear',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('begin_on', models.DateField()),
                ('end_on', models.DateField()),
            ],
            options={
                'ordering': ['begin_on'],
            },
        ),
        migrations.CreateModel(
            name='AdvisingNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('note', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Building',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('abbrev', models.CharField(max_length=20)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['abbrev'],
            },
        ),
        migrations.CreateModel(
            name='ClassMeeting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('held_on', models.DateField()),
                ('begin_at', models.TimeField()),
                ('end_at', models.TimeField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ClassStanding',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('seq', models.PositiveIntegerField(default=10)),
                ('name', models.CharField(max_length=20)),
            ],
            options={
                'ordering': ['seq'],
            },
        ),
        migrations.CreateModel(
            name='Constraint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80)),
                ('constraint_text', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('number', models.CharField(max_length=10)),
                ('title', models.CharField(max_length=80)),
                ('credit_hours', models.PositiveIntegerField(default=3)),
                ('schedule_year', models.CharField(default=b'B', max_length=1, choices=[(b'E', b'Even'), (b'O', b'Odd'), (b'B', b'Both')])),
                ('crn', models.CharField(max_length=10, null=True, blank=True)),
            ],
            options={
                'ordering': ['subject', 'number', 'title'],
            },
        ),
        migrations.CreateModel(
            name='CourseAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('abbrev', models.CharField(max_length=10)),
                ('name', models.CharField(max_length=80)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CourseOffering',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('load_available', models.FloatField(default=3)),
                ('max_enrollment', models.PositiveIntegerField(default=10)),
                ('comment', models.CharField(help_text=b'(optional)', max_length=20, null=True, blank=True)),
                ('course', models.ForeignKey(related_name='offerings', to='planner.Course')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CourseTaken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course_offering', models.ForeignKey(to='planner.CourseOffering')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DegreeProgram',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(help_text=b'e.g., Physics BS, entering odd years', max_length=100)),
                ('entering_year', models.CharField(max_length=1, choices=[(b'E', b'Even'), (b'O', b'Odd'), (b'B', b'Both')])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DegreeProgramCourse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('class_standing', models.ForeignKey(to='planner.ClassStanding')),
                ('course', models.ForeignKey(to='planner.Course')),
                ('degree_program', models.ForeignKey(to='planner.DegreeProgram')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('abbrev', models.CharField(max_length=10, blank=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('letter_grade', models.CharField(max_length=5)),
                ('grade_points', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Holiday',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('begin_on', models.DateField()),
                ('end_on', models.DateField()),
            ],
            options={
                'ordering': ['begin_on'],
            },
        ),
        migrations.CreateModel(
            name='Major',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80)),
                ('department', models.ForeignKey(related_name='majors', to='planner.Department')),
            ],
        ),
        migrations.CreateModel(
            name='Minor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80)),
                ('department', models.ForeignKey(related_name='minors', to='planner.Department')),
            ],
        ),
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('note', models.TextField()),
                ('department', models.ForeignKey(related_name='notes', to='planner.Department')),
                ('year', models.ForeignKey(related_name='notes', blank=True, to='planner.AcademicYear', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OfferingInstructor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('load_credit', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)])),
                ('course_offering', models.ForeignKey(related_name='offering_instructors', to='planner.CourseOffering')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OtherLoad',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('load_credit', models.FloatField()),
                ('comments', models.CharField(help_text=b'optional longer comments', max_length=100, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='OtherLoadType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('load_type', models.CharField(help_text=b'e.g., Research, Chair, Sabbatical', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('nickname', models.CharField(max_length=50, blank=True)),
                ('home_phone', models.CharField(max_length=20, blank=True)),
                ('cell_phone', models.CharField(max_length=20, blank=True)),
                ('work_phone', models.CharField(max_length=20, blank=True)),
                ('photo', models.ImageField(upload_to=b'photos', blank=True)),
            ],
            options={
                'verbose_name_plural': 'people',
            },
        ),
        migrations.CreateModel(
            name='Requirement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'e.g., PhysicsBS Technical Electives, or GenEd Literature;first part is helpful for searching (when creating a major).', max_length=50)),
                ('display_name', models.CharField(help_text=b'e.g., Technical Electives, or Literature;this is the title that will show up when studentsdo a graduation audit.', max_length=50)),
                ('constraints', models.ManyToManyField(related_name='constraints', to='planner.Constraint', blank=True)),
                ('courses', models.ManyToManyField(related_name='courses', to='planner.Course', blank=True)),
                ('requirements', models.ManyToManyField(related_name='sub_requirements', to='planner.Requirement', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='RequirementBlock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'e.g., PhysicsBS Technical Electives, or GenEd Literature;first part is helpful for searching (when creating a major).', max_length=50)),
                ('display_name', models.CharField(help_text=b'e.g., Technical Electives, or Literature;this is the title that will show up when studentsdo a graduation audit.', max_length=50)),
                ('requirement_type', models.IntegerField(default=1, help_text=b'Choose AND if all are required,OR if a subset is required.', choices=[(1, b'AND'), (2, b'OR')])),
                ('minimum_number_of_credit_hours', models.IntegerField(default=10)),
                ('list_order', models.PositiveIntegerField(default=1, help_text=b'Preferred place in the listof requirements; it is OK if numbersare repeated or skipped.')),
                ('text_for_user', models.CharField(help_text=b'Optional helpful text for the user;will appear in the graduation audit.', max_length=200, blank=True)),
                ('courses', models.ManyToManyField(help_text=b'Select courses for this requirement.', to='planner.Course')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('number', models.CharField(max_length=20)),
                ('capacity', models.PositiveIntegerField(default=20)),
                ('building', models.ForeignKey(related_name='rooms', to='planner.Building')),
            ],
            options={
                'ordering': ['building__name', 'number'],
            },
        ),
        migrations.CreateModel(
            name='ScheduledClass',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('day', models.IntegerField(default=0, choices=[(0, b'Monday'), (1, b'Tuesday'), (2, b'Wednesday'), (3, b'Thursday'), (4, b'Friday')])),
                ('begin_at', models.TimeField()),
                ('end_at', models.TimeField()),
                ('comment', models.CharField(help_text=b'optional brief comment', max_length=40, null=True, blank=True)),
                ('course_offering', models.ForeignKey(related_name='scheduled_classes', to='planner.CourseOffering')),
                ('room', models.ForeignKey(related_name='scheduled_classes', to='planner.Room')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='School',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Semester',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('begin_on', models.DateField()),
                ('end_on', models.DateField()),
            ],
            options={
                'ordering': ['year', 'name'],
            },
        ),
        migrations.CreateModel(
            name='SemesterName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('seq', models.PositiveIntegerField(default=10)),
                ('name', models.CharField(max_length=40)),
            ],
            options={
                'ordering': ['seq'],
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('abbrev', models.CharField(max_length=10)),
                ('name', models.CharField(max_length=80)),
                ('department', models.ForeignKey(related_name='subjects', to='planner.Department')),
            ],
            options={
                'ordering': ['abbrev'],
            },
        ),
        migrations.CreateModel(
            name='TransferCourse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=80)),
                ('credit_hours', models.PositiveIntegerField(default=3)),
                ('equivalent_course', models.ForeignKey(related_name='transfer_courses', to='planner.Course')),
                ('semester', models.ForeignKey(to='planner.Semester')),
            ],
        ),
        migrations.CreateModel(
            name='University',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('url', models.URLField()),
            ],
            options={
                'verbose_name_plural': 'universities',
            },
        ),
        migrations.CreateModel(
            name='UserPreferences',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('permission_level', models.IntegerField(default=0, choices=[(0, b'view only'), (1, b'department scheduler'), (2, b'super-user')])),
                ('academic_year_to_view', models.ForeignKey(related_name='user_preferences', to='planner.AcademicYear')),
                ('department_to_view', models.ForeignKey(related_name='user_preferences', to='planner.Department')),
                ('other_load_types_to_view', models.ManyToManyField(related_name='user_preferences', null=True, to='planner.OtherLoadType', blank=True)),
                ('rooms_to_view', models.ManyToManyField(related_name='user_preferences', null=True, to='planner.Room', blank=True)),
                ('user', models.ForeignKey(related_name='user_preferences', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FacultyMember',
            fields=[
                ('person_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='planner.Person')),
                ('faculty_id', models.CharField(max_length=25)),
                ('rank', models.CharField(max_length=8, choices=[(b'Inst', b'Instructor'), (b'Adj', b'Adjunct Professor'), (b'Asst', b'Assistant Professor'), (b'Assoc', b'Associate Professor'), (b'Full', b'Professor')])),
            ],
            options={
                'ordering': ['last_name', 'first_name'],
            },
            bases=('planner.person',),
        ),
        migrations.CreateModel(
            name='StaffMember',
            fields=[
                ('person_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='planner.Person')),
                ('staff_id', models.CharField(max_length=25)),
            ],
            options={
                'abstract': False,
            },
            bases=('planner.person',),
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('person_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='planner.Person')),
                ('student_id', models.CharField(max_length=25)),
                ('catalog_year', models.ForeignKey(related_name='+', to='planner.AcademicYear', help_text=b'Catalog year for graduation plan')),
                ('entering_year', models.ForeignKey(related_name='+', to='planner.AcademicYear', help_text=b'Year student entered university')),
                ('majors', models.ManyToManyField(related_name='students', null=True, to='planner.Major', blank=True)),
                ('minors', models.ManyToManyField(related_name='students', null=True, to='planner.Minor', blank=True)),
                ('university', models.ForeignKey(related_name='students', to='planner.University')),
            ],
            options={
                'abstract': False,
            },
            bases=('planner.person',),
        ),
        migrations.AddField(
            model_name='transfercourse',
            name='university',
            field=models.ForeignKey(related_name='transfer_courses', to='planner.University'),
        ),
        migrations.AddField(
            model_name='semester',
            name='name',
            field=models.ForeignKey(to='planner.SemesterName'),
        ),
        migrations.AddField(
            model_name='semester',
            name='year',
            field=models.ForeignKey(related_name='semesters', to='planner.AcademicYear'),
        ),
        migrations.AddField(
            model_name='school',
            name='university',
            field=models.ForeignKey(related_name='schools', to='planner.University'),
        ),
        migrations.AddField(
            model_name='otherload',
            name='load_type',
            field=models.ForeignKey(related_name='other_loads', to='planner.OtherLoadType'),
        ),
        migrations.AddField(
            model_name='otherload',
            name='semester',
            field=models.ForeignKey(to='planner.Semester'),
        ),
        migrations.AddField(
            model_name='holiday',
            name='semester',
            field=models.ForeignKey(related_name='holidays', to='planner.Semester'),
        ),
        migrations.AddField(
            model_name='department',
            name='school',
            field=models.ForeignKey(related_name='departments', to='planner.School'),
        ),
        migrations.AddField(
            model_name='degreeprogramcourse',
            name='semester_name',
            field=models.ForeignKey(to='planner.SemesterName'),
        ),
        migrations.AddField(
            model_name='degreeprogram',
            name='major',
            field=models.ForeignKey(related_name='degree_programs', to='planner.Major'),
        ),
        migrations.AddField(
            model_name='coursetaken',
            name='final_grade',
            field=models.ForeignKey(to='planner.Grade', blank=True),
        ),
        migrations.AddField(
            model_name='courseoffering',
            name='semester',
            field=models.ForeignKey(related_name='offerings', to='planner.Semester'),
        ),
        migrations.AddField(
            model_name='course',
            name='attributes',
            field=models.ManyToManyField(related_name='courses', to='planner.CourseAttribute', blank=True),
        ),
        migrations.AddField(
            model_name='course',
            name='coreqs',
            field=models.ManyToManyField(related_name='coreq_for', to='planner.Requirement', blank=True),
        ),
        migrations.AddField(
            model_name='course',
            name='prereqs',
            field=models.ManyToManyField(related_name='prereq_for', to='planner.Requirement', blank=True),
        ),
        migrations.AddField(
            model_name='course',
            name='schedule_semester',
            field=models.ManyToManyField(help_text=b'Semester(s) offered', to='planner.SemesterName', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='course',
            name='subject',
            field=models.ForeignKey(related_name='courses', to='planner.Subject'),
        ),
        migrations.AddField(
            model_name='classmeeting',
            name='course_offering',
            field=models.ForeignKey(related_name='class_meetings', to='planner.CourseOffering'),
        ),
        migrations.AddField(
            model_name='classmeeting',
            name='room',
            field=models.ForeignKey(to='planner.Room'),
        ),
        migrations.AddField(
            model_name='userpreferences',
            name='faculty_to_view',
            field=models.ManyToManyField(related_name='user_preferences', null=True, to='planner.FacultyMember', blank=True),
        ),
        migrations.AddField(
            model_name='transfercourse',
            name='student',
            field=models.ForeignKey(related_name='transfer_courses', to='planner.Student'),
        ),
        migrations.AddField(
            model_name='staffmember',
            name='department',
            field=models.ForeignKey(related_name='staff', to='planner.Department'),
        ),
        migrations.AddField(
            model_name='staffmember',
            name='university',
            field=models.ForeignKey(related_name='staff', to='planner.University'),
        ),
        migrations.AddField(
            model_name='school',
            name='dean',
            field=models.OneToOneField(null=True, blank=True, to='planner.FacultyMember'),
        ),
        migrations.AddField(
            model_name='otherload',
            name='instructor',
            field=models.ForeignKey(related_name='other_loads', to='planner.FacultyMember'),
        ),
        migrations.AddField(
            model_name='offeringinstructor',
            name='instructor',
            field=models.ForeignKey(related_name='offering_instructors', to='planner.FacultyMember'),
        ),
        migrations.AddField(
            model_name='facultymember',
            name='department',
            field=models.ForeignKey(related_name='faculty', to='planner.Department'),
        ),
        migrations.AddField(
            model_name='facultymember',
            name='university',
            field=models.ForeignKey(related_name='faculty', to='planner.University'),
        ),
        migrations.AddField(
            model_name='department',
            name='chair',
            field=models.OneToOneField(related_name='department_chaired', null=True, blank=True, to='planner.FacultyMember'),
        ),
        migrations.AddField(
            model_name='coursetaken',
            name='student',
            field=models.ForeignKey(related_name='courses_taken', to='planner.Student'),
        ),
        migrations.AddField(
            model_name='courseoffering',
            name='instructor',
            field=models.ManyToManyField(related_name='course_offerings', null=True, through='planner.OfferingInstructor', to='planner.FacultyMember', blank=True),
        ),
        migrations.AddField(
            model_name='classmeeting',
            name='instructor',
            field=models.ForeignKey(related_name='class_meetings', to='planner.FacultyMember'),
        ),
        migrations.AddField(
            model_name='advisingnote',
            name='student',
            field=models.ForeignKey(related_name='advising_notes', to='planner.Student'),
        ),
    ]
