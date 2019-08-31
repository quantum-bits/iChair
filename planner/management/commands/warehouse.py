import pyodbc
from django.core.management import BaseCommand

from four_year_plan.secret import DATA_WAREHOUSE_AUTH as DW

# https://github.com/mkleehammer/pyodbc/wiki/Objects

class Command(BaseCommand):
    help = "Manage data warehouse information"

    def handle(self, *args, **options):
        connection = pyodbc.connect(f'DSN=warehouse;UID={DW["user"]};PWD={DW["password"]}')
        cursor = connection.cursor()
        rows = cursor.execute("select @@VERSION").fetchall()
        #rows2 = cursor.execute("select campus as CMP, term, part_of_term from dw.dim_course_section dcs").fetchall()
        faculty_rows = cursor.execute("""
            SELECT pidm AS PIDM, last_name, first_name 
            FROM dw.dim_faculty""").fetchall()
        rows2 = cursor.execute("""
            SELECT campus AS CMP
                , subject_course AS COURSE
                , last_name
                , first_name
                , course_reference_number AS CRN
                , course AS TITLE
                , section_credit_hours AS CREDHRS
                , section_capacity AS ENRLCAP
                , section AS [SESSION]
                , dmt.start_time AS STARTTIME
                , dmt.end_time AS ENDTIME
                , dmt.day_of_week AS DAY
                , term
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
            WHERE (term = '202020' AND (subject_code = 'PHY' OR subject_code = 'ENP'))
                """).fetchall()

        course_offering_meetings = cursor.execute("""
            SELECT campus AS CMP
                , subject_course AS COURSE
                , course_reference_number AS CRN
                , course AS TITLE
                , section_credit_hours AS CREDHRS
                , section_capacity AS ENRLCAP
                , section AS [SESSION]
                , dmt.start_time AS STARTTIME
                , dmt.end_time AS ENDTIME
                , dmt.day_of_week AS DAY
                , fcm.course_section_key AS faculty_course_meeting_key
                , term
                , part_of_term
            FROM dw.dim_course_section dcs -- Use the course section dimension as base.
                -- Meeting times
                LEFT OUTER JOIN dw.fact_course_meeting fcm ON (dcs.course_section_key = fcm.course_section_key)
                LEFT OUTER JOIN dw.dim_meeting_time dmt ON (fcm.meeting_time_key = dmt.meeting_time_key)
            WHERE (term = '202020' AND subject_code = 'PHY' AND campus = 'U')
                """).fetchall()

        course_instructors = cursor.execute("""
            SELECT dcs.*
                , ffc.faculty_key as faculty_key
                , ffc.primary_instructor
                , ffc.secondary_instructor
                , df.*
            FROM dw.dim_course_section dcs -- use the course section dimension as base.
                LEFT OUTER JOIN dw.fact_faculty_course ffc ON (ffc.scheduled_course_key = dcs.course_section_key)
                LEFT OUTER JOIN dw.dim_faculty df ON (ffc.faculty_key = df.faculty_key)
            WHERE (term = '202020' AND (subject_code = 'COS' OR subject_code = 'PHY' OR subject_code = 'ENP'))
                """).fetchall()

        rows3 = cursor.execute("""
            SELECT dcs.term_code as TERMCODE,
                dcs.course_reference_number as CRN,
                pidm AS instructor_pidm,
                last_name,
                first_name,
                CASE WHEN primary_instructor = 1
                    THEN 'Primary'
                ELSE 'Secondary' END AS instructor_type
                    --*
            FROM dw.fact_faculty_course ff
                -- Same joins as ichair 1, just reduced to hide other fields and make it appear as an associative table.
                INNER JOIN dw.dim_faculty df ON ff.faculty_key = df.faculty_key
                INNER JOIN dw.dim_course_section dcs ON (dcs.course_section_key = ff.scheduled_course_key)
            WHERE (term = '202020' AND (subject_code = 'PHY' OR subject_code = 'ENP'))
                """).fetchall()

        cursor.close()
        connection.close()

        print(rows[0][0])

        num_no_mtgs_sched = 0
        for co_meeting in course_offering_meetings:
            if co_meeting.faculty_course_meeting_key is None:
                num_no_mtgs_sched = num_no_mtgs_sched + 1
                print('%s %s %s %s -- no meeting times or anything scheduled!!!' % (co_meeting.CMP, co_meeting.CRN, co_meeting.COURSE, co_meeting.TITLE))
            print('%s %s %s %s %s %s %s %s %s %s %s ' % (co_meeting.CMP, co_meeting.CRN, co_meeting.COURSE, co_meeting.TITLE, co_meeting.CREDHRS, co_meeting.ENRLCAP, co_meeting.term, co_meeting.part_of_term, co_meeting.DAY, co_meeting.STARTTIME, co_meeting.ENDTIME))

        print("there are", len(course_offering_meetings), "course meeting times/courses with no meeting times")
        print("number unscheduled: ", num_no_mtgs_sched)

        for instructor in course_instructors:
            if instructor.faculty_key is None:
                print('%s %s -- NO INSTRUCTOR!!!' % (instructor.term, instructor.course))
            else:
                print('%s %s %s %s %s %s %s %s %s ' % (instructor.course_section_key, instructor.term, instructor.course, instructor.faculty_key, instructor.primary_instructor, instructor.secondary_instructor, instructor.pidm, instructor.last_name, instructor.first_name))
        
        print("there are", len(course_instructors), "course offerings with/without instructors")

        #for row in faculty_rows:
        #    pidm = str(row[0])
        #    print(pidm," ", row[1], " ", row[2])
        #    print(row.PIDM, " ", row.last_name)

        #for row in rows2:
        #    print('%s %s %s %s %s %s %s %s %s %s %s %s %s %s ' % (row.CMP, row.CRN, row.COURSE, row.TITLE, row.CREDHRS, row.ENRLCAP, row.term, row.part_of_term, row.DAY, row.STARTTIME, row.ENDTIME, row.last_name, row.first_name, row.primary_instructor))

        #for row in rows3:
        #    print('%s %s %s %s %s %s ' % (row.TERMCODE, row.CRN, row.instructor_pidm, row.instructor_type, row.last_name, row.first_name))

        #for row in rows3:
        #    print(row)

        #for row in rows3:
        #    print(row)
        #for row in rows2:
        #    print(row)
        #for i in range(10):
        #    print(rows2[i].CMP, rows2[i].term, rows2[i].part_of_term)
