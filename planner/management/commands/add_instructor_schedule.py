from django.core.management.base import BaseCommand, CommandError
from planner.campus_models import *
from django.db.models import Q
import datetime 
import csv

class Command(BaseCommand):
    args = 'subject_abbrev, course_number, semester, actual_year, instructor_first_name,instructor_last_name, days, begin_time, end_time, building_abbrev, room_number'
    help = 'Add an instructor and a weekly schedule to a course offering that currently has neither.'
#
# sample usage:
# ./manage.py add_instructor_schedule PHY 124 J-Term 2014 'Hank' 'Voss' 'MWF' '0900' '1250' 'ESC' '125' (note: creates in 2013-14 academic year)
#
# Notes: 
# 1. The actual_year is the year the semester actually occurs.  In the rest of the software, academic_year
#    is used, and it refers to the year that goes with the Fall of the academic year in question.  Thus, for J-Term
#    and Spring, academic_year = actual_year - 1.
# 2. There is no possibility of co-teaching a course -- one instructor gets all of the load.  A shared course
#    must be put in by hand later.
# 3. The load given to the instructor is the load assigned to the associated CourseOffering object.
# 4. The beginning and ending times need to be exactly four characters each (e.g., '0900' for 9:00)
#
    
    def handle(self, *args, **options):
        subject_abbrev, course_number, semester, actual_year, instructor_first_name, instructor_last_name, days, begin_time, end_time, building_abbrev, room_number = args

# >>> in run_command.py
# checks:
# - if more than one subj/course # combination exists in db, exit, since it is ambiguous which one should be used
# - looks for a course offering that contains no professor and no weekly schedule; if that doesn't exist, exits
# - looks for room; if it doesn't exist, exits
# - looks for requested instructor; if that person doesn't exist, exits
# - checks if requested faculty member is currently associated with the dept offering the course; if not, exits
# - checks that the days are M, T, W, R or F
# - checks that the begin_time and end_time strings are 4 characters and that they make sense, to some extent

        print "processing: ", subject_abbrev, course_number, semester, actual_year, instructor_first_name, instructor_last_name, days, begin_time, end_time, building_abbrev, room_number

        weekday_dict={'M':0,'T':1,'W':2,'R':3,'F':4}
        day_list = []

        if (len(begin_time) != 4) or (len(end_time)!=4):
            raise CommandError('begin_time and end_time need to be 4-character strings, such as 0900.')

        try:
            begin_time_hour = int(begin_time[:2])
            end_time_hour = int(end_time[:2])
            begin_time_minute = int(begin_time[2:])
            end_time_minute = int(end_time[2:])
        except ValueError:
            raise CommandError('begin_time and end_time need to be strings such as 0900.')

        if begin_time_hour<7 or end_time_hour>21:
            raise CommandError('Class appears to be starting very early or late.  Assuming this is an error.')

        if begin_time_minute<0 or begin_time_minute>59 or end_time_minute<0 or end_time_minute>59:
            raise CommandError('The minute setting(s) for this class need to be between 0 and 59.')

        if begin_time_hour+float(begin_time_minute)/60 >= end_time_hour+float(end_time_minute)/60:
            raise CommandError('The beginning time for the class needs to be before the ending time.')

        for day in days:
            try:
                day_list.append(weekday_dict[day])
            except KeyError:
                raise CommandError('Possible days are M, T, W, R or F.')

        try:
            course = Course.objects.get(Q(subject__abbrev = subject_abbrev)&Q(number = course_number))
#            print "Found: ", course
        except Course.DoesNotExist:
            raise CommandError(subject_abbrev+' '+course_number+' does not exist.')
        except Course.MultipleObjectsReturned:
            raise CommandError('Ambiguity: there are multiple versions of '+subject_abbrev+' '+course_number+'; exiting....')

        try:
            room = Room.objects.get(Q(number=room_number)&Q(building__abbrev=building_abbrev))
        except Room.DoesNotExist:
            raise CommandError(building_abbrev+' '+room_number+' does not exist.')
        except Course.MultipleObjectsReturned:
            raise CommandError('Ambiguity: there are multiple versions of '+building_abbrev+' '+room_number+'; exiting....')
        
        try:
            instructor = FacultyMember.objects.get(last_name=instructor_last_name)
#            print 'Found the instructor: ',instructor
        except FacultyMember.DoesNotExist:
            raise CommandError(instructor_last_name+' does not exist in the database.')
        except FacultyMember.MultipleObjectsReturned:
            try:
                instructor = FacultyMember.objects.get(Q(last_name=instructor_last_name)&Q(first_name=instructor_first_name))
                print 'There is more than one',instructor_last_name,'in the database, but the ambiguity was resolved by the first name.'
            except FacultyMember.MultipleObjectsReturned:
                raise CommandError('Ambiguity: there are multiple versions of '+instructor_first_name+' '+instructor_last_name+'; exiting....')
            except FacultyMember.DoesNotExist:
                raise CommandError(instructor_first_name+' '+instructor_last_name+' does not exist in the database.')

        if course.subject.department.id != instructor.department.id:
            raise CommandError('The instructor and course do not belong to the same department.')

# convert actual_year to academic_year
        if semester == 'Fall':
            academic_year = int(actual_year)
        else:
            academic_year = int(actual_year)-1

        current_offerings = course.offerings.filter(Q(semester__name__name=semester)&Q(semester__year__begin_on__year=academic_year))
        if len(current_offerings)==0:
            raise CommandError('There are no empty course offerings for this course.')

        found_empty_course_offering = False
        for co in current_offerings:
            instructor_list = co.offering_instructors.all()
            schedule_list = co.scheduled_classes.all()
            if len(instructor_list)==0 and len(schedule_list)==0:
                co_empty = co
                found_empty_course_offering = True
        if not found_empty_course_offering:
            raise CommandError('There are no empty course offerings for this course.')

# if get here, all checks have been passed and it is time to create an OfferingInstructor object and one or more
# ScheduledClass objects...woo-hoo!

        load = co_empty.load_available
        offering_instructor = OfferingInstructor.objects.create(course_offering = co_empty,
                                                                instructor = instructor,
                                                                load_credit = load
                                                                )
        offering_instructor.save()

        for day in day_list:
            schedule_addition = ScheduledClass.objects.create(course_offering = co_empty,
                                                              day = day,
                                                              begin_at = begin_time[:2]+':'+begin_time[2:],
                                                              end_at = end_time[:2]+':'+end_time[2:],
                                                              room = room,
                                                              comment = ''
                                                              )
            schedule_addition.save()


#        if len(current_offerings) < int(number_offerings):
#            number_sections_to_create = int(number_offerings) - len(current_offerings)
#            print len(current_offerings), 'section(s) exist(s); attempting to create', number_sections_to_create, 'more....'
#        else:
#            raise CommandError('Enough sections of this course already exist for this semester.')

#        semester_object = Semester.objects.get(Q(name__name=semester)&Q(year__begin_on__year=academic_year))

#        for ii in range(number_sections_to_create):
#            co = CourseOffering.objects.create(course = course,
#                                               semester = semester_object,
#                                               load_available = float(load),
#                                               max_enrollment = int(max_enrollment),
#                                               comment = ''
#                                               )
#            co.save()
