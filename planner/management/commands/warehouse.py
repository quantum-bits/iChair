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
from banner.models import DeliveryMethod as BannerDeliveryMethod
from planner.models import DeliveryMethod
from planner.models import FacultyMember, Department, Room

from four_year_plan.secret import DATA_WAREHOUSE_AUTH as DW

from django.core.mail import EmailMultiAlternatives

from four_year_plan.secret import ADMIN_EMAIL, NO_REPLY_EMAIL

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
            for semester in BannerSemesterCodeToImport.objects.all():
                if len(term_group) > 0:
                    term_group += " OR "
                term_group += "term = '"+semester.term_code+"'"

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
                WHERE (({0}) AND ({1}) AND (campus = 'U' OR campus = 'OCD' OR campus = 'OCP'))
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
                WHERE (({0}) AND ({1}) AND (dcs.campus = 'U' OR dcs.campus = 'OCD' OR dcs.campus = 'OCP'))
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
                WHERE (({0}) AND ({1}) AND (campus = 'U' OR campus = 'OCD' OR campus = 'OCP'))
                    """.format(term_group, subject_group)).fetchall()

            course_offerings = cursor.execute("""
                SELECT dcs.*
                FROM dw.dim_course_section dcs -- use the course section dimension as base.
                WHERE (({0}) AND ({1}) AND (campus = 'U' OR campus = 'OCD' OR campus = 'OCP'))
                    """.format(term_group, subject_group)).fetchall()

            faculty_pidms = cursor.execute("""
                SELECT df.pidm
                FROM dw.dim_faculty df
                    """).fetchall()
            
            

            #print(all_banner_faculty_pidms)
            # https://www.programiz.com/python-programming/methods/list/index
            #index = all_banner_faculty_pidms.index('502163')
            #print('The index of 502163:', index)


            
            
            # to find the building and room information for a course section with no scheduled
            # classes, can do this (for example):
            # select * from dbo.ssrmeet
            #    where ssrmeet_crn='30410' and ssrmeet_term_code='202120'
            # the building and room information are in 
            # ssrmeet_building_code and ssrmeet_room_code (which could be null or a string)


            cursor.close()
            connection.close()

            print(rows[0][0])

            number_errors = 0
            number_meetings = 0
            number_repeated_rooms_in_meeting = 0
            repeated_room_in_meetings_list = []
            class_meeting_dict = {}
            error_list = []
            rooms_created = []
            buildings_created = []
            building_room_errors = 0
            delivery_methods_created = []
            faculty_with_pidm_in_ichair_not_in_banner = []
            repeated_ichair_pidms = []
            banner_faculty_without_perfect_match_in_ichair = []
            adj_fac_w_pidm_not_in_adjunct_dept = []
            number_OCD_sections = 0
            number_OCP_sections = 0
            
            #print("Checking faculty....")
            
            # check that:
            # - all faculty in ichair.db with pidms also exist in the datawarehouse db (or at least the pidms exist)
            # - check that no two faculty in ichair.db have the same pidm
            # - check (by pidm) that all faculty in banner.db exist in ichair.db (this is checked a bit later on)
            # ...if any of the above are an issue, report that in the email

            #https://www.geeksforgeeks.org/convert-decimal-to-string-in-python/#:~:text=str()%20method%20can%20be,decimal%20to%20string%20in%20Python.
            all_banner_faculty_pidms = [str(pidm[0]) for pidm in faculty_pidms] # the entries in faculty_pidms are of Decimal type
            all_ichair_faculty_pidms = []
            for faculty in FacultyMember.objects.all():
                if not((faculty.pidm == '') or (faculty.pidm == None)): #faculty member does have a pidm
                    if faculty.pidm not in all_ichair_faculty_pidms:
                        all_ichair_faculty_pidms.append(faculty.pidm)
                    else:
                        print('pidm is repeated in iChair: ', faculty)
                        repeated_ichair_pidms.append(faculty.pidm)
                        number_errors += 1
                    if faculty.pidm not in all_banner_faculty_pidms:
                        print('pidm is in iChair, but not in banner: ', faculty)
                        faculty_with_pidm_in_ichair_not_in_banner.append(faculty.first_name + ' ' + faculty.last_name)
                        number_errors += 1

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
                if co.campus == 'OCD':
                    number_OCD_sections += 1
                    print('OCD section: %s %s %s %s %s %s %s %s' % (co.term, co.part_of_term, co.course_reference_number,
                        co.subject_code, co.course_number, co.course, co.section_capacity, co.section_credit_hours))
                if co.campus == 'OCP':
                    number_OCP_sections += 1
                    print('OCP section: %s %s %s %s %s %s %s %s' % (co.term, co.part_of_term, co.course_reference_number,
                        co.subject_code, co.course_number, co.course, co.section_capacity, co.section_credit_hours))

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
                    course = BannerCourse.objects.create(
                        subject=subject,
                        number=co.course_number,
                        title=co.course,
                        credit_hours=int(co.section_credit_hours))
                    course.save()
                    #print('creating new course!', course)
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

                    if (co.campus != BannerCourseOffering.U) and (co.campus != BannerCourseOffering.OCP) and (co.campus != BannerCourseOffering.OCD):
                        # this exits the course_offerings loop....
                        number_errors += 1
                        error_string = 'Unknown value for campus: '+co.campus+'; exiting....'
                        error_list.append(error_string)
                        raise CommandError(error_string)

                    # find the delivery type; create a new one if the one we need does not yet exist....
                    delivery_methods = BannerDeliveryMethod.objects.filter(code = co.delivery_method_code)
                    
                    if len(delivery_methods) == 1:
                        delivery_method = delivery_methods[0]
                    elif len(delivery_methods) == 0:
                        delivery_method = BannerDeliveryMethod.objects.create(
                            code = co.delivery_method_code,
                            description = co.delivery_method)
                        delivery_method.save()
                        delivery_methods_created.append(delivery_method.description)
                    else:
                        number_errors = number_errors +1
                        error_string = 'Ambiguity: there are multiple versions of '+co.delivery_method+' in our version of the Banner database....'
                        error_list.append(error_string)
                        delivery_method = delivery_methods[0]

                    course_offering = BannerCourseOffering.objects.create(
                        course = course,
                        term_code = co.term,
                        semester_fraction = semester_fraction,
                        campus = co.campus,
                        max_enrollment = co.section_capacity,
                        crn = co.course_reference_number,
                        delivery_method = delivery_method)
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
                    #print('delivery type: ', ' ', co_meeting.delivery_method_code, ' ', co_meeting.delivery_method)
                elif (co_meeting.DAY == None) or (co_meeting.STARTTIME == None) or (co_meeting.ENDTIME == None):
                    # iChair needs all of these in order to have a ScheduledClass object, so if any are missing, we need to skip it (at least for now)
                    # if all of these are missing, there's nothing to worry about.  If only some are missing, then we may need to think a bit more....
                    num_no_mtgs_sched = num_no_mtgs_sched + 1
                    #print('%s %s %s %s %s %s %s %s -- have partial meeting time information!!!' %
                    #      (co_meeting.CMP, co_meeting.CRN, co_meeting.COURSE, co_meeting.TITLE, co_meeting.DAY, co_meeting.STARTTIME, co_meeting.ENDTIME, co_meeting.MEETINGTIMEKEY))
                    #print('delivery type: ', ' ', co_meeting.delivery_method_code, ' ', co_meeting.delivery_method)
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
                    
                    #print('%s %s %s %s %s %s %s %s -- things look good....' %
                    #      (co_meeting.CMP, co_meeting.CRN, co_meeting.COURSE, co_meeting.TITLE, co_meeting.DAY, co_meeting.STARTTIME, co_meeting.ENDTIME, co_meeting.MEETINGTIMEKEY))
                    #print('delivery type: ', co_meeting.INSTRUCTIONALTYPECODE,' ', co_meeting.INSTRUCTIONALTYPEDESCRIPTION, ' ', co_meeting.delivery_method_code, ' ', co_meeting.delivery_method)

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
                                # time and day, which is allowed in Banner (and also, now, in iChair).
                                #print('A meeting time is being repeated!!!', co_meeting.CRN, co_meeting.term)
                                #print(day_of_week, ' ', start_time, ' ', end_time)
                                #print(class_meeting_dict[co_key])

                                class_meeting_repeated = True

                                #print('other meeting(s): ', class_meeting_dict[co_key])
                                #print('room for this (new) meeting: ', co_meeting.building_code, co_meeting.room_number)
                                # add the room info....
                                if (not (co_meeting.building_code == None or co_meeting.building_code == '')) and (not (co_meeting.room_number == None or co_meeting.room_number == '')):
                                    # check that we don't already have this room in the list of rooms
                                    room_repeated_this_meeting_time = False
                                    for existing_room in mtg['rooms']:
                                        if (existing_room['building_abbrev'] == co_meeting.building_code) and (existing_room['number'] == co_meeting.room_number):
                                            room_repeated_this_meeting_time = True
                                            repeated_room_in_meetings_list.append({
                                                'CRN': co_meeting.CRN,
                                                'course': co_meeting.COURSE,
                                                'term_code': co_meeting.term,
                                                'day': day_of_week,
                                                'begin_at': start_time,
                                                'end_at': end_time
                                            })
                                            number_repeated_rooms_in_meeting += 1
                                            number_errors += 1

                                    if not room_repeated_this_meeting_time:
                                        mtg['rooms'].append({
                                            'building_abbrev': co_meeting.building_code,
                                            'number': co_meeting.room_number
                                        })
                                else:
                                    print("Class meeting is repeated, but there is not complete room information....")
                                    print(class_meeting_dict[co_key])
                                    print("   building: ", co_meeting.building_code)
                                    print("   room: ", co_meeting.room_number)
                                    #print('    >>>> updated object: ', class_meeting_dict[co_key])

                        if not class_meeting_repeated:
                            rooms = []
                            if (not (co_meeting.building_code == None or co_meeting.building_code == '')) and (not (co_meeting.room_number == None or co_meeting.room_number == '')):
                                rooms.append({
                                    'building_abbrev': co_meeting.building_code,
                                    'number': co_meeting.room_number
                                })
                            
                            class_meeting_dict[co_key]['scheduled_meetings'].append({
                                'day': day_of_week,
                                'begin_at': start_time,
                                'end_at': end_time,
                                'rooms': rooms
                            })
                    else:
                        class_meeting_dict[co_key] = {
                            'course': co_meeting.COURSE,
                            'CRN': co_meeting.CRN,
                            'term_code': co_meeting.term,
                            'scheduled_meetings': []
                        }
                        rooms = []
                        if (not (co_meeting.building_code == None or co_meeting.building_code == '')) and (not (co_meeting.room_number == None or co_meeting.room_number == '')):
                            rooms.append({
                                'building_abbrev': co_meeting.building_code,
                                'number': co_meeting.room_number
                            })
                        class_meeting_dict[co_key]['scheduled_meetings'].append({
                            'day': day_of_week,
                            'begin_at': start_time,
                            'end_at': end_time,
                            'rooms': rooms
                        })
                    
                    room = None
                    if (not (co_meeting.building_code == None or co_meeting.building_code == '')) and (not (co_meeting.room_number == None or co_meeting.room_number == '')):
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
                    
                    if not class_meeting_repeated:
                        scheduled_class = BannerScheduledClass.objects.create(
                            day = day_of_week,
                            begin_at = start_time,
                            end_at = end_time,
                            course_offering = course_offering
                        )
                        if room is not None:
                            scheduled_class.rooms.add(room)
                        scheduled_class.save()
                        number_meetings += 1
                    elif (class_meeting_repeated and (room is not None)):
                        #print('we have a new room to add to an existing meeting...attempting to find the meeting and add the new room')
                        scheduled_classes = BannerScheduledClass.objects.filter(
                            Q(day = day_of_week) &
                            Q(begin_at = start_time) &
                            Q(begin_at = start_time) &
                            Q(end_at = end_time) &
                            Q(course_offering = course_offering)
                        )
                        #print("...existing scheduled classes: ", scheduled_classes)
                        if len(scheduled_classes) == 1:
                            scheduled_classes[0].rooms.add(room)
                            scheduled_classes[0].save()
                        else:
                            error_list.append("There should be exactly one scheduled class, but there is/are: {0} (CRN: {1}, {2} - {3})".format(len(scheduled_classes), co_meeting.CRN, co_meeting.COURSE, co_meeting.term))
                            number_errors += 1

            print(' ')
            print('Number of course offerings without scheduled classes: ', num_no_mtgs_sched)

            #print('Assigning instructors....')
            current_banner_instructor_pidms = []
            for co_instructor in course_instructors:
                if co_instructor.faculty_key is not None:
                    # nothing more to do in this case....
                    #print('%s %s -- NO INSTRUCTOR!!!' %
                    #      (co_instructor.term, co_instructor.course))
                #else:
                    #print('%s %s %s %s %s %s %s %s %s ' % (co_instructor.course_section_key, co_instructor.term, co_instructor.course, co_instructor.faculty_key,
                    #                                       co_instructor.primary_instructor, co_instructor.secondary_instructor, co_instructor.pidm, co_instructor.last_name, co_instructor.first_name))
                    
                    # collect the pidms for later use
                    co_instructor_pidm = str(co_instructor.pidm)
                    if co_instructor_pidm not in current_banner_instructor_pidms:
                        current_banner_instructor_pidms.append(co_instructor_pidm)
                
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

            # check if there are adjunct faculty in ichair.db who DO have a pidm but are not in the "Adjunct" department; if so, report them
            adj_rank = FacultyMember.ADJUNCT_RANK
            adj_depts = Department.objects.filter(name='Adjunct')
            if (len(adj_depts) == 1):
                for fm in FacultyMember.objects.filter (rank = adj_rank):
                    if (fm.department != adj_depts[0]) and not (fm.pidm == '' or fm.pidm is None):
                        adj_fac_w_pidm_not_in_adjunct_dept.append(fm.first_name + ' ' + fm.last_name + ' (pidm: ' + fm.pidm + ')')
                        number_errors += 1
            else:
                print("There appears to be more than one adjunct department!")
                number_errors += 1

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
            print('number of OCD course offerings: ', number_OCD_sections)

            print(' ')
            print('number of OCP course offerings: ', number_OCP_sections)

            print(' ')
            print('number of repeated rooms in meetings: ', len(repeated_room_in_meetings_list))
            if len(repeated_room_in_meetings_list) > 0:
                print(' ')
                print('There were one or more instances of a room being repeated for a given meeting time.')

                print(' ')
                print('repeated rooms in meetings (only scheduled once each): ')
                for mtg in repeated_room_in_meetings_list:
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
            print('number of new delivery methods created: ', len(delivery_methods_created))
            if len(delivery_methods_created) > 0:
                print(' ')
                print('new delivery methods added to banner.db:')
                print(' ')
                for new_delivery_method in delivery_methods_created:
                    print(new_delivery_method)

            # now check (by pidm) that the instructors in banner.db also exist in ichair.db
            for pidm in current_banner_instructor_pidms:
                ichair_fms = FacultyMember.objects.filter(pidm=pidm)
                if len(ichair_fms) != 1: #catches if there are 0 matches or more than 1
                    banner_fm = BannerFacultyMember.objects.filter(pidm=pidm)
                    number_errors += 1
                    print(' ')
                    if len(banner_fm) == 1:
                        banner_fm_name = banner_fm[0].first_name + ' ' + banner_fm[0].last_name
                        banner_faculty_without_perfect_match_in_ichair.append(banner_fm_name)
                        print('The following Banner faculty member does not have a perfect match in iChair: ', banner_fm_name)
                    else:
                        print('There is not exactly one banner faculty member with the following pidm: ', pidm)
                        number_errors += 1

            print(' ')
            print('number of errors associated with faculty members: ', len(faculty_with_pidm_in_ichair_not_in_banner) + len(repeated_ichair_pidms) + len(banner_faculty_without_perfect_match_in_ichair))
            
            if len(adj_fac_w_pidm_not_in_adjunct_dept) > 0:
                print(' ')
                print('One or more adjunct faculty members are not in the Adjunct department, even though they have pidms: ')
                for adj_fm in adj_fac_w_pidm_not_in_adjunct_dept:
                    print('   {0}'.format(adj_fm))

            # check that banner.db and ichair.db have exactly the same delivery methods....
            number_matching_ichair_delivery_methods = 0
            number_banner_delivery_methods = 0
            for banner_delivery_method in BannerDeliveryMethod.objects.all():
                number_banner_delivery_methods += 1
                ichair_delivery_methods = DeliveryMethod.objects.filter(code = banner_delivery_method.code)
                if len(ichair_delivery_methods) == 1:
                    number_matching_ichair_delivery_methods += 1
            if number_matching_ichair_delivery_methods != number_banner_delivery_methods:
                number_errors += 1

            print(' ')
            print('iChair and Banner delivery methods agree exactly?', number_matching_ichair_delivery_methods == number_banner_delivery_methods)

            # check for rooms in the iChair database that are inactive but are, nevertheless, scheduled to have classes;
            # this should never happen, but we're checking just to make sure that something hasn't been missed....
            number_scheduled_classes_in_inactive_rooms = 0
            for room in Room.objects.all():
                if room.inactive_after is not None:
                    for sc in room.scheduled_class_objects.all():
                        if sc.course_offering.semester.begin_on > room.inactive_after:
                            print('class scheduled in inactive room: ', sc, room)
                            number_scheduled_classes_in_inactive_rooms += 1
                            number_errors += 1

            if number_scheduled_classes_in_inactive_rooms > 0:
                print(' ')
                print('there are {} classes scheduled in inactive rooms'.format(number_scheduled_classes_in_inactive_rooms))

            print(' ')
            print('total number of errors encountered: ', number_errors)

            if len(error_list) > 0:
                for error in error_list:
                    print(error)

            context = {
                'number_scheduled_classes_in_inactive_rooms': number_scheduled_classes_in_inactive_rooms,
                'number_meetings': number_meetings,
                'repeated_room_in_meetings_list': repeated_room_in_meetings_list,
                'classes_missing_scheduled_meeting_info': classes_missing_scheduled_meeting_info,
                'number_errors': number_errors,
                'num_no_mtgs_sched': num_no_mtgs_sched,
                'rooms_created': rooms_created,
                'delivery_methods_created': delivery_methods_created,
                'buildings_created': buildings_created,
                'building_room_errors': building_room_errors,
                'delivery_methods_agree': number_matching_ichair_delivery_methods == number_banner_delivery_methods,
                'faculty_with_pidm_in_ichair_not_in_banner': faculty_with_pidm_in_ichair_not_in_banner,
                'repeated_ichair_pidms': repeated_ichair_pidms,
                'banner_faculty_without_perfect_match_in_ichair': banner_faculty_without_perfect_match_in_ichair,
                'class_meeting_dict': class_meeting_dict,
                'adj_fac_w_pidm_not_in_adjunct_dept': adj_fac_w_pidm_not_in_adjunct_dept
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
                NO_REPLY_EMAIL,
                # to:
                [ADMIN_EMAIL]
            )
            msg.send()

        except:
            msg = EmailMultiAlternatives(
                # title:
                ("Banner database not updated"),
                # message:
                "There was a problem with updating the banner database.",
                # from:
                NO_REPLY_EMAIL,
                # to:
                [ADMIN_EMAIL]
            )
            msg.send()

def banner_updated_message(context):
    #print(context)
    num_repeated_rooms_in_mtgs = len(context["repeated_room_in_meetings_list"])
    num_incomplete_schedule_info = len(context["classes_missing_scheduled_meeting_info"])
    plaintext_message = """
