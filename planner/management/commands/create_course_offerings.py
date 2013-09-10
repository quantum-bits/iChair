from django.core.management.base import BaseCommand, CommandError
from planner.campus_models import *
from django.db.models import Q
import datetime 
import csv

class Command(BaseCommand):
    args = 'subject_abbrev, course_number, semester, actual_year, loads, max_enrollment'
    help = 'Create a number of course offerings, along with associated instructors, if they do not exist'
#
# sample usage:
# ./manage.py create_course_offerings PHY 124 Fall 2013 [3,2,2] 32
# ./manage.py create_course_offerings PHY 124 J-Term 2014 [3] 32 (note: creates in 2013-14 academic year)
#
# Notes: 
# 1. The actual_year is the year the semester actually occurs.  In the rest of the software, academic_year
#    is used, and it refers to the year that goes with the Fall of the academic year in question.  Thus, for J-Term
#    and Spring, academic_year = actual_year - 1.
# 2. There is no possibility of co-teaching a course -- one instructor gets all of the load.  A shared course
#    must be put in by hand later.
    
    def handle(self, *args, **options):
        subject_abbrev, course_number, semester, actual_year, loads, max_enrollment=args

# >>> in run_command.py
# checks:
# - if more than one subj/course # combination exists in db, exit, since it is ambiguous which one should be used
# - checks db to see how many course offerings already exist for this course, semester and actual year.  If more
#   are requested than exist, those are created

        print "processing: ", subject_abbrev, course_number, semester, actual_year, loads, max_enrollment

        load_list = convert_loads_to_list(loads)

        number_offerings = len(load_list)
        print load_list, number_offerings

        try:
            course = Course.objects.get(Q(subject__abbrev = subject_abbrev)&Q(number = course_number))
            print "Found: ", course
        except Course.DoesNotExist:
            raise CommandError(subject_abbrev+' '+course_number+' does not exist.')
        except Course.MultipleObjectsReturned:
            raise CommandError('Ambiguity: there are multiple versions of '+subject_abbrev+' '+course_number+'; exiting....')

# convert actual_year to academic_year
        if semester == 'Fall':
            academic_year = int(actual_year)
        else:
            academic_year = int(actual_year)-1

        current_offerings = course.offerings.filter(Q(semester__name__name=semester)&Q(semester__year__begin_on__year=academic_year))

        if len(current_offerings) < int(number_offerings):
            number_sections_to_create = int(number_offerings) - len(current_offerings)
            print len(current_offerings), 'section(s) exist(s); attempting to create', number_sections_to_create, 'more....'
        else:
            raise CommandError('Enough sections of this course already exist for this semester.')

        semester_object = Semester.objects.get(Q(name__name=semester)&Q(year__begin_on__year=academic_year))

        for ii in range(number_sections_to_create):
            co = CourseOffering.objects.create(course = course,
                                               semester = semester_object,
                                               load_available = float(load_list[ii]),
                                               max_enrollment = int(max_enrollment),
                                               comment = ''
                                               )
            co.save()

def convert_loads_to_list(loads):
    """Converts a load list string, such as '[3,2,4]' into a list of floats, such as [3.0, 2.0, 4.0]"""
    loads = loads[:-1]
    loads = loads[1:]
    loads = loads+','
    templist=[]
    new_word=''
    for i in loads:
        if i!=',':
            new_word = new_word+i
        else:
            templist.append(float(new_word))
            new_word=''
    return templist
            
