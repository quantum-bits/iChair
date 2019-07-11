from django.core.management import BaseCommand

from planner.models import *


class Command(BaseCommand):
    help = "find duplicate faculty in iChair db"

    def handle(self, *args, **options):
        
        faculty_members = FacultyMember.objects.all()
        faculty_last_names = []
        repeated_last_names = []
        # https://stackoverflow.com/questions/1156087/python-search-in-lists-of-lists
        for faculty_member in faculty_members:
            if faculty_member.last_name not in faculty_last_names:
                faculty_last_names.append(faculty_member.last_name)
            elif (faculty_member.last_name != 'TBA') and (faculty_member.last_name != 'TBD') and (faculty_member.last_name != 'Adjunct') and (faculty_member.last_name not in repeated_last_names):
                repeated_last_names.append(faculty_member.last_name)
                
        for last_name in repeated_last_names:
            faculty_list = FacultyMember.objects.filter(last_name = last_name)
            for f in faculty_list:
                print(f," ", f.department)

        

    #def find_faculty_member()