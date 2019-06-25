from django.core.management.base import BaseCommand, CommandError
from planner.campus_models import *
from django.db.models import Q
import datetime 
import csv

class Command(BaseCommand):
    args = 'subject_abbrev, course_number, title, credit_hours, schedule_semester, schedule_year'
    help = 'Create a course if it does not exist'
#
# sample usage:
# ./manage.py create_course PHY 124 'clarinet for the simple minded' 2 Spring E
#
    
    def handle(self, *args, **options):
        subject_abbrev, course_number, title, credit_hours, schedule_semester, schedule_year = args
        print("processing: ", subject_abbrev, course_number, title, credit_hours, schedule_semester, schedule_year)

        try:
            semester_name = SemesterName.objects.get(name = schedule_semester)
            print(semester_name)
        except SemesterName.DoesNotExist:
            raise CommandError(schedule_semester+' semester does not exist.')

        subject = Subject.objects.filter(abbrev=subject_abbrev)
        if len(subject) == 0:
            raise CommandError('Subject area does not exist!')
        elif len(subject) > 1:
            raise CommandError('There is ambiguity in the subject -- more than one such subject exists.')

        if not(schedule_year == 'O' or schedule_year == 'E' or schedule_year == 'B'):
            raise CommandError(schedule_year+' is not a possible schedule_year option.')

        try:
            credit_hours = int(credit_hours)
        except ValueError:
            raise CommandError('credit_hours must be an integer.')

#        course = Course.objects.filter(Q(subject__abbrev=subject_abbrev)
#                                       &(number=course_number))
#        print course

        course = Course.objects.filter(Q(subject__abbrev=subject_abbrev)&Q(number=course_number))
        if len(course)==0:
            print('creating course....')
            co, created = Course.objects.get_or_create(subject = subject[0],
                                                       number = course_number,
                                                       title = title,
                                                       credit_hours = credit_hours,
                                                       schedule_year = schedule_year
                                                       )
            co.save()
            co.schedule_semester.add(semester_name.id)
        else:
            raise CommandError(subject_abbrev+' '+course_number+' already exists.')

#        for course in Course.objects.filter(Q(subject__abbrev=subject_abbrev)
#                                            &Q(number=course_number)):
#            print course

