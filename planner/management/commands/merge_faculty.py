import pyodbc
from django.core.management import BaseCommand

from planner.models import *

from four_year_plan.secret import DATA_WAREHOUSE_AUTH as DW

 # Question: Are there any things other than course offerings and other loads that we need to worry about?
        # Potential issues: 
        #   1. If both departments were keeping track of load, the new load will be doubled...should print load sheets for both
        #      depts before doing anything(!) so can fix things.
        #   2. "Other load" is only associated with the home dept, so just keep in mind that the "new" person will be getting it all
        #   3. If someone has effectively switched departments (like BB), we need to make a choice
        #

class Command(BaseCommand):
    # https://stackoverflow.com/questions/30230490/django-custom-command-error-unrecognized-arguments
    help = "Look for duplicates of faculty members in the iChair database."

    def add_arguments(self, parser):
        parser.add_argument('delete_instructor_id')
        parser.add_argument('keep_instructor_id')

    def handle(self, *args, **options):
        delete_instructor_id = options['delete_instructor_id']
        keep_instructor_id = options['keep_instructor_id']

        delete_instructor = FacultyMember.objects.get(pk=delete_instructor_id)
        keep_instructor = FacultyMember.objects.get(pk=keep_instructor_id)
        
        print('instructor to eventually delete: ', delete_instructor, " ", delete_instructor.department)
        print('instructor to keep: ', keep_instructor, " ", keep_instructor.department)
        proceed = input("proceed? (y/n)")
        if proceed == 'y':
            for oi in delete_instructor.offering_instructors.all():
                oi.instructor = keep_instructor
                oi.save()
        # same idea for other loads:
        for ol in delete_instructor.other_loads.all():
            ol.instructor = keep_instructor
            ol.save()








