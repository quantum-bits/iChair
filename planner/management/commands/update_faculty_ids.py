import pyodbc
from django.core.management import BaseCommand

from planner.models import *

from four_year_plan.secret import DATA_WAREHOUSE_AUTH as DW


class Command(BaseCommand):
    help = "Update faculty pidms in the iChair database so that they match those in Banner"

    def handle(self, *args, **options):
        connection = pyodbc.connect(f'DSN=warehouse;UID={DW["user"]};PWD={DW["password"]}')
        cursor = connection.cursor()
        
        faculty_rows = cursor.execute("""
            SELECT pidm, last_name, first_name, formal_first_name
            FROM dw.dim_faculty""").fetchall()
       
        cursor.close()
        connection.close()

        for row in faculty_rows:
            pidm = str(row.pidm)
            print(pidm," ", row.last_name, " ", row.first_name, " ", row.formal_first_name)

        faculty_members = FacultyMember.objects.all()
        counter = 0
        unmatched_faculty = []
        # https://stackoverflow.com/questions/1156087/python-search-in-lists-of-lists
        for faculty_member in faculty_members:
            counter = counter+1

            
            print(faculty_member.last_name," ", faculty_member.first_name)

            no_match = True
            banner_counter = 0
            for banner_faculty in faculty_rows:
                banner_counter = banner_counter + 1
                if banner_faculty.last_name == faculty_member.last_name and (banner_faculty.first_name == faculty_member.first_name or banner_faculty.formal_first_name == faculty_member.first_name ):
                    print(faculty_member.last_name," ", faculty_member.first_name, " ", banner_faculty.last_name, " ", banner_faculty.first_name, " ", banner_faculty.formal_first_name)
                    no_match = False
                    banner_pidm = str(banner_faculty.pidm)
                    if faculty_member.pidm == banner_pidm:
                        print("pidm matches!")
                    else:
                        faculty_member.pidm = str(banner_faculty.pidm)
                        faculty_member.save()
                    break
            print(banner_counter)
            if no_match:
                # set id to ''
                faculty_member.pidm = ''
                faculty_member.save()
                unmatched_faculty.append(faculty_member)
                


            #if counter == 15:
            #    break

        print("No matches found for the following: ")
        for faculty in unmatched_faculty:
            print(faculty, " - ", faculty.department, "; # course offerings: ", len(faculty.course_offerings.all()))

    #def find_faculty_member()