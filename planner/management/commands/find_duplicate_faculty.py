from django.core.management import BaseCommand

from planner.models import *


class Command(BaseCommand):
    help = "find duplicate faculty in iChair db"

    def handle(self, *args, **options):
        
        ay201718 = AcademicYear.objects.filter(begin_on__year = '2017')
        ay201819 = AcademicYear.objects.filter(begin_on__year = '2018')

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
                co2017=len(f.course_offerings.filter(Q(semester__year__begin_on__year = '2017')))
                co2018=len(f.course_offerings.filter(Q(semester__year__begin_on__year = '2018')))
                co2019=len(f.course_offerings.filter(Q(semester__year__begin_on__year = '2019')))
                ol2017=len(f.other_loads.filter(Q(semester__year__begin_on__year = '2017')))
                ol2018=len(f.other_loads.filter(Q(semester__year__begin_on__year = '2018')))
                ol2019=len(f.other_loads.filter(Q(semester__year__begin_on__year = '2019')))
                print(f," ", f.id," ",f.department)
                print('   loads: ', co2017, ' ', co2018, ' ', co2019,' other: ', ol2017, ' ', ol2018, ' ', ol2019)

        

    #def find_faculty_member()