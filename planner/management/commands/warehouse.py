import pyodbc
from django.core.management import BaseCommand

from four_year_plan.secret import DATA_WAREHOUSE_AUTH as DW


class Command(BaseCommand):
    help = "Manage data warehouse information"

    def handle(self, *args, **options):
        connection = pyodbc.connect(f'DSN=warehouse;UID={DW["user"]};PWD={DW["password"]}')
        cursor = connection.cursor()
        rows = cursor.execute("select @@VERSION").fetchall()
        #rows2 = cursor.execute("select campus as CMP, term, part_of_term from dw.dim_course_section dcs").fetchall()
        faculty_rows = cursor.execute("""
            SELECT pidm, last_name, first_name 
            FROM dw.dim_faculty""").fetchall()
        rows2 = cursor.execute("""
            SELECT campus AS CMP
                , subject_course AS COURSE
                , course_reference_number AS CRN
                , course AS TITLE
                , section_credit_hours AS CREDHRS
                , section_capacity AS ENRLCAP
                , section AS [SESSION]
                , replace(days_of_week, '-', '') AS [DAYS], --'TR' as [DAYS]
            left(dmt.start_time, 2) + ':' + right(dmt.start_time, 2) + '-' + left(dmt.end_time, 2) + ':' +
            right(dmt.end_time, 2) AS [TIME], --'14:00-15:20' as [TIME]
                primary_df.last_name AS primary_instructor
                , --,secondary_df.last_name as secondary_instructor
            part_of_term
            --		,dcs.*
            FROM dw.dim_course_section dcs -- Use the course section dimension as base.
                -- Meeting times
                INNER JOIN dw.fact_course_meeting fcm ON (dcs.course_section_key = fcm.course_section_key)
                LEFT OUTER JOIN dw.dim_meeting_time dmt ON (fcm.meeting_time_key = dmt.meeting_time_key)
                -- Primary and Secondary Instructors
            INNER JOIN dw.fact_faculty_course primary_ffc ON (dcs.course_section_key = primary_ffc.scheduled_course_key AND
                primary_ffc.primary_instructor = 1) -- Check fact table for primary instructors
                --left outer join dw.fact_faculty_course secondary_ffc on (dcs.course_section_key=secondary_ffc.scheduled_course_key and secondary_ffc.secondary_instructor=1) -- Check fact table for secondary instructors
                LEFT OUTER JOIN dw.dim_faculty primary_df ON (primary_ffc.faculty_key = primary_df.faculty_key)
                """).fetchone()

        rows3 = cursor.execute("""
            SELECT dcs.term_code,
                dcs.course_reference_number,
                pidm AS instructor_pidm,
                CASE WHEN primary_instructor = 1
                    THEN 'Primary'
                ELSE 'Secondary' END AS instructor_type
                    --*
            FROM dw.fact_faculty_course ff
                -- Same joins as ichair 1, just reduced to hide other fields and make it appear as an associative table.
                INNER JOIN dw.dim_faculty df ON ff.faculty_key = df.faculty_key
                INNER JOIN dw.dim_course_section dcs ON (dcs.course_section_key = ff.scheduled_course_key)
                """).fetchone()

        cursor.close()
        connection.close()

        print(rows[0][0])

        for row in faculty_rows:
            pidm = str(row[0])
            print(pidm," ", row[1], " ", row[2])

        #for row in rows2:
        #    print(row)
        #for row in rows2:
        #    print(row)
        #for i in range(10):
        #    print(rows2[i].CMP, rows2[i].term, rows2[i].part_of_term)
