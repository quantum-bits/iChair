import pyodbc
from django.core.management import BaseCommand

from planner.models import *
from banner.models import FacultyMember as BannerFacultyMember

from four_year_plan.secret import DATA_WAREHOUSE_AUTH as DW


class Command(BaseCommand):
    help = "Update faculty external_system_ids in the iChair and Banner databases so that they match those in the Data Warehouse"

    def handle(self, *args, **options):
        connection = pyodbc.connect(f'DSN=warehouse;UID={DW["user"]};PWD={DW["password"]}')
        cursor = connection.cursor()
        
        faculty_rows = cursor.execute("""
            SELECT pidm, last_name, first_name, formal_first_name, external_system_id
            FROM dw.dim_faculty""").fetchall()
       
        cursor.close()
        connection.close()

        for row in faculty_rows:
            pidm = str(row.pidm)
            print(pidm," ", row.external_system_id, " ", row.last_name, " ", row.first_name, " ", row.formal_first_name)

        banner_faculty_members = BannerFacultyMember.objects.all()
        faculty_members = FacultyMember.objects.all()
        
        for banner_faculty_member in banner_faculty_members:
            no_match = True
            for dw_faculty in faculty_rows:
                if banner_faculty_member.pidm == str(dw_faculty.pidm):
                    print('matched banner pidm!')
                    no_match = False
                    banner_faculty_member.external_system_id = dw_faculty.external_system_id
                    banner_faculty_member.save()
                    # https://learn.theprogrammingfoundation.org/programming/python/loops
                    # https://www.tutorialspoint.com/python/python_break_statement.htm
                    break
            if no_match:
                print("no match for: ", banner_faculty_member.last_name, " ", banner_faculty_member.first_name, " (", banner_faculty_member.pidm, ")")

        for faculty_member in faculty_members:
            no_match = True
            for dw_faculty in faculty_rows:
                if faculty_member.pidm == str(dw_faculty.pidm):
                    print('matched iChair pidm!')
                    no_match = False
                    faculty_member.external_system_id = dw_faculty.external_system_id
                    faculty_member.save()
                    # https://learn.theprogrammingfoundation.org/programming/python/loops
                    # https://www.tutorialspoint.com/python/python_break_statement.htm
                    break
            if no_match:
                print("no match for: ", faculty_member.last_name, " ", faculty_member.first_name, " (", faculty_member.pidm, ")")
