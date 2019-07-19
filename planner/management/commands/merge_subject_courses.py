from django.core.management import BaseCommand
from django.db.models import Q

from planner.models import *

from four_year_plan.secret import DATA_WAREHOUSE_AUTH as DW

# Note:
#   1. MCM is an outdated subject prefix (confirmed); can just leave the two copies in the db and not worry about it.
#   2. Need to create two new departments: Natural Science and Interarea Studies, and then create subjects for them....
#   3. The course 'IAS NAS480' in CSE needs to move over to NAS(!)  Do that FIRST
#   4. Then run all the depts with IAS subjects....do MAT first, then CSE

class Command(BaseCommand):
    # https://stackoverflow.com/questions/30230490/django-custom-command-error-unrecognized-arguments
    help = "Compares courses in one subject to those in a duplicate subject to see if there are duplicate courses."

    def add_arguments(self, parser):
        parser.add_argument('delete_subject_id')
        parser.add_argument('keep_subject_id')

    def handle(self, *args, **options):
        delete_subject_id = options['delete_subject_id']
        keep_subject_id = options['keep_subject_id']

        delete_subject = Subject.objects.get(pk=delete_subject_id)
        keep_subject = Subject.objects.get(pk=keep_subject_id)
        
        print('subject to eventually delete: ', delete_subject, " ", delete_subject.department)
        print('subject to keep: ', keep_subject, " ", keep_subject.department)
        proceed = input("proceed? (y/n) ")

        if proceed=='y':
            keep_course_list = [c.number for c in keep_subject.courses.all()]
            for course_to_be_fixed in delete_subject.courses.all():
                if course_to_be_fixed.number in keep_course_list:
                    print(course_to_be_fixed, 'IS a duplicate....')
                    # find the (hopefully unique) duplicate course in the "keep" version of the subject, and then attach the course offerings to it
                    course_keep_list = Course.objects.filter(Q(subject = keep_subject) & Q(number=course_to_be_fixed.number))
                    if len(course_keep_list) > 1:
                        print('ruh roh...there are ', len(course_keep_list), ' versions of this course!  looking for a match...')
                    else:
                        print("one potential match in 'subject to keep': ", course_keep_list[0])
                    for course_keep in course_keep_list:
                        if course_keep.title == course_to_be_fixed.title and course_keep.credit_hours == course_to_be_fixed.credit_hours:
                            print('...found a perfect match!  making the switch in ', len(course_to_be_fixed.offerings.all()),' course offering(s)....')
                            # now find the course offerings of course_delete and attach them to course_keep(!)
                            for co in course_to_be_fixed.offerings.all():
                                co.course = course_keep
                                co.save()
                                print('> ', co, 'moved over successfully!')
                            # now check if there are any course offerings for course_to_be_fixed (there shouldn't be)
                            if len(course_to_be_fixed.offerings.all())==0:
                                question_delete_course = input('>>> all course offerings have been moved; delete course? (y/n) ')
                                if question_delete_course=='y':
                                    print('...deleting course....')
                                    # https://stackoverflow.com/questions/3805958/how-to-delete-a-record-in-django-models
                                    delete_course = course_to_be_fixed.delete()
                                    print(delete_course)
                            else:
                                print('>>>...something went wrong -- not all course offerings were moved over')
                            break
                        else:
                            print('...not a perfect match....')
                            print('> ', len(course_to_be_fixed.offerings.all()), ' course offering(s)....')
                            print(' - title matches? ',course_keep.title == course_to_be_fixed.title)
                            print(' - credit hours match? ',course_keep.credit_hours == course_to_be_fixed.credit_hours)
                            if course_keep.credit_hours != course_to_be_fixed.credit_hours:
                                print("credit hours in 'subject to keep': ", course_keep.credit_hours, "; credit hours in 'subject to delete': ", course_to_be_fixed.credit_hours)
                            question_ignore_and_move = input(' > ignore differences, attach course offerings to existing course, then delete old course? (y/n) ')
                            if question_ignore_and_move == 'y':
                                for co in course_to_be_fixed.offerings.all():
                                    co.course = course_keep
                                    co.save()
                                    print('> ', co, 'moved over successfully!')
                                if len(course_to_be_fixed.offerings.all())==0:
                                    print('...deleting course....')
                                    delete_course = course_to_be_fixed.delete()
                                    print(delete_course)
                                break
                            else:
                                question_move_course = input(" > move this course over to the 'subject to keep'? (y/n) ")
                                if question_move_course == 'y':
                                    course_to_be_fixed.subject = keep_subject
                                    course_to_be_fixed.save()
                                    break
                else:
                    # move the course over to the "keep" version of the subject
                    print(course_to_be_fixed, "is NOT a duplicate; attaching course to 'subject to keep'....")
                    course_to_be_fixed.subject = keep_subject
                    course_to_be_fixed.save()



