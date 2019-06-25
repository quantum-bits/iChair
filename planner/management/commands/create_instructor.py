from django.core.management.base import BaseCommand, CommandError
from planner.campus_models import *
from django.db.models import Q

class Command(BaseCommand):
    args = 'instructor_first_name,instructor_last_name, university, department_abbrev, faculty_id, rank'
    help = 'Create an instructor if that person does not already exist'
#
# sample usage:
# ./manage.py create_instructor 'Hank' 'Voss' 'Taylor University' 'PHY' '0001' 'Full'
#
# Note: checks first to see if instructor already exists in the db; if so, exits
#
    
    def handle(self, *args, **options):
        instructor_first_name,instructor_last_name, university, department_abbrev, faculty_id, rank = args

        print("processing: ", instructor_first_name,instructor_last_name, university, department_abbrev, faculty_id, rank) 

        try:
            university_object = University.objects.get(name = university)
        except University.DoesNotExist:
            raise CommandError(university+' does not exist')

        try:
            department_object = Department.objects.get(abbrev = department_abbrev)
        except Department.DoesNotExist:
            raise CommandError(department+' does not exist')

        try:
            instructor = FacultyMember.objects.get(Q(last_name=instructor_last_name)&Q(first_name=instructor_first_name))
            raise CommandError(instructor_first_name+' '+instructor_last_name+' already exists in the database.')
        except FacultyMember.DoesNotExist:
            instructor = FacultyMember.objects.create(last_name = instructor_last_name,
                                                      first_name = instructor_first_name,
                                                      department = department_object,
                                                      university = university_object,
                                                      rank = rank,
                                                      faculty_id = faculty_id
                                                      )
