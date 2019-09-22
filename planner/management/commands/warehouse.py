import pyodbc
from django.core.management import BaseCommand, CommandError
from django.db.models import Q

from banner.models import Subject as BannerSubject
from banner.models import Course as BannerCourse
from banner.models import CourseOffering as BannerCourseOffering
from banner.models import ScheduledClass as BannerScheduledClass
from banner.models import FacultyMember as BannerFacultyMember
from banner.models import OfferingInstructor as BannerOfferingInstructor

from four_year_plan.secret import DATA_WAREHOUSE_AUTH as DW

# https://github.com/mkleehammer/pyodbc/wiki/Objects


class Command(BaseCommand):
    help = "Manage data warehouse information"

    def handle(self, *args, **options):
        connection = pyodbc.connect(
            f'DSN=warehouse;UID={DW["user"]};PWD={DW["password"]}')
        cursor = connection.cursor()
        rows = cursor.execute("select @@VERSION").fetchall()
        #rows2 = cursor.execute("select campus as CMP, term, part_of_term from dw.dim_course_section dcs").fetchall()
        #faculty_rows = cursor.execute("""
        #    SELECT pidm AS PIDM, last_name, first_name 
        #    FROM dw.dim_faculty""").fetchall()
        # rows2 = cursor.execute("""
        #     SELECT campus AS CMP
        #         , subject_course AS COURSE
        #         , last_name
        #         , first_name
        #         , course_reference_number AS CRN
        #         , course AS TITLE
        #         , section_credit_hours AS CREDHRS
        #         , section_capacity AS ENRLCAP
        #         , section AS [SESSION]
        #         , dmt.start_time AS STARTTIME
        #         , dmt.end_time AS ENDTIME
        #         , dmt.day_of_week AS DAY
        #         , term
        #         , replace(days_of_week, '-', '') AS [DAYS], --'TR' as [DAYS]
        #     left(dmt.start_time, 2) + ':' + right(dmt.start_time, 2) + '-' + left(dmt.end_time, 2) + ':' +
        #     right(dmt.end_time, 2) AS [TIME], --'14:00-15:20' as [TIME]
        #         primary_df.last_name AS primary_instructor
        #         , --,secondary_df.last_name as secondary_instructor
        #     part_of_term
        #     --		,dcs.*
        #     FROM dw.dim_course_section dcs -- Use the course section dimension as base.
        #         -- Meeting times
        #         INNER JOIN dw.fact_course_meeting fcm ON (dcs.course_section_key = fcm.course_section_key)
        #         LEFT OUTER JOIN dw.dim_meeting_time dmt ON (fcm.meeting_time_key = dmt.meeting_time_key)
        #         -- Primary and Secondary Instructors
        #     INNER JOIN dw.fact_faculty_course primary_ffc ON (dcs.course_section_key = primary_ffc.scheduled_course_key AND
        #         primary_ffc.primary_instructor = 1) -- Check fact table for primary instructors
        #         --left outer join dw.fact_faculty_course secondary_ffc on (dcs.course_section_key=secondary_ffc.scheduled_course_key and secondary_ffc.secondary_instructor=1) -- Check fact table for secondary instructors
        #         LEFT OUTER JOIN dw.dim_faculty primary_df ON (primary_ffc.faculty_key = primary_df.faculty_key)
        #     WHERE (term = '202020' AND (subject_code = 'PHY' OR subject_code = 'ENP'))
        #         """).fetchall()

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
            WHERE ((term = '201990' OR term = '202010' OR term = '202020' OR term = '202050') AND (subject_code = 'MAT' OR subject_code = 'PHY' OR subject_code = 'ENP') AND campus = 'U')
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
            WHERE ((term = '201990' OR term = '202010' OR term = '202020' OR term = '202050') AND (subject_code = 'MAT' OR subject_code = 'PHY' OR subject_code = 'ENP') AND campus = 'U')
                """).fetchall()

        course_offerings = cursor.execute("""
            SELECT dcs.*
            FROM dw.dim_course_section dcs -- use the course section dimension as base.
            WHERE ((term = '201990' OR term = '202010' OR term = '202020' OR term = '202050') AND (subject_code = 'MAT' OR subject_code = 'PHY' OR subject_code = 'ENP') AND campus = 'U')
                """).fetchall()

        # rows3 = cursor.execute("""
        #     SELECT dcs.term_code as TERMCODE,
        #         dcs.course_reference_number as CRN,
        #         pidm AS instructor_pidm,
        #         last_name,
        #         first_name,
        #         CASE WHEN primary_instructor = 1
        #             THEN 'Primary'
        #         ELSE 'Secondary' END AS instructor_type
        #             --*
        #     FROM dw.fact_faculty_course ff
        #         -- Same joins as ichair 1, just reduced to hide other fields and make it appear as an associative table.
        #         INNER JOIN dw.dim_faculty df ON ff.faculty_key = df.faculty_key
        #         INNER JOIN dw.dim_course_section dcs ON (dcs.course_section_key = ff.scheduled_course_key)
        #     WHERE (term = '202020' AND (subject_code = 'PHY' OR subject_code = 'ENP'))
        #         """).fetchall()

        cursor.close()
        connection.close()

        print(rows[0][0])

        number_errors = 0
        error_list = []

        # create course sections, along with instructors and meeting times....

        # start by clearing the banner database!
        # https://stackoverflow.com/questions/3805958/how-to-delete-a-record-in-django-models
        banner_subjects = BannerSubject.objects.all()
        for banner_subject in banner_subjects:
            # this clears all subjects, courses, course offerings and scheduled classes (cascade delete!)
            deleted_subjects = banner_subject.delete()
            print('the following were deleted: ')
            print(deleted_subjects)

        for co in course_offerings:
            print('%s %s %s %s %s %s %s %s %s' % (co.campus, co.term, co.part_of_term, co.course_reference_number,
                                                  co.subject_code, co.course_number, co.course, co.section_capacity, co.section_credit_hours))
            #print('type of credit hours: ', type(co.section_credit_hours))
            # print(int(co.section_credit_hours))

            subjects = BannerSubject.objects.filter(abbrev=co.subject_code)
            if len(subjects) == 0:
                # create new subject
                print('creating new subject!')
                subject = BannerSubject.objects.create(abbrev=co.subject_code)
                subject.save()
            elif len(subjects) == 1:
                print('there is already exactly one copy of '+co.subject_code)
                subject = subjects[0]
            else:
                # this exits the course_offerings loop....
                number_errors = number_errors +1
                error_string = 'Ambiguity: there are multiple versions of '+co.subject_code+'; exiting....'
                error_list.append(error_string)
                raise CommandError(error_string)

            courses = BannerCourse.objects.filter(Q(subject=subject) & Q(number=co.course_number) & Q(
                title=co.course) & Q(credit_hours=int(co.section_credit_hours)))
            # print(courses)
            if len(courses) == 0:
                # create new course
                print('creating new course!')
                course = BannerCourse.objects.create(
                    subject=subject,
                    number=co.course_number,
                    title=co.course,
                    credit_hours=int(co.section_credit_hours))
                course.save()
            elif len(courses) == 1:
                print('there is already exactly one copy of '+co.course+' with the appropriate properties....')
                course = courses[0]
            else:
                # this exits the course_offerings loop....
                number_errors = number_errors +1
                error_string = 'Ambiguity: there are multiple versions of '+co.course+' with the same properties; exiting....'
                error_list.append(error_string)
                raise CommandError(error_string)

            # apparently the CRN+term combination is guaranteed to be a unique identifier....
            course_offerings = BannerCourseOffering.objects.filter(Q(crn = co.course_reference_number)&Q(term_code = co.term))

            if len(course_offerings) == 0:
                # create new course offering
                print('creating new course offering!')
                if co.part_of_term == '1':
                    semester_fraction = BannerCourseOffering.FULL_SEMESTER
                elif co.part_of_term == 'H1':
                    semester_fraction = BannerCourseOffering.FIRST_HALF_SEMESTER
                elif co.part_of_term == 'H2':
                    semester_fraction = BannerCourseOffering.SECOND_HALF_SEMESTER
                else:
                    # this exits the course_offerings loop....
                    number_errors = number_errors +1
                    error_string = 'Unknown value for part_of_term: '+co.part_of_term+'; exiting....'
                    error_list.append(error_string)
                    raise CommandError(error_string)

                course_offering = BannerCourseOffering.objects.create(
                    course = course,
                    term_code = co.term,
                    semester_fraction = semester_fraction,
                    max_enrollment = co.section_capacity,
                    crn = co.course_reference_number)
                course_offering.save()
            elif len(course_offerings) == 1:
                # assume that all other course offering properties are consistent, since the CRN+term are supposed to be a unique identifier
                print('there is already one copy of the course offering with CRN '+co.course_reference_number+' for the semester '+co.term)
                course_offering = course_offerings[0]
            else:
                # this exits the course_offerings loop....
                number_errors = number_errors +1
                error_string = 'Ambiguity: there are multiple versions of the course offering '+co.course_reference_number+' - '+co.term+'; exiting....'
                error_list.append(error_list)
                raise CommandError(error_list)


        num_no_mtgs_sched = 0
        for co_meeting in course_offering_meetings:
            if co_meeting.faculty_course_meeting_key is None:
                # there is nothing to do, since the course offering has already been created...should be good to go
                num_no_mtgs_sched = num_no_mtgs_sched + 1
                print('%s %s %s %s -- no meeting times or anything scheduled!!!' %
                      (co_meeting.CMP, co_meeting.CRN, co_meeting.COURSE, co_meeting.TITLE))
            else:
                print('%s %s %s %s %s %s %s %s %s %s %s ' % (co_meeting.CMP, co_meeting.CRN, co_meeting.COURSE, co_meeting.TITLE, co_meeting.CREDHRS,
                                                         co_meeting.ENRLCAP, co_meeting.term, co_meeting.part_of_term, co_meeting.DAY, co_meeting.STARTTIME, co_meeting.ENDTIME))
                try:
                    course_offering = BannerCourseOffering.objects.get(Q(crn = co_meeting.CRN)&Q(term_code = co_meeting.term))
                    print("Found: ", course_offering)
                except BannerCourseOffering.DoesNotExist:
                    number_errors = number_errors +1
                    error_string = 'CRN '+co_meeting.CRN+' for semester '+co_meeting.term+' does not exist.'
                    error_list.append(error_list)
                    raise CommandError(error_string)
                except BannerCourseOffering.MultipleObjectsReturned:
                    number_errors = number_errors +1
                    error_string = 'Ambiguity: there are multiple versions of CRN '+co_meeting.CRN+' for semester '+co_meeting.term+'; exiting....'
                    error_list.append(error_list)
                    raise CommandError(error_string)
                
                if co_meeting.DAY == 'M':
                    day_of_week = BannerScheduledClass.MONDAY
                elif co_meeting.DAY == 'T':
                    day_of_week = BannerScheduledClass.TUESDAY
                elif co_meeting.DAY == 'W':
                    day_of_week = BannerScheduledClass.WEDNESDAY
                elif co_meeting.DAY == 'R':
                    day_of_week = BannerScheduledClass.THURSDAY
                elif co_meeting.DAY == 'F':
                    day_of_week = BannerScheduledClass.FRIDAY
                else:
                    number_errors = number_errors +1
                    error_string = 'Day of week is not M-F; it is '+co_meeting.DAY+'; exiting....'
                    error_list.append(error_list)
                    raise CommandError(error_string)
                
                # https://stackoverflow.com/questions/20988835/how-to-get-the-first-2-letters-of-a-string-in-python/20989153
                if len(co_meeting.STARTTIME) == 4:
                    start_time = co_meeting.STARTTIME[:2]+':'+co_meeting.STARTTIME[2:]
                elif len(co_meeting.STARTTIME) == 3:
                    start_time = co_meeting.STARTTIME[:1]+':'+co_meeting.STARTTIME[2:]
                else:
                    number_errors = number_errors +1
                    error_string = 'Start time is ill formed: '+co_meeting.STARTTIME
                    error_list.append(error_list)
                    raise CommandError(error_string)
                
                if len(co_meeting.ENDTIME) == 4:
                    end_time = co_meeting.ENDTIME[:2]+':'+co_meeting.ENDTIME[2:]
                elif len(co_meeting.ENDTIME) == 3:
                    end_time = co_meeting.ENDTIME[:1]+':'+co_meeting.ENDTIME[2:]
                else:
                    number_errors = number_errors +1
                    error_string = 'End time is ill formed: '+co_meeting.ENDTIME
                    error_list.append(error_list)
                    raise CommandError(error_string)
                
                print('start: '+start_time+'; end: '+end_time)

                scheduled_class = BannerScheduledClass.objects.create(
                    day = day_of_week,
                    begin_at = start_time,
                    end_at = end_time,
                    course_offering = course_offering
                )
                scheduled_class.save()

        print('Number of course offerings without scheduled classes: ', num_no_mtgs_sched)

        print('Assigning instructors....')
        for co_instructor in course_instructors:
            if co_instructor.faculty_key is None:
                # nothing more to do in this case....
                print('%s %s -- NO INSTRUCTOR!!!' %
                      (co_instructor.term, co_instructor.course))
            else:
                print('%s %s %s %s %s %s %s %s %s ' % (co_instructor.course_section_key, co_instructor.term, co_instructor.course, co_instructor.faculty_key,
                                                       co_instructor.primary_instructor, co_instructor.secondary_instructor, co_instructor.pidm, co_instructor.last_name, co_instructor.first_name))
                
                try:
                    course_offering = BannerCourseOffering.objects.get(Q(crn = co_instructor.course_reference_number)&Q(term_code = co_instructor.term))
                    print("Found: ", course_offering)
                except BannerCourseOffering.DoesNotExist:
                    number_errors = number_errors +1
                    error_string = 'CRN '+co_instructor.course_reference_number+' for semester '+co_instructor.term+' does not exist.'
                    error_list.append(error_list)
                    raise CommandError(error_string)
                except BannerCourseOffering.MultipleObjectsReturned:
                    number_errors = number_errors +1
                    error_string = 'Ambiguity: there are multiple versions of CRN '+co_instructor.course_reference_number+' for semester '+co_instructor.term+'; exiting....'
                    error_list.append(error_list)
                    raise CommandError(error_string)
                
                try:
                    instructor = BannerFacultyMember.objects.get(pidm=co_instructor.pidm)
                    print('instructor already exists....')
                    #raise CommandError(instructor_first_name+' '+instructor_last_name+' already exists in the database.')
                except BannerFacultyMember.DoesNotExist:
                    instructor = BannerFacultyMember.objects.create(
                        last_name = co_instructor.last_name,
                        first_name = co_instructor.first_name,
                        formal_first_name = co_instructor.formal_first_name,
                        middle_name = co_instructor.middle_name,
                        pidm = co_instructor.pidm)
                    instructor.save()
                    print('created instructor.... ')
                
                is_primary = co_instructor.primary_instructor == 1

                if co_instructor.primary_instructor + co_instructor.secondary_instructor != 1:
                    number_errors = number_errors +1
                    error_string = 'Ambiguity: the instructor is not uniquely a primary or secondary instructor ('+co_instructor.last_name+')'
                    raise CommandError(error_string)

                offering_instructor = BannerOfferingInstructor.objects.create(
                    course_offering = course_offering,
                    instructor = instructor,
                    is_primary = is_primary)
                offering_instructor.save()
                


        print('total number of errors encountered: ', number_errors)
        if len(error_list) > 0:
            for error in error_list:
                print(error)