The nightly Data Warehouse import has been completed.  The following is a summary.

Number of meetings scheduled: {0}

Number of course offerings without scheduled classes: {1}

Number of repeated rooms in meetings (only one copy of each was made): {2}
        """.format(context["number_meetings"], context["num_no_mtgs_sched"], str(num_repeated_rooms_in_mtgs))

    if num_repeated_rooms_in_mtgs > 0:
        plaintext_message += """
    Repeated rooms in class meetings...details:
            """
        for mtg in context["repeated_room_in_meetings_list"]:
            plaintext_message += """
        {0} (CRN: {1}; {2}): {3} - {4} (day: {5})
                """.format(mtg["course"], mtg["CRN"], mtg["term_code"], mtg["begin_at"], mtg["end_at"], mtg["day"])
        plaintext_message += """
There were one or more instances of a room being repeated for a given meeting time.
            """

    plaintext_message += """
The following meeting times have more than one room assigned:
    """
    # https://realpython.com/iterate-through-dictionary-python/#iterating-through-keys-directly
    for co_key in context["class_meeting_dict"]:
        for scheduled_meeting in context["class_meeting_dict"][co_key]['scheduled_meetings']:
            if len(scheduled_meeting["rooms"]) > 1:
                room_string = ""
                for room in scheduled_meeting["rooms"]:
                    if len(room_string) > 0:
                        room_string += ", "
                    room_string += "{0} {1}".format(room["building_abbrev"], room["number"])
                plaintext_message += """
    CRN: {0}, term: {1} ({2}) - day: {3}, {4}-{5} ({6})
                """.format(context["class_meeting_dict"][co_key]['CRN'], 
                context["class_meeting_dict"][co_key]['term_code'], context["class_meeting_dict"][co_key]['course'],
                scheduled_meeting["day"], scheduled_meeting["begin_at"], scheduled_meeting["end_at"], room_string)
                
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
    
    number_faculty_errors = len(context["faculty_with_pidm_in_ichair_not_in_banner"]) + len(context["repeated_ichair_pidms"]) + len(context["banner_faculty_without_perfect_match_in_ichair"])
    
    plaintext_message += """
