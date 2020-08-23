import pyodbc
from django.core.management import BaseCommand, CommandError
from django.db.models import Q
from django.template.loader import render_to_string

from banner.models import Subject as BannerSubject
from banner.models import Course as BannerCourse
from banner.models import CourseOffering as BannerCourseOffering
from banner.models import ScheduledClass as BannerScheduledClass
from banner.models import FacultyMember as BannerFacultyMember
from banner.models import OfferingInstructor as BannerOfferingInstructor
from banner.models import CourseOfferingComment as BannerCourseOfferingComment
from banner.models import SemesterCodeToImport as BannerSemesterCodeToImport
from banner.models import Room as BannerRoom
from banner.models import Building as BannerBuilding
from banner.models import SubjectToImport as BannerSubjectToImport

from four_year_plan.secret import DATA_WAREHOUSE_AUTH as DW

from django.core.mail import EmailMultiAlternatives

# https://github.com/mkleehammer/pyodbc/wiki/Objects

#print(f'DSN=warehouse;UID={DW["user"]};PWD={DW["password"]}')

class Command(BaseCommand):
    help = "Manage data warehouse information"

    def handle(self, *args, **options):
        try:
            connection = pyodbc.connect(
                f'DSN=warehouse;UID={DW["user"]};PWD={DW["password"]}')
            cursor = connection.cursor()
            rows = cursor.execute("select @@VERSION").fetchall()

            term_group = ""
            include_rooms_dict = {}
            for semester in BannerSemesterCodeToImport.objects.all():
                include_rooms_dict[semester.term_code] = semester.allow_room_copy
                if len(term_group) > 0:
                    term_group += " OR "
                term_group += "term = '"+semester.term_code+"'"

            print('include_rooms_dict: ', include_rooms_dict)

            subject_group = ""
            for banner_subject in BannerSubjectToImport.objects.all():
                if len(subject_group) > 0:
                    subject_group += " OR "
                subject_group += "subject_code = '"+banner_subject.abbrev+"'"
            
            course_offering_comments = cursor.execute("""
                SELECT ssrtext_crn as COMMENTCRN
                    , ssrtext_term_code as COMMENTTERM
                    , ssrtext_text as COMMENTTEXT
                    , course_reference_number AS CRN
                    , course AS TITLE
                    , term
                    , ssrtext_seqno AS SEQNO
                FROM dw.dim_course_section dcs -- Use the course section dimension as base.
                    -- Comments
                    LEFT OUTER JOIN dbo.ssrtext ssr ON ((ssr.ssrtext_term_code = dcs.term) AND (ssr.ssrtext_crn = dcs.course_reference_number))
                WHERE (({0}) AND ({1}) AND campus = 'U')
                    """.format(term_group, subject_group)).fetchall()
        
            course_offering_meetings = cursor.execute("""
                SELECT dcs.campus AS CMP
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
                    , dmt.meeting_time_key AS MEETINGTIMEKEY
                    , term
                    , part_of_term
                    , dr.building_code as building_code
                    , dr.room_number as room_number
                    , dr.room_capacity as room_capacity
                    , dr.building_name as building_name
                FROM dw.dim_course_section dcs -- Use the course section dimension as base.
                    -- Meeting times
                    LEFT OUTER JOIN dw.fact_course_meeting fcm ON (dcs.course_section_key = fcm.course_section_key)
                    LEFT OUTER JOIN dw.dim_meeting_time dmt ON (fcm.meeting_time_key = dmt.meeting_time_key)
                    LEFT OUTER JOIN dw.dim_room dr ON (fcm.room_key = dr.room_key)
                WHERE (({0}) AND ({1}) AND dcs.campus = 'U')
                    """.format(term_group, subject_group)).fetchall()

            course_instructors = cursor.execute("""
                SELECT dcs.*
                    , ffc.faculty_key as faculty_key
                    , ffc.primary_instructor
                    , ffc.secondary_instructor
                    , df.*
                FROM dw.dim_course_section dcs -- use the course section dimension as base.
                    LEFT OUTER JOIN dw.fact_faculty_course ffc ON (ffc.scheduled_course_key = dcs.course_section_key)
                    LEFT OUTER JOIN dw.dim_faculty df ON (ffc.faculty_key = df.faculty_key)
                WHERE (({0}) AND ({1}) AND campus = 'U')
                    """.format(term_group, subject_group)).fetchall()

            course_offerings = cursor.execute("""
                SELECT dcs.*
                FROM dw.dim_course_section dcs -- use the course section dimension as base.
                WHERE (({0}) AND ({1}) AND campus = 'U')
                    """.format(term_group, subject_group)).fetchall()

            cursor.close()
            connection.close()

            print(rows[0][0])

            number_errors = 0
            number_meetings = 0
            repeated_meetings_list = []
            class_meeting_dict = {}
            error_list = []
            rooms_created = []
            buildings_created = []
            building_room_errors = 0

            # start by clearing the banner database!
            # https://stackoverflow.com/questions/3805958/how-to-delete-a-record-in-django-models
            banner_subjects = BannerSubject.objects.all()
            for banner_subject in banner_subjects:
                # this clears all subjects, courses, course offerings and scheduled classes (cascade delete!)
                deleted_subjects = banner_subject.delete()
                #print('the following were deleted: ')
                #print(deleted_subjects)

            for co in course_offerings:
                #print('%s %s %s %s %s %s %s %s %s' % (co.campus, co.term, co.part_of_term, co.course_reference_number,
                #                                      co.subject_code, co.course_number, co.course, co.section_capacity, co.section_credit_hours))
                #print('type of credit hours: ', type(co.section_credit_hours))
                # print(int(co.section_credit_hours))

                subjects = BannerSubject.objects.filter(abbrev=co.subject_code)
                if len(subjects) == 0:
                    # create new subject
                    #print('creating new subject!')
                    subject = BannerSubject.objects.create(abbrev=co.subject_code)
                    subject.save()
                elif len(subjects) == 1:
                    #print('there is already exactly one copy of '+co.subject_code)
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
                    #print('creating new course!')
                    course = BannerCourse.objects.create(
                        subject=subject,
                        number=co.course_number,
                        title=co.course,
                        credit_hours=int(co.section_credit_hours))
                    course.save()
                elif len(courses) == 1:
                    #print('there is already exactly one copy of '+co.course+' with the appropriate properties....')
                    course = courses[0]
                else:
                    # this exits the course_offerings loop....
                    number_errors = number_errors +1
                    error_string = 'Ambiguity: there are multiple versions of '+co.course+' with the same properties; exiting....'
                    error_list.append(error_string)
                    raise CommandError(error_string)

                # apparently the CRN+term combination is guaranteed to be a unique identifier....
                banner_course_offerings = BannerCourseOffering.objects.filter(Q(crn = co.course_reference_number)&Q(term_code = co.term))

                if len(banner_course_offerings) == 0:
                    # create new course offering
                    #print('creating new course offering!')
                    if co.part_of_term == '1':
                        semester_fraction = BannerCourseOffering.FULL_SEMESTER
                    elif (co.part_of_term == 'H1') or (co.part_of_term == '2'): # '2' is used for the May session if the semester is 'Summer'
                        semester_fraction = BannerCourseOffering.FIRST_HALF_SEMESTER
                    elif (co.part_of_term == 'H2') or (co.part_of_term == '3'): # '3' is used for June session if the semester is 'Summer'
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
                elif len(banner_course_offerings) == 1:
                    # assume that all other course offering properties are consistent, since the CRN+term are supposed to be a unique identifier
                    #print('there is already one copy of the course offering with CRN '+co.course_reference_number+' for the semester '+co.term)
                    course_offering = banner_course_offerings[0] # I don't think that this actually gets used....
                else:
                    # this exits the course_offerings loop....
                    number_errors = number_errors +1
                    error_string = 'Ambiguity: there are multiple versions of the course offering '+co.course_reference_number+' - '+co.term+'; exiting....'
                    error_list.append(error_string)
                    raise CommandError(error_string)

            num_no_mtgs_sched = 0
            classes_missing_scheduled_meeting_info = []
            for co_meeting in course_offering_meetings:
                if co_meeting.faculty_course_meeting_key is None:
                    # there is nothing to do, since the course offering has already been created...should be good to go
                    num_no_mtgs_sched = num_no_mtgs_sched + 1

                    #print('%s %s %s %s -- no meeting times or anything scheduled!!!' %
                    #      (co_meeting.CMP, co_meeting.CRN, co_meeting.COURSE, co_meeting.TITLE))
                elif (co_meeting.DAY == None) or (co_meeting.STARTTIME == None) or (co_meeting.ENDTIME == None):
                    # iChair needs all of these in order to have a ScheduledClass object, so if any are missing, we need to skip it (at least for now)
                    # if all of these are missing, there's nothing to worry about.  If only some are missing, then we may need to think a bit more....
                    num_no_mtgs_sched = num_no_mtgs_sched + 1
                    #print('%s %s %s %s %s %s %s %s -- have partial meeting time information!!!' %
                    #      (co_meeting.CMP, co_meeting.CRN, co_meeting.COURSE, co_meeting.TITLE, co_meeting.DAY, co_meeting.STARTTIME, co_meeting.ENDTIME, co_meeting.MEETINGTIMEKEY))
                    if not ((co_meeting.DAY == None) and (co_meeting.STARTTIME == None) and (co_meeting.ENDTIME == None)):
                        # at least one of these is not None....
                        classes_missing_scheduled_meeting_info.append(co_meeting)
                        print('%s %s %s %s %s %s %s -- have partial meeting time information!!!' %
                            (co_meeting.CMP, co_meeting.CRN, co_meeting.COURSE, co_meeting.TITLE, co_meeting.DAY, co_meeting.STARTTIME, co_meeting.ENDTIME))
                else:
                    #print('%s %s %s %s %s %s %s %s %s %s %s ' % (co_meeting.CMP, co_meeting.CRN, co_meeting.COURSE, co_meeting.TITLE, co_meeting.CREDHRS,
                    #                                         co_meeting.ENRLCAP, co_meeting.term, co_meeting.part_of_term, co_meeting.DAY, co_meeting.STARTTIME, co_meeting.ENDTIME))
                    try:
                        course_offering = BannerCourseOffering.objects.get(Q(crn = co_meeting.CRN)&Q(term_code = co_meeting.term))
                    except BannerCourseOffering.DoesNotExist:
                        number_errors = number_errors +1
                        error_string = 'CRN '+co_meeting.CRN+' for semester '+co_meeting.term+' does not exist.'
                        error_list.append(error_string)
                        raise CommandError(error_string)
                    except BannerCourseOffering.MultipleObjectsReturned:
                        number_errors = number_errors +1
                        error_string = 'Ambiguity: there are multiple versions of CRN '+co_meeting.CRN+' for semester '+co_meeting.term+'; exiting....'
                        error_list.append(error_string)
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
                        error_list.append(error_string)
                        raise CommandError(error_string)
                    
                    if len(co_meeting.ENDTIME) == 4:
                        end_time = co_meeting.ENDTIME[:2]+':'+co_meeting.ENDTIME[2:]
                    elif len(co_meeting.ENDTIME) == 3:
                        end_time = co_meeting.ENDTIME[:1]+':'+co_meeting.ENDTIME[2:]
                    else:
                        number_errors = number_errors +1
                        error_string = 'End time is ill formed: '+co_meeting.ENDTIME
                        error_list.append(error_string)
                        raise CommandError(error_string)
                    
                    class_meeting_repeated = False
                    co_key = str(course_offering.id)
                    # https://stackoverflow.com/questions/1323410/should-i-use-has-key-or-in-on-python-dicts
                    if co_key in class_meeting_dict:
                        for mtg in class_meeting_dict[co_key]['scheduled_meetings']:
                            if (mtg['day'] == day_of_week) and (mtg['begin_at'] == start_time) and (mtg['end_at'] == end_time):
                                # We have a repeat; this can occur if a course offering is offered in two different rooms at the same
                                # time and day, which is allowed in Banner; this may be associated with a trick in Banner; not sure.
                                # Since we are not concerned with rooms during schedule editing time, we merge these multiple-meetings 
                                # into one.
                                #print('A meeting time is being repeated!!!', co_meeting.CRN, co_meeting.term)
                                #print(day_of_week, ' ', start_time, ' ', end_time)
                                #print(class_meeting_dict[co_key])
                                repeated_meetings_list.append({
                                    'CRN': co_meeting.CRN,
                                    'course': co_meeting.COURSE,
                                    'term_code': co_meeting.term,
                                    'day': day_of_week,
                                    'begin_at': start_time,
                                    'end_at': end_time
                                })
                                class_meeting_repeated = True
                        if not class_meeting_repeated:
                            class_meeting_dict[co_key]['scheduled_meetings'].append({
                                'day': day_of_week,
                                'begin_at': start_time,
                                'end_at': end_time
                            })
                    else:
                        class_meeting_dict[co_key] = {
                            'CRN': co_meeting.CRN,
                            'term_code': co_meeting.term,
                            'scheduled_meetings': []
                        }
                        class_meeting_dict[co_key]['scheduled_meetings'].append({
                            'day': day_of_week,
                            'begin_at': start_time,
                            'end_at': end_time
                        })
                    
                    room = None
                    if include_rooms_dict[co_meeting.term] and (not (co_meeting.building_code == None or co_meeting.building_code == '')) and (not (co_meeting.room_number == None or co_meeting.room_number == '')):
                        rooms = BannerRoom.objects.filter(Q(building__abbrev = co_meeting.building_code) & Q(number = co_meeting.room_number))
                        if len(rooms) > 1:
                            print('ERROR!!!  There seem to be more than one copy of this room: ', co_meeting.building_code, co_meeting.room_number)
                            building_room_errors += 1
                        elif len(rooms) == 0:
                            print('room does not exist: ', co_meeting.building_code, co_meeting.room_number)
                            # room does not yet exist; check if building exists....
                            buildings = BannerBuilding.objects.filter(abbrev = co_meeting.building_code)
                            can_create_room = True
                            if len(buildings) > 1:
                                print('ERROR!!!  There seem to be more than one copy of this building: ', co_meeting.building_code)
                                building_room_errors += 1
                                can_create_room = False
                            elif len(buildings) == 0:
                                # building does not yet exist; create it....
                                print('creating building: ', co_meeting.building_code, co_meeting.building_name)
                                building = BannerBuilding.objects.create(
                                    abbrev = co_meeting.building_code,
                                    name = co_meeting.building_name
                                )
                                buildings_created.append({
                                    'abbrev': building.abbrev,
                                    'name': building.name
                                })
                            else:
                                building = buildings[0]
                            if co_meeting.room_number == None or co_meeting.room_number == '':
                                can_create_room = False
                                print('Room has no number!')
                            if can_create_room:
                                print('creating room: ', building, co_meeting.room_number, co_meeting.room_capacity)
                                room = BannerRoom.objects.create(
                                    number = co_meeting.room_number,
                                    building = building,
                                    capacity = co_meeting.room_capacity if co_meeting.room_capacity != None else 0
                                )
                                rooms_created.append({
                                    'number': room.number,
                                    'building_abbrev': room.building.abbrev,
                                    'capacity': room.capacity
                                })
                        else:
                            room = rooms[0]
                    #else:
                    #    print('room not completely specified: ', co_meeting.COURSE, co_meeting.CRN, co_meeting.DAY, co_meeting.STARTTIME, co_meeting.ENDTIME, co_meeting.building_code, co_meeting.room_number)

                    if not class_meeting_repeated:
                        scheduled_class = BannerScheduledClass.objects.create(
                            day = day_of_week,
                            begin_at = start_time,
                            end_at = end_time,
                            course_offering = course_offering,
                            room = room
                        )
                        scheduled_class.save()
                        number_meetings += 1

            print(' ')
            print('Number of course offerings without scheduled classes: ', num_no_mtgs_sched)

            #print('Assigning instructors....')
            for co_instructor in course_instructors:
                if co_instructor.faculty_key is not None:
                    # nothing more to do in this case....
                    #print('%s %s -- NO INSTRUCTOR!!!' %
                    #      (co_instructor.term, co_instructor.course))
                #else:
                    #print('%s %s %s %s %s %s %s %s %s ' % (co_instructor.course_section_key, co_instructor.term, co_instructor.course, co_instructor.faculty_key,
                    #                                       co_instructor.primary_instructor, co_instructor.secondary_instructor, co_instructor.pidm, co_instructor.last_name, co_instructor.first_name))
                    
                    try:
                        course_offering = BannerCourseOffering.objects.get(Q(crn = co_instructor.course_reference_number)&Q(term_code = co_instructor.term))
                        #print("Found: ", course_offering)
                    except BannerCourseOffering.DoesNotExist:
                        number_errors = number_errors +1
                        error_string = 'CRN '+co_instructor.course_reference_number+' for semester '+co_instructor.term+' does not exist.'
                        error_list.append(error_string)
                        raise CommandError(error_string)
                    except BannerCourseOffering.MultipleObjectsReturned:
                        number_errors = number_errors +1
                        error_string = 'Ambiguity: there are multiple versions of CRN '+co_instructor.course_reference_number+' for semester '+co_instructor.term+'; exiting....'
                        error_list.append(error_string)
                        raise CommandError(error_string)
                    
                    try:
                        instructor = BannerFacultyMember.objects.get(pidm=co_instructor.pidm)
                        #print('instructor already exists....')
                        #raise CommandError(instructor_first_name+' '+instructor_last_name+' already exists in the database.')
                    except BannerFacultyMember.DoesNotExist:
                        instructor = BannerFacultyMember.objects.create(
                            last_name = co_instructor.last_name,
                            first_name = co_instructor.first_name,
                            formal_first_name = co_instructor.formal_first_name,
                            middle_name = co_instructor.middle_name,
                            pidm = co_instructor.pidm)
                        instructor.save()
                        #print('created instructor.... ')
                    
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

            #print('Add comments to course offerings....')
            for co_comment in course_offering_comments:
                #print(co_comment.COMMENTTERM, ' ', co_comment.term, ' ', co_comment.COMMENTCRN, ' ',co_comment.CRN, ' ',co_comment.SEQNO, ' ', co_comment.COMMENTTEXT)
                if co_comment.COMMENTTERM is not None:
                    # nothing more to do in this case; the course offering has no comments....
                    #print('%s %s -- NO COMMENT!!!' %
                    #      (co_comment.term, co_comment.CRN))
                #else:
                    try:
                        course_offering = BannerCourseOffering.objects.get(Q(crn = co_comment.CRN)&Q(term_code = co_comment.term))
                        #print("Found: ", course_offering)
                    except BannerCourseOffering.DoesNotExist:
                        number_errors = number_errors +1
                        error_string = 'CRN '+co_comment.CRN+' for semester '+co_comment.term+' does not exist.'
                        error_list.append(error_string)
                        raise CommandError(error_string)
                    except BannerCourseOffering.MultipleObjectsReturned:
                        number_errors = number_errors +1
                        error_string = 'Ambiguity: there are multiple versions of CRN '+co_comment.CRN+' for semester '+co_comment.term+'; exiting....'
                        error_list.append(error_string)
                        raise CommandError(error_string)
                    
                    course_offering_comment = BannerCourseOfferingComment.objects.create(
                        course_offering = course_offering,
                        text = co_comment.COMMENTTEXT,
                        sequence_number = co_comment.SEQNO)
                    course_offering_comment.save()

            print(' ')
            print('number of class meetings scheduled: ', number_meetings)

            print(' ')
            print('number of repeated meetings: ', len(repeated_meetings_list))
            if len(repeated_meetings_list) > 0:
                print(' ')
                print('Repeated meetings can occur if there are two or more rooms booked for a ')
                print('course for the exact same time slot.  At this point we are not allowing')
                print('this in iChair (and in any case, we are not concerned with rooms during the')
                print('schedule editing process), so we coalesce these multiple meetings into one.')
                print('If we incorporate rooms into the schedule editing process in the future we')
                print('may need to start being more careful about this...!')

            print(' ')
            print('repeated meetings (only scheduled once each): ')
            for mtg in repeated_meetings_list:
                print(mtg)

            print(' ')
            print('classes with partial meeting info: ')
            print(' ')
            for pmi_course in classes_missing_scheduled_meeting_info:
                print('   %s %s %s %s %s %s %s %s ' %
                    (pmi_course.CMP, pmi_course.CRN, pmi_course.COURSE, pmi_course.TITLE, pmi_course.DAY, pmi_course.STARTTIME, pmi_course.ENDTIME, pmi_course.MEETINGTIMEKEY))
                
            print('number of classes with partial meeting info: ', len(classes_missing_scheduled_meeting_info))
            if len(classes_missing_scheduled_meeting_info) > 0:
                print('There are some classes with only partial meeting info...need to deal with this!')
            
            print(' ')
            print('total number of errors encountered: ', number_errors)

            if len(error_list) > 0:
                for error in error_list:
                    print(error)

            context = {
                'number_meetings': number_meetings,
                'repeated_meetings_list': repeated_meetings_list,
                'classes_missing_scheduled_meeting_info': classes_missing_scheduled_meeting_info,
                'number_errors': number_errors,
                'num_no_mtgs_sched': num_no_mtgs_sched,
                'rooms_created': rooms_created,
                'buildings_created': buildings_created,
                'building_room_errors': building_room_errors
                }

            # In the following I can use just "banner_import_report.txt" (without the path) if I'm running the warehouse command at the 
            # command line, but if I'm running it as a cron job, it apparently doesn't know where the template lives (that is set in 
            # settings.py).  For this reason, I'm explicitly giving the relative path to the file here.
            # https://unix.stackexchange.com/questions/38951/what-is-the-working-directory-when-cron-executes-a-job
            #email_plaintext_message = render_to_string('../../planner/email/banner_import_report.txt', context)
            email_plaintext_message = banner_updated_message(context)

            #print(email_plaintext_message)

            msg = EmailMultiAlternatives(
                # title:
                ("Banner database updated"),
                # message:
                email_plaintext_message,
                # from:
                "noreply@taylor.edu",
                # to:
                ["knkiers@taylor.edu"]
            )
            msg.send()

        except:
            msg = EmailMultiAlternatives(
                # title:
                ("Banner database not updated"),
                # message:
                "There was a problem with updating the banner database.",
                # from:
                "noreply@taylor.edu",
                # to:
                ["knkiers@taylor.edu"]
            )
            msg.send()