Number of errors associated with faculty members: {0}
    """.format(number_faculty_errors)

    if len(context["faculty_with_pidm_in_ichair_not_in_banner"]) > 0:
        plaintext_message += """
The following faculty members have a pidm in iChair that does not appear in Banner:
        """
        for fm in context["faculty_with_pidm_in_ichair_not_in_banner"]:
            plaintext_message += """
    {0}
            """.format(fm)

    if len(context["adj_fac_w_pidm_not_in_adjunct_dept"]) > 0:
        plaintext_message += """
One or more adjunct faculty members are not in the Adjunct department, even though they have pidms:
        """
        for fm in context["adj_fac_w_pidm_not_in_adjunct_dept"]:
            plaintext_message += """
    {0}
            """.format(fm)

    if len(context["repeated_ichair_pidms"]) > 0:
        plaintext_message += """
The following pidms are repeated in iChair:
        """
        for pidm in context["repeated_ichair_pidms"]:
            plaintext_message += """
    {0}
            """.format(pidm)

    if len(context["banner_faculty_without_perfect_match_in_ichair"]) > 0:
        plaintext_message += """
The following Banner faculty members do not have a perfect match in iChair:
        """
        for fm in context["banner_faculty_without_perfect_match_in_ichair"]:
            plaintext_message += """
    {0}
            """.format(fm)

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
    if len(context["delivery_methods_created"]) > 0:
        plaintext_message += """
Delivery methods created:
        """
        for delivery_method in context["delivery_methods_created"]:
            plaintext_message += """
    {0}
            """.format(delivery_method)

    if not context["delivery_methods_agree"]:
        plaintext_message += """
iChair and Banner delivery methods are not in exact agreement -- this error needs to be fixed!
        """

    plaintext_message += """
Number of classes scheduled in inactive rooms: {}
        """.format(context["number_scheduled_classes_in_inactive_rooms"])

    plaintext_message += """
Number of errors: {0}
        """.format(context["number_errors"])
    return plaintext_message