def banner_updated_message(context):
    #print(context)
    num_repeated_mtgs = len(context["repeated_meetings_list"])
    num_incomplete_schedule_info = len(context["classes_missing_scheduled_meeting_info"])
    plaintext_message = """
The nightly Data Warehouse import has been completed.  The following is a summary.

Number of meetings scheduled: {0}

Number of course offerings without scheduled classes: {1}

Number of repeated meetings (only one copy of each was made): {2}
        """.format(context["number_meetings"], context["num_no_mtgs_sched"], str(num_repeated_mtgs))

    if num_repeated_mtgs > 0:
        plaintext_message += """
    Repeated class meetings...details:
            """
        for mtg in context["repeated_meetings_list"]:
            plaintext_message += """
        {0} (CRN: {1}; {2}): {3} - {4} (day: {5})
                """.format(mtg["course"], mtg["CRN"], mtg["term_code"], mtg["begin_at"], mtg["end_at"], mtg["day"])
        plaintext_message += """
Repeated meetings can occur if there are two or more rooms booked for a course for 
the exact same time slot.  At this point we are not allowing this in iChair (and in 
any case, we are not concerned with rooms during the schedule editing process), so 
we coalesce these multiple meetings into one.  If we incorporate rooms into the 
schedule editing process in the future we may need to start being more careful about 
this...!
            """
    plaintext_message += """
Number of classes with partial meeting info: {0}
        """.format(str(num_incomplete_schedule_info))
    if num_incomplete_schedule_info > 0:
        plaintext_message += """
    Classes with partial meetings...details:
            """
        for pmc in context["classes_missing_scheduled_meeting_info"]:
            plaintext_message += """
        {0} {1} {2} ({3}); {4} - {5} (day: {6}); mtg time key: {7}
                """.format(pmc.CMP, pmc.CRN, pmc.COURSE, pmc.TITLE, pmc.STARTTIME, pmc.ENDTIME, pmc.DAY, pmc.MEETINGTIMEKEY)
    
    plaintext_message += """
Number of building or room errors (due to existence of multiple versions): {0}
    """.format(context["building_room_errors"])
    if len(context["buildings_created"]) > 0:
        plaintext_message += """
Buildings created:
        """
        for bldg in context["buildings_created"]:
            plaintext_message += """
    {0}: {1}
            """.format(bldg["abbrev"], bldg["name"])
    if len(context["rooms_created"]) > 0:
        plaintext_message += """
Rooms created:
        """
        for room in context["rooms_created"]:
            plaintext_message += """
    {0} {1} (capacity: {2})
            """.format(room["building_abbrev"], room["number"], room["capacity"])
    
    plaintext_message += """
Number of errors: {0}
        """.format(context["number_errors"])
    return plaintext_message


