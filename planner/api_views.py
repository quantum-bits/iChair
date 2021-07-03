from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from .models import *
from banner.models import Course as BannerCourse
from banner.models import CourseOffering as BannerCourseOffering
from banner.models import SemesterCodeToImport as BannerSemesterCodeToImport
from banner.models import ScheduledClass as BannerScheduledClass
from banner.models import FacultyMember as BannerFacultyMember
from banner.models import OfferingInstructor as BannerOfferingInstructor
from banner.models import Room as BannerRoom
from banner.models import Building as BannerBuilding

from .helper_functions import *

from django.shortcuts import render

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.http import HttpResponse
from django.http import FileResponse

from reportlab.pdfgen import canvas
from PyPDF2 import PdfFileWriter, PdfFileReader
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
#from reportlab.platypus import PageBreak
import datetime

import json
import re
import uuid

import collections

@login_required
def fetch_semesters_and_extra_departmental_courses(request):
    department_id = request.GET.get('departmentId')
    year_id = request.GET.get('yearId')

    department = Department.objects.get(pk=department_id)
    academic_year = AcademicYear.objects.get(pk=year_id)
    semesters = academic_year.semesters.all()
    semester_choices = []
    banner_data_exists = False
    extra_departmental_courses_planned_this_year = [{
                                                        "id": course.id,
                                                        "name": "{0} {1} - {2} ({3} hr)".format(course.subject, course.number, course.title, course.credit_hours)
                                                    } for course in department.outside_courses_this_year(academic_year)] # contains a list of all the extra-departmental courses taught by department members this year
    extra_course_ids = [course["id"] for course in extra_departmental_courses_planned_this_year]

    #print(extra_departmental_courses_planned_this_year)
    #print(department.subject_trusting_departments.all())

    other_extra_departmental_courses = []
    for subject in department.subject_trusting_departments.all():
        course_list = []
        for course in subject.courses.all():
            if course.id not in extra_course_ids:
                course_list.append({
                    "id": course.id,
                    "name": "{0} {1} - {2} ({3} hr)".format(course.subject, course.number, course.title, course.credit_hours)
                })
        other_extra_departmental_courses.append({
            "id": subject.id,
            "abbrev": subject.abbrev,
            "courses": course_list
        })
    #print(other_extra_departmental_courses)

    for semester in semesters:
        # try to find this semester in the "semesters to import" in the banner database
        banner_semester_codes_to_import = BannerSemesterCodeToImport.objects.filter(term_code=semester.banner_code)
        allow_room_requests_this_semester = False
        if len(banner_semester_codes_to_import) == 1:
            allow_room_requests_this_semester = banner_semester_codes_to_import[0].allow_room_requests

        banner_data_exists_this_semester = False
        # check if there is any banner data for the given semester, but stop checking once something is found
        for subject in department.subjects.all():
            if (not banner_data_exists_this_semester):
                banner_course_offerings = BannerCourseOffering.objects.filter(
                    Q(course__subject__abbrev=subject.abbrev) & Q(term_code=semester.banner_code))
                if (len(banner_course_offerings)>0):
                    banner_data_exists_this_semester = True
                    banner_data_exists = True
        
        if (banner_data_exists_this_semester):
            no_data_message = ''
        else:
            no_data_message = '(no Registrar data for this semester)'
        semester_choices.append({
            "semester_name": '{0} {1} (Banner code: {2}) {3} '.format(semester.name, semester.year, semester.banner_code, no_data_message),
            "id": semester.id,
            "banner_code": semester.banner_code,
            "banner_data_exists": banner_data_exists_this_semester,
            "allow_room_requests": allow_room_requests_this_semester
        })

    data = {
        "semester_choices": semester_choices,
        "banner_data_exists": banner_data_exists,
        "extra_departmental_course_choices": other_extra_departmental_courses,
        "extra_courses_this_year": extra_departmental_courses_planned_this_year
    }
    return JsonResponse(data)

@login_required
@csrf_exempt
def dismiss_message(request):
    json_data = json.loads(request.body)
    #print(json_data)
    message_id = json_data['messageId']

    message_dismissed = True
    try:
        message = Message.objects.get(pk=message_id)
        message.dismissed = True
        message.save()
    except Message.DoesNotExist:
        message_dismissed = False


    data = {
        'message_dismissed': message_dismissed
    }
    return JsonResponse(data)

@login_required
@csrf_exempt
def set_semester_to_view(request):
    json_data = json.loads(request.body)
    #print(json_data)
    request.session["semester_to_view"] = int(json_data['semesterNameId'])
    data = {
        'semester_set': True
    }
    return JsonResponse(data)

@login_required
@csrf_exempt
def create_update_courses(request):

    json_data = json.loads(request.body)
    update_dict = json_data['update']
    create_dict = json_data['create']

    #print('update: ', update_dict)
    #print('create: ', create_dict)

    creates_successful = True
    updates_successful = True
    #print('updating....')
    for update_item in update_dict:
        #print(' ')
        #print(update_item)
        # course = Course.objects.get(pk = update_item.ichair_course_id)
        try:
            course = Course.objects.get(pk=update_item["ichair_course_id"])
            #print(course)
            # check to see if the banner title already exists; if not, add it as a new one
            #print('existing banner titles: ', course.banner_title_list)
            if update_item["banner_title"] not in course.banner_title_list:
                banner_title = BannerTitle.objects.create(
                    course = course,
                    title = update_item["banner_title"]
                )
                banner_title.save()
                #print('>>>>>> new banner title created!', banner_title)
            #course.banner_title = update_item["banner_title"]
            #course.save()
        except:
            updates_successful = False
        #print('updates successful: ', updates_successful)

    #print('creating...')
    created_course_ids = []
    for create_item in create_dict:
        #print(create_item)
        try:
            subject = Subject.objects.get(pk=create_item["subject_id"])
            #print(subject)
            course = Course.objects.create(
                title=create_item["title"],
                credit_hours=create_item["credit_hours"],
                subject=subject,
                number=create_item["number"])
            course.save()
            created_course_ids.append(course.id)
            #print(course)
        except:
            creates_successful = False

    data = {
        'updates_successful': updates_successful,
        'creates_successful': creates_successful,
        'created_course_ids': created_course_ids
    }
    return JsonResponse(data)


@login_required
@csrf_exempt
def get_courses(request):
    """Get courses matching the pattern specified by a particular Banner course offering."""
    json_data = json.loads(request.body)

    number = json_data['number']
    ichair_subject_id = json_data['ichairSubjectId']
    title = json_data['title']
    credit_hours = json_data['creditHours']
    semester_id = json_data['semesterId']

    #print('number: ', number)
    #print('subject  id: ', ichair_subject_id)
    #print('title: ', title)
    #print('credit hours: ', credit_hours)

    subject = Subject.objects.get(pk=ichair_subject_id)
    semester = Semester.objects.get(pk=semester_id)
    academic_year = semester.year

    courses = Course.objects.filter(
        Q(number__startswith=number) &
        Q(subject=subject) &
        Q(credit_hours=credit_hours)
    )

    course_list = [
        {
            "subject": c.subject.abbrev,
            "number": c.number,
            "title": c.title,
            "banner_titles": c.banner_title_list,
            "credit_hours": c.credit_hours,
            "id": c.id,
            "number_offerings_this_year": c.number_offerings_this_year(academic_year),
            "year_name": '{0}-{1}'.format(academic_year.begin_on.year, academic_year.end_on.year)
        } for c in courses]

    data = {
        'courses': course_list
    }
    return JsonResponse(data)

@login_required
@csrf_exempt
def update_instructors_for_course_offering(request):
    """
    Update the instructors for an iChair course offering (including load hours).
    Possibly also change the total number of load hours available for the course offering.
    """
    user = request.user
    user_preferences = user.user_preferences.all()[0]
    user_department = user_preferences.department_to_view

    json_data = json.loads(request.body)
    
    ichair_course_offering_id = json_data['courseOfferingId']
    snapshot = json_data['snapshot']
    
    load_available = json_data['loadAvailable']
    load_available_requires_update = json_data['loadAvailableRequiresUpdate']
    instructor_list = json_data['instructorList']
    banner_course_offering_id = json_data['bannerId']
    has_delta = json_data['hasDelta']
    has_banner = json_data['hasBanner']
    delta = json_data["delta"]
    include_room_comparisons = json_data['includeRoomComparisons']

    # delta course offering actions from the model itself:
    delta_course_offering_actions = DeltaCourseOffering.actions()

    #print(ichair_course_offering_id)
    #print(load_available)
    #print(load_available_requires_update)
    #print(instructor_list)
    #print(banner_course_offering_id)

    updates_completed = True

    ico = CourseOffering.objects.get(pk=ichair_course_offering_id)
    course_department = ico.course.subject.department
    original_co_snapshot = ico.snapshot
    year = ico.semester.year

    all_instructors_exist = True
    for instructor_data in instructor_list:
        try:
            instructor = FacultyMember.objects.get(pk=instructor_data["id"])
            #print(instructor)
        except FacultyMember.DoesNotExist:
            print("oops! faculty member does not exist")
            all_instructors_exist = False
            updates_completed = False
    if all_instructors_exist:
        # delete all of the offering instructors and start over...simpler than trying to figure out the differences
        # https://stackoverflow.com/questions/9143262/delete-multiple-objects-in-django
        ico.offering_instructors.all().delete()
        for instructor_data in instructor_list:
            instructor = FacultyMember.objects.get(pk=instructor_data["id"])
            offering_instructor = OfferingInstructor.objects.create(
                course_offering=ico,
                instructor=instructor,
                load_credit = instructor_data["loadCredit"],
                is_primary= instructor_data["isPrimary"])
            offering_instructor.save()

    if load_available < 0:
        updates_completed = False
    elif load_available_requires_update and (load_available >= 0):
        ico.load_available = load_available
        ico.save()
    
    updated_load_available = ico.load_available

    ico_instructors = construct_instructor_list(ico, True)
    ico_instructors_detail = construct_ichair_instructor_detail_list(ico)

    # now update things related to deltas so can update this stuff in the UI
    #schedules_match = False
    #enrollment_caps_match = False
    #sem_fractions_match = False
    
    if user_department != course_department:
        revised_co_snapshot = ico.snapshot
        updated_fields = ["offering_instructors"]
        if original_co_snapshot["load_available"] != revised_co_snapshot["load_available"]:
            updated_fields.append("load_available")
        create_message_course_offering_update(user.username, user_department, course_department, year,
                                    original_co_snapshot, revised_co_snapshot, updated_fields)

    delta_response = None
    inst_match = False

    if has_banner and ico:
        bco = BannerCourseOffering.objects.get(pk=banner_course_offering_id)
        inst_match = instructors_match(bco, ico)

        if has_delta:
            dco = DeltaCourseOffering.objects.get(pk=delta["id"])
            delta_response = delta_update_status(bco, ico, dco, check_rooms = include_room_comparisons)
    elif (not(has_banner)) and ico:
        if has_delta:
            # in this case we are talking about a delta requested action of "create"
            dco = DeltaCourseOffering.objects.get(pk=delta["id"])
            if dco.requested_action != delta_course_offering_actions["create"]:
                print('we have a problem!!! expecting that delta is of the create type, but it is not...!')
            else:
                delta_response = delta_create_status(ico, dco, check_rooms = include_room_comparisons)
                inst_match = delta_response["request_update_instructors"]
    
    snapshot["load_available"] = original_co_snapshot["load_available"]
    snapshot["offering_instructors"] = original_co_snapshot["offering_instructors"]

    data = {
        'snapshot': snapshot,
        'instructors_detail': ico_instructors_detail,
        'instructors': ico_instructors,
        "load_available": updated_load_available,
        "updates_completed": updates_completed,
        "instructors_match": inst_match,
        'has_delta': has_delta,
        'delta': delta_response # will be None if there is no delta object
    }
    return JsonResponse(data)



@login_required
@csrf_exempt
def create_course_offering(request):
    """Create a course offering, as well as associated scheduled classes and instructors."""
    json_data = json.loads(request.body)

    course_id = json_data['courseId']
    semester_fraction = json_data['semesterFraction']
    max_enrollment = json_data['maxEnrollment']
    delivery_method = json_data['deliveryMethod']
    crn = json_data['crn']
    campus = json_data['campus'] # should be one of 'U', 'OCD' or 'OCP'
    semester_id = json_data['semesterId']
    #load_available = json_data['loadAvailable']
    meetings = json_data['meetings']
    instructor_details = json_data['instructorDetails']
    banner_course_offering_id = json_data['bannerCourseOfferingId']
    comments = json_data['comments']
    include_room_comparisons = json_data['includeRoomComparisons']

    #print('comments: ', comments)
    print(meetings)
    user = request.user
    user_preferences = user.user_preferences.all()[0]
    user_department = user_preferences.department_to_view
    faculty_to_view_ids = [fm.id for fm in user_preferences.faculty_to_view.all()]

    day_sorter_dict = {
        'M': 0,
        'T': 1,
        'W': 2,
        'R': 3,
        'F': 4
    }

    #print(course_id)
    #print(semester_fraction)
    #print(max_enrollment)
    #print(crn)
    #print(semester_id)
    #print(load_available)
    #print(meetings)
    #print(instructor_details)

    # first get the course and semester objects
    course = Course.objects.get(pk=course_id)
    semester = Semester.objects.get(pk=semester_id)
    ichair_delivery_methods = DeliveryMethod.objects.filter(code=delivery_method["code"])

    print('is summer? ', semester.is_summer())
    print('campus is OCD? ', campus == BannerCourseOffering.OCD)
    print('campus is OCP? ', campus == BannerCourseOffering.OCP)

    if semester.is_summer() or campus == BannerCourseOffering.OCD or campus == BannerCourseOffering.OCP:
        load_available = 0
        print("zero load!")
    else:
        load_available = course.credit_hours
        print("non-zero load!", load_available)

    # now create the course offering
    course_offering = CourseOffering.objects.create(
        course=course,
        semester=semester,
        semester_fraction=semester_fraction,
        max_enrollment=max_enrollment,
        load_available=load_available,
        delivery_method=ichair_delivery_methods[0] if len(ichair_delivery_methods) == 1 else None,
        crn=crn)
    course_offering.save()

    # now add the scheduled classes
    classrooms_unassigned = False
    for meeting in meetings:
        ichair_rooms_to_add = []
        if len(meeting["rooms"]) == 0:
            classrooms_unassigned = True
        for room in meeting["rooms"]:
            banner_room = BannerRoom.objects.get(pk=room["id"])
            ichair_rooms = Room.objects.filter(Q(number=banner_room.number) & Q(building__abbrev=banner_room.building.abbrev))
            if len(ichair_rooms) > 1:
                print("ERROR!!!  There appear to be more than one iChair room with the same name.")
                classrooms_unassigned = True
            elif len(ichair_rooms) == 1:
                ichair_rooms_to_add.append(ichair_rooms[0])
            else:
                print("ERROR!!!  There does not appear to be an iChair room for this Banner room.", banner_room)
                classrooms_unassigned = True

        sc = ScheduledClass.objects.create(
            course_offering=course_offering,
            day=meeting["day"],
            begin_at=meeting['beginAt'],
            end_at=meeting['endAt'])
        for ichair_room in ichair_rooms_to_add:
            sc.rooms.add(ichair_room)
        
        sc.save()

    # now add in the offering instructors; if one of them is primary, give that person all of the load
    # set to true if one of the instructors is listed as being the primary (in theory, there should be at most one primary instructor)
    instructors_created_successfully = True
    load_manipulation_performed = False
    
    for instructor_item in instructor_details:
        candidate_instructors = FacultyMember.objects.filter(pidm=instructor_item["pidm"])
        if len(candidate_instructors) == 1:
            # found exactly one match
            instructor = candidate_instructors[0]
            if instructor.is_active(semester.year):
                if instructor_item["isPrimary"]:
                    load_credit = load_available
                else:
                    load_credit = 0
                offering_instructor = OfferingInstructor.objects.create(
                    course_offering=course_offering,
                    instructor=instructor,
                    load_credit = load_credit,
                    is_primary= instructor_item["isPrimary"])
                offering_instructor.save()
                load_manipulation_performed = True
            else:
                #print('instructor is no longer active in iChair')
                instructors_created_successfully = False
        else:
            instructors_created_successfully = False

    # now add any comments
    for comment in comments["comment_list"]:
        # https://www.digitalocean.com/community/tutorials/how-to-convert-data-types-in-python-3
        public_comment = CourseOfferingPublicComment.objects.create(
            course_offering = course_offering,
            text = comment["text"][:60],
            sequence_number = float(comment["sequence_number"])
        )
        public_comment.save()


    # now should do the delta stuff and return that, too
    # >>> Note: if the room list is ever included (as above), will need to be more careful about the sorting
    # >>> that is done below, since the room list order and the meeting times order are correlated!
    # ...at this point, since we are copying this information from Banner, and since we are not getting room
    # information from Banner, we leave the rooms unspecified.
    # could use the method sort_rooms(...) for this....
    presorted_ico_meeting_times_list, presorted_ico_room_list = class_time_and_room_summary(
        course_offering.scheduled_classes.all(), new_format = True)
    # do some sorting so that the meeting times (hopefully) come out in the same order for the bco and ico cases....
    ico_meeting_times_list = sorted(
        presorted_ico_meeting_times_list, key=lambda item: (day_sorter_dict[item[:1]]))

    # sort the rooms so that the sort order matches that of the meeting times....
    ico_room_list = sort_rooms(presorted_ico_meeting_times_list, ico_meeting_times_list, presorted_ico_room_list)

    ico_instructors = construct_instructor_list(course_offering, True)
    ico_instructors_detail = construct_ichair_instructor_detail_list(course_offering)

    meeting_times_detail = construct_meeting_times_detail(course_offering, True)

    # don't state the requested_action, since the default is set to UPDATE anyways
    # also, don't set the various update options to True; the default is False, and that is fine...
    # no sense asking the registrar to change something just because we couldn't copy it correctly into iChair
    delta_object = DeltaCourseOffering.objects.create(
        crn=crn,
        semester=semester,
        course_offering=course_offering
    )
    # now fetch the banner course offering object
    bco = BannerCourseOffering.objects.get(pk=banner_course_offering_id)
    
    delta_response = delta_update_status(bco, course_offering, delta_object, check_rooms = include_room_comparisons)

    available_instructors = user_department.available_instructors(semester.year, course_offering, faculty_to_view_ids)

    #ico_room_list = ['---' for mt in ico_meeting_times_list] # make a list of strings that is the same length as meeting_times

    ichair_course_offering_data = {
        "course_offering_id": course_offering.id,
        "course_id": course_offering.course.id,
        "meeting_times": ico_meeting_times_list,
        "meeting_times_detail": meeting_times_detail,
        "rooms": ico_room_list,
        "instructors": ico_instructors,
        "instructors_detail": ico_instructors_detail,
        "available_instructors": available_instructors,
        "snapshot": course_offering.snapshot,
        "change_can_be_undone": {
            "max_enrollment": False,
            "comments": False,
            "semester_fraction": False,
            "instructors": False,
            "meeting_times": False,
            "delivery_method": False,
        },
        "load_available": course_offering.load_available,
        "semester": course_offering.semester.name.name,
        "semester_fraction": int(course_offering.semester_fraction),
        "max_enrollment": int(course_offering.max_enrollment),
        "course": course_offering.course.subject.abbrev+' '+course_offering.course.number,
        "number": course_offering.course.number,
        "credit_hours": course_offering.course.credit_hours,
        "course_title": course_offering.course.title,
        "comments": course_offering.comment_list(),
        "delivery_method": create_delivery_method_dict(course_offering.delivery_method)
    }
    agreement_update = {
        "instructors_match": instructors_match(bco, course_offering),
        "meeting_times_match": scheduled_classes_match(bco, course_offering, check_rooms = include_room_comparisons),
        "max_enrollments_match": max_enrollments_match(bco, course_offering),
        "semester_fractions_match": semester_fractions_match(bco, course_offering),
        "public_comments_match": public_comments_match(bco, course_offering),
        "delivery_methods_match": delivery_methods_match(bco, course_offering),
    }

    data = {
        'instructors_created_successfully': instructors_created_successfully,
        'delta': delta_response,
        'ichair_course_offering_data': ichair_course_offering_data,
        'agreement_update': agreement_update,
        'load_manipulation_performed': load_manipulation_performed,
        'classrooms_unassigned': classrooms_unassigned
    }
    return JsonResponse(data)


@login_required
@csrf_exempt
def banner_comparison_data(request):

    user = request.user
    user_preferences = user.user_preferences.all()[0]
    
    json_data = json.loads(request.body)
    department_id = json_data['departmentId']
    year_id = json_data['yearId']
    semester_ids = json_data['semesterIds']

    extra_departmental_course_id_list = json_data['extraDepartmentalCourseIdList']
    include_room_comparisons = json_data['includeRoomComparisons']

    #print("include room comparisons?", include_room_comparisons)

    day_sorter_dict = {
        'M': 0,
        'T': 1,
        'W': 2,
        'R': 3,
        'F': 4
    }

    semester_sorter_dict = {}
    counter = 0
    for semester_id in semester_ids:
        semester_sorter_dict[semester_id] = counter
        counter = counter+1

    #print('semesters')
    #print(semester_sorter_dict)

    department = Department.objects.get(pk=department_id)
    academic_year = AcademicYear.objects.get(pk = year_id)

    faculty_to_view_ids = [fm.id for fm in user_preferences.faculty_to_view.all()]

    semester_fractions = {
        'full': CourseOffering.FULL_SEMESTER,
        'first_half': CourseOffering.FIRST_HALF_SEMESTER,
        'second_half': CourseOffering.SECOND_HALF_SEMESTER
    }

    # delta course offering actions from the model itself:
    delta_course_offering_actions = DeltaCourseOffering.actions()

    # https://stackoverflow.com/questions/483666/python-reverse-invert-a-mapping
    semester_fractions_reverse = {v: k for k, v in semester_fractions.items()}

    # process:
    # loop through all banner course offerings and try to assign CRNs to iChair course offerings
    #   - first, unlink the courses (i.e., basically start from scratch, in case things have changed either in banner or ichair)
    #   - for each banner course, check iChair course candidates
    #       - assign CRN to iChair course (and ichair_id to banner course) if following criteria are satisfied:
    #           - course itself agrees (subject, number, credit hours, title or banner_title)
    #           - semester agrees
    #           - iChair course has not already been assigned a CRN
    #       - if multiple iChair course offerings match according to the above criteria, find the "best" fit, based on days, times and instructors
    #           - if there is an exact fit on days and times, assign the CRN to the iChair offering
    #           - if multiple fits on days and times, proceed to check instructors
    #               - if instructors agree for exactly one course offering, assign the CRN to the iChair offering
    #               - if zero or multiple course offerings agree, proceed to check semester fraction

    # now we construct some objects that contain a bit of information about the iChair versions of the extra-departmental
    # courses so that that can be used to get banner course offerings
    extra_departmental_courses = [{
        "credit_hours": course.credit_hours,
        "title": course.title,
        "subject_abbrev": course.subject.abbrev,
        "number": course.number,
        "banner_titles": course.banner_title_list
        } for course in Course.objects.filter(pk__in = extra_departmental_course_id_list)]

    #print("extra-departmental courses: ", extra_departmental_courses)

    course_offering_data = []

    index = 0
    for semester_id in semester_ids:
        semester = Semester.objects.get(pk=semester_id)
        term_code = semester.banner_code

        banner_semester_codes_to_import = BannerSemesterCodeToImport.objects.filter(term_code=term_code)
        allow_room_requests_this_semester = False
        include_room_comparisons_this_semester = False
        if len(banner_semester_codes_to_import) == 1:
            allow_room_requests_this_semester = banner_semester_codes_to_import[0].allow_room_requests
            include_room_comparisons_this_semester = include_room_comparisons and allow_room_requests_this_semester
            
        # eventually expand this to include extra-departmental courses taught by dept...?
        for subject in department.subjects_including_outside_courses(semester, extra_departmental_course_id_list):
            # first should reset all crns of the iChair course offerings, so we start with a clean slate
            # should also reset all ichair_ids for the Banner course offerings, for the same reason (that's done below)

            # RESET CRNs of all corresponding iChair course offerings (i.e., start from scratch)
            
            is_own_subject = subject.department == department
            
            for course_offering in subject.restricted_course_offerings(department, semester, extra_departmental_course_id_list):
            #CourseOffering.objects.filter(
            #        Q(semester=semester) &
            #        Q(course__subject=subject)):
                course_offering.crn = None
                course_offering.save()

            # the following find all banner course offerings for this subject and semester if the department owns the subject;
            # otherwise it only looks for course offerings associated with the courses in the list extra_departmental_courses
            banner_course_offerings = BannerCourseOffering.filtered_objects(subject, term_code, is_own_subject, extra_departmental_courses)
 
            # the following is an initial round of attempting to link up banner courses with iChair courses
            # once this is done, we can cycle through the linked courses (which should be 1-to-1 at that point) and add them to a list
            # then we can cycle through any unlinked courses on both sides and add them to the list
            # then we should sort the list so the order doesn't seem crazy

            for bco in banner_course_offerings:
                #print(bco," ", bco.term_code, " ", bco.crn)
                # attempt to assign an iChair course offering to the banner one
                find_ichair_course_offering(bco, semester, subject)

            # now we cycle through all the banner course offerings and add them to the list
            for bco in banner_course_offerings:
                # https://stackoverflow.com/questions/7108080/python-get-the-first-character-of-the-first-string-in-a-list
                # do some sorting so that the meeting times (hopefully) come out in the same order for the bco and ico cases....
                if not allow_room_requests_this_semester:
                    presorted_bco_meeting_times_list = class_time_and_room_summary(
                        bco.scheduled_classes.all(), include_rooms=False, new_format = True)
                    bco_meeting_times_list = sorted(
                        presorted_bco_meeting_times_list, key=lambda item: (day_sorter_dict[item[:1]]))
                    bco_room_list = ['---' for mt in bco_meeting_times_list]
                else:
                    presorted_bco_meeting_times_list, presorted_bco_room_list = class_time_and_room_summary(
                        bco.scheduled_classes.all(), new_format = True)
                    # do some sorting so that the meeting times (hopefully) come out in the same order for the bco and ico cases....
                    bco_meeting_times_list = sorted(
                        presorted_bco_meeting_times_list, key=lambda item: (day_sorter_dict[item[:1]]))
                    # sort the rooms so that the sort order matches that of the meeting times....
                    bco_room_list = sort_rooms(presorted_bco_meeting_times_list, bco_meeting_times_list, presorted_bco_room_list)

                bco_instructors = construct_instructor_list(bco)
                bco_instructors_detail = construct_instructor_detail_list(bco)

                bco_meeting_times_detail = construct_meeting_times_detail(bco, True)

                course_offering_item = {
                    "index": index,  # used in the UI as a unique key
                    "semester": semester.name.name,
                    "term_code": term_code,
                    "allow_room_requests": allow_room_requests_this_semester, # whether room edit requests may be made for this semester (regardless of whether the user wants to do them)
                    "include_room_comparisons": include_room_comparisons_this_semester, # whether to include room comparisons as part of the meeting time comparisons
                    "semester_id": semester.id,
                    "course_owned_by_user": department == subject.department,
                    "course": bco.course.subject.abbrev+' '+bco.course.number,
                    "credit_hours": bco.course.credit_hours,
                    "course_title": bco.course.title,
                    "schedules_match": False,
                    "instructors_match": False,
                    "semester_fractions_match": False,
                    "enrollment_caps_match": False,
                    "public_comments_match": False,
                    "delivery_methods_match": False,
                    "ichair_subject_id": subject.id,
                    "banner": {
                        "course_offering_id": bco.id,
                        "meeting_times": bco_meeting_times_list,
                        "meeting_times_detail": bco_meeting_times_detail,
                        "rooms": bco_room_list,
                        "instructors": bco_instructors,
                        "instructors_detail": bco_instructors_detail,
                        "term_code": bco.term_code,
                        "semester_fraction": int(bco.semester_fraction),
                        "max_enrollment": int(bco.max_enrollment),
                        "course": bco.course.subject.abbrev+' '+bco.course.number,
                        "number": bco.course.number,
                        "credit_hours": bco.course.credit_hours,
                        "course_title": bco.course.title,
                        "comments": bco.comment_list(),
                        "delivery_method": create_delivery_method_dict(bco.delivery_method)
                    },
                    "ichair": {},
                    # options for possible matches (if the banner course offering is linked to an iChair course offering, this list remains empty)
                    "ichair_options": [],
                    "banner_options": [],
                    "has_banner": True,
                    "has_ichair": False,
                    "linked": False,
                    "delta": None,
                    "all_OK": False,
                    "crn": bco.crn,
                    "campus": bco.campus
                }
                index = index + 1

                if bco.is_linked:
                    # get the corresponding iChair course offering
                    try:
                        ico = CourseOffering.objects.get(pk=bco.ichair_id)
                        presorted_ico_meeting_times_list, presorted_ico_room_list = class_time_and_room_summary(
                            ico.scheduled_classes.all(), new_format = True)
                        # do some sorting so that the meeting times (hopefully) come out in the same order for the bco and ico cases....
                        ico_meeting_times_list = sorted(
                            presorted_ico_meeting_times_list, key=lambda item: (day_sorter_dict[item[:1]]))

                        # sort the rooms so that the sort order matches that of the meeting times....
                        ico_room_list = sort_rooms(presorted_ico_meeting_times_list, ico_meeting_times_list, presorted_ico_room_list)

                        ico_instructors = construct_instructor_list(ico, True)
                        ico_instructors_detail = construct_ichair_instructor_detail_list(ico)
                        available_instructors = department.available_instructors(academic_year, ico, faculty_to_view_ids)

                        meeting_times_detail = construct_meeting_times_detail(ico, True)

                        # check to see if there are relevant delta objects
                        # we're only interested in "update" types of delta objects, since
                        # they are the only ones that include a crn (for a banner course offering)
                        # and are tied to a course offering in the iChair database
                        # (the create and delete deltas only have an iChair course offering and a crn, respectively)

                        delta_objects = DeltaCourseOffering.objects.filter(
                            Q(crn=bco.crn) &
                            Q(course_offering=ico) &
                            Q(requested_action=delta_course_offering_actions["update"]))

                        delta_exists = False
                        if len(delta_objects) > 0:
                            delta_exists = True
                            #print('delta object(s) found for', bco)
                            recent_delta_object = delta_objects[0]
                            for delta_object in delta_objects:
                                #print(delta_object, delta_object.updated_at)
                                if delta_object.updated_at > recent_delta_object.updated_at:
                                    recent_delta_object = delta_object
                                    #print('found more recent!',
                                    #      recent_delta_object.updated_at)

                            delta_response = delta_update_status(
                                bco, ico, recent_delta_object, check_rooms = include_room_comparisons_this_semester)
                            course_offering_item["delta"] = delta_response

                        if delta_exists:
                            # either these properties already match, or we are going to request a change from the registrar so that they do match
                            schedules_match = scheduled_classes_match(
                                bco, ico, include_room_comparisons_this_semester) or delta_response["request_update_meeting_times"]
                            inst_match = instructors_match(
                                bco, ico) or delta_response["request_update_instructors"]
                            sem_fractions_match = semester_fractions_match(
                                bco, ico) or delta_response["request_update_semester_fraction"]
                            enrollment_caps_match = max_enrollments_match(
                                bco, ico) or delta_response["request_update_max_enrollment"]
                            comments_match = public_comments_match(
                                bco, ico) or delta_response["request_update_public_comments"]
                            del_methods_match = delivery_methods_match(
                                bco, ico) or delta_response["request_update_delivery_method"]
                        else:
                            schedules_match = scheduled_classes_match(bco, ico, include_room_comparisons_this_semester)
                            inst_match = instructors_match(bco, ico)
                            sem_fractions_match = semester_fractions_match(
                                bco, ico)
                            enrollment_caps_match = max_enrollments_match(
                                bco, ico)
                            comments_match = public_comments_match(
                                bco, ico)
                            del_methods_match = delivery_methods_match(
                                bco, ico)

                        course_offering_item["ichair"] = {
                            "course_offering_id": ico.id,
                            "course_id": ico.course.id,
                            "meeting_times": ico_meeting_times_list,
                            "meeting_times_detail": meeting_times_detail,
                            "rooms": ico_room_list,
                            "instructors": ico_instructors,
                            "instructors_detail": ico_instructors_detail,
                            "available_instructors": available_instructors,
                            "snapshot": ico.snapshot,
                            "change_can_be_undone": {
                                "max_enrollment": False,
                                "comments": False,
                                "semester_fraction": False,
                                "instructors": False,
                                "meeting_times": False,
                                "delivery_method": False,
                            },
                            "load_available": ico.load_available,
                            "semester": ico.semester.name.name,
                            "semester_fraction": int(ico.semester_fraction),
                            "max_enrollment": int(ico.max_enrollment),
                            "course": ico.course.subject.abbrev+' '+ico.course.number,
                            "number": ico.course.number,
                            "credit_hours": ico.course.credit_hours,
                            "course_title": ico.course.title,
                            "comments": ico.comment_list(),
                            "delivery_method": create_delivery_method_dict(ico.delivery_method)
                        }
                        course_offering_item["has_ichair"] = True
                        course_offering_item["linked"] = True
                        course_offering_item["schedules_match"] = schedules_match
                        course_offering_item["instructors_match"] = inst_match
                        course_offering_item["semester_fractions_match"] = sem_fractions_match
                        course_offering_item["enrollment_caps_match"] = enrollment_caps_match
                        course_offering_item["public_comments_match"] = comments_match
                        course_offering_item["delivery_methods_match"] = del_methods_match

                        course_offering_item["all_OK"] = schedules_match and inst_match and sem_fractions_match and enrollment_caps_match and comments_match and del_methods_match

                    except CourseOffering.DoesNotExist:
                        print(
                            'OOPS!  Looking for a course offering that does not exist....')
                        print(bco)

                else:
                    # look for possible ichair course offering matches for this unlinked banner course offering
                    unlinked_ichair_course_offerings = find_unlinked_ichair_course_offerings(
                        bco, semester, subject)
                    #print('bco...', bco)
                    #print('some iChair options:')
                    for unlinked_ico in unlinked_ichair_course_offerings:
                        #print(unlinked_ico)
                        presorted_ico_meeting_times_list, presorted_ico_room_list = class_time_and_room_summary(
                            unlinked_ico.scheduled_classes.all(), new_format = True)
                        # do some sorting so that the meeting times (hopefully) come out in the same order for the bco and ico cases....
                        ico_meeting_times_list = sorted(
                            presorted_ico_meeting_times_list, key=lambda item: (day_sorter_dict[item[:1]]))
                        # sort the rooms so that the sort order matches that of the meeting times....
                        ico_room_list = sort_rooms(presorted_ico_meeting_times_list, ico_meeting_times_list, presorted_ico_room_list)

                        ico_instructors = construct_instructor_list(
                            unlinked_ico, True)
                        ico_instructors_detail = construct_ichair_instructor_detail_list(unlinked_ico)
                        available_instructors = department.available_instructors(academic_year, unlinked_ico, faculty_to_view_ids)

                        meeting_times_detail = construct_meeting_times_detail(unlinked_ico, True)
                        course_offering_item["ichair_options"].append({
                            "course_title": unlinked_ico.course.title,
                            "comments": unlinked_ico.comment_list(),
                            "delivery_method": create_delivery_method_dict(unlinked_ico.delivery_method),
                            "course": unlinked_ico.course.subject.abbrev+' '+unlinked_ico.course.number,
                            "number": unlinked_ico.course.number,
                            "credit_hours": unlinked_ico.course.credit_hours,
                            "course_offering_id": unlinked_ico.id,
                            "course_id": unlinked_ico.course.id,
                            "meeting_times": ico_meeting_times_list,
                            "meeting_times_detail": meeting_times_detail,
                            "rooms": ico_room_list,
                            "instructors": ico_instructors,
                            "instructors_detail": ico_instructors_detail,
                            "available_instructors": available_instructors,
                            "snapshot": unlinked_ico.snapshot,
                            "change_can_be_undone": {
                                "max_enrollment": False,
                                "comments": False,
                                "semester_fraction": False,
                                "instructors": False,
                                "meeting_times": False,
                                "delivery_method": False,
                            },
                            "load_available": unlinked_ico.load_available,
                            "semester": unlinked_ico.semester.name.name,
                            "semester_fraction": int(unlinked_ico.semester_fraction),
                            "max_enrollment": int(unlinked_ico.max_enrollment)})

                    # now check to see if there is a delta object with requested_action being of the "delete" type
                    delta_objects = DeltaCourseOffering.objects.filter(
                        Q(crn=bco.crn) &
                        Q(semester=semester) &
                        Q(requested_action=delta_course_offering_actions["delete"]))

                    delta_exists = False
                    if len(delta_objects) > 0:
                        delta_exists = True
                        #print(
                        #    '>>>>>>>>>>>>>>>>>>>>>>delete-type delta object(s) found for', bco)
                        recent_delta_object = delta_objects[0]
                        for delta_object in delta_objects:
                            #print(delta_object, delta_object.updated_at)
                            if delta_object.updated_at > recent_delta_object.updated_at:
                                recent_delta_object = delta_object
                                #print('found more recent!',
                                #      recent_delta_object.updated_at)

                    if delta_exists:
                        delta_response = delta_delete_status(
                            recent_delta_object)

                        # these will match after the course offering is deleted by the registrar
                        course_offering_item["schedules_match"] = True
                        course_offering_item["instructors_match"] = True
                        course_offering_item["semester_fractions_match"] = True
                        course_offering_item["enrollment_caps_match"] = True
                        course_offering_item["public_comments_match"] = True
                        course_offering_item["delivery_methods_match"] = True

                        course_offering_item["all_OK"] = True
                        course_offering_item["delta"] = delta_response

                course_offering_data.append(course_offering_item)

            # and now we go through the remaining iChair course offerings (i.e., the ones that have not been linked to banner course offerings)
            for ico in subject.restricted_course_offerings_no_crn(department, semester, extra_departmental_course_id_list):

                presorted_ico_meeting_times_list, presorted_ico_room_list = class_time_and_room_summary(ico.scheduled_classes.all(), new_format = True)
                # do some sorting so that the meeting times (hopefully) come out in the same order for the bco and ico cases....
                ico_meeting_times_list = sorted(
                    presorted_ico_meeting_times_list, key=lambda item: (day_sorter_dict[item[:1]]))

                # sort the rooms so that the sort order matches that of the meeting times....
                ico_room_list = sort_rooms(presorted_ico_meeting_times_list, ico_meeting_times_list, presorted_ico_room_list)

                ico_instructors = construct_instructor_list(ico, True)
                ico_instructors_detail = construct_ichair_instructor_detail_list(ico)
                available_instructors = department.available_instructors(academic_year, ico, faculty_to_view_ids)

                meeting_times_detail = construct_meeting_times_detail(ico, True)

                unlinked_banner_course_offerings = find_unlinked_banner_course_offerings(
                    ico, term_code, subject)

                banner_options = []
                for unlinked_bco in unlinked_banner_course_offerings:
                    #print(unlinked_bco)
                    if not allow_room_requests_this_semester:
                        presorted_bco_meeting_times_list = class_time_and_room_summary(
                            unlinked_bco.scheduled_classes.all(), include_rooms=False, new_format = True)
                        bco_meeting_times_list = sorted(
                            presorted_bco_meeting_times_list, key=lambda item: (day_sorter_dict[item[:1]]))
                        bco_room_list = ['---' for mt in bco_meeting_times_list]
                    else:
                        presorted_bco_meeting_times_list, presorted_bco_room_list = class_time_and_room_summary(
                            unlinked_bco.scheduled_classes.all(), new_format = True)
                        # do some sorting so that the meeting times (hopefully) come out in the same order for the bco and ico cases....
                        bco_meeting_times_list = sorted(
                            presorted_bco_meeting_times_list, key=lambda item: (day_sorter_dict[item[:1]]))
                        # sort the rooms so that the sort order matches that of the meeting times....
                        bco_room_list = sort_rooms(presorted_bco_meeting_times_list, bco_meeting_times_list, presorted_bco_room_list)

                    bco_instructors = construct_instructor_list(
                        unlinked_bco)
                    bco_instructors_detail = construct_instructor_detail_list(
                        unlinked_bco)
                    bco_meeting_times_detail = construct_meeting_times_detail(
                        unlinked_bco, True)

                    banner_options.append({
                        "crn": unlinked_bco.crn,
                        "campus": unlinked_bco.campus,
                        "course_title": unlinked_bco.course.title,
                        "comments": unlinked_bco.comment_list(),
                        "delivery_method": create_delivery_method_dict(unlinked_bco.delivery_method),
                        "course": unlinked_bco.course.subject.abbrev+' '+unlinked_bco.course.number,
                        "number": unlinked_bco.course.number,
                        "credit_hours": unlinked_bco.course.credit_hours,
                        "course_offering_id": unlinked_bco.id,
                        "meeting_times": bco_meeting_times_list,
                        "rooms": bco_room_list,
                        "meeting_times_detail": bco_meeting_times_detail,
                        "instructors": bco_instructors,
                        "instructors_detail": bco_instructors_detail,
                        "term_code": unlinked_bco.term_code,
                        "semester_fraction": int(unlinked_bco.semester_fraction),
                        "max_enrollment": int(unlinked_bco.max_enrollment)})

                # now check to see if there is a delta object with requested_action being of the "create" type
                delta_objects = DeltaCourseOffering.objects.filter(
                    Q(crn__isnull=True) &
                    Q(course_offering=ico) &
                    Q(requested_action=delta_course_offering_actions["create"]))

                delta_exists = False
                if len(delta_objects) > 0:
                    delta_exists = True
                    #print('delta object(s) found for', ico)
                    recent_delta_object = delta_objects[0]
                    for delta_object in delta_objects:
                        #print(delta_object, delta_object.updated_at)
                        if delta_object.updated_at > recent_delta_object.updated_at:
                            recent_delta_object = delta_object
                            #print('found more recent!',
                            #      recent_delta_object.updated_at)

                if delta_exists:
                    delta_response = delta_create_status(
                        ico, recent_delta_object, check_rooms = include_room_comparisons_this_semester)
                    schedules_match = delta_response["request_update_meeting_times"]
                    inst_match = delta_response["request_update_instructors"]
                    sem_fractions_match = delta_response["request_update_semester_fraction"]
                    enrollment_caps_match = delta_response["request_update_max_enrollment"]
                    comments_match = delta_response["request_update_public_comments"]
                    del_methods_match = delta_response["request_update_delivery_method"]
                else:
                    delta_response = None
                    schedules_match = False
                    inst_match = False
                    sem_fractions_match = False
                    enrollment_caps_match = False
                    comments_match = False
                    del_methods_match = False

                course_offering_item = {
                    "index": index,
                    "semester": semester.name.name,
                    "semester_id": semester.id,
                    "course_owned_by_user": department == subject.department,
                    "term_code": term_code,
                    "allow_room_requests": allow_room_requests_this_semester, # whether room edit requests may be made for this semester (regardless of whether the user wants to do them)
                    "include_room_comparisons": include_room_comparisons_this_semester, # whether to include room comparisons as part of the meeting time comparisons
                    "course": ico.course.subject.abbrev+' '+ico.course.number,
                    "credit_hours": ico.course.credit_hours,
                    "course_title": ico.course.title,
                    "schedules_match": schedules_match,
                    "instructors_match": inst_match,
                    "semester_fractions_match": sem_fractions_match,
                    "enrollment_caps_match": enrollment_caps_match,
                    "public_comments_match": comments_match,
                    "delivery_methods_match": del_methods_match,
                    "ichair_subject_id": subject.id,
                    "banner": {},
                    "ichair": {
                        "course_offering_id": ico.id,
                        "course_id": ico.course.id,
                        "meeting_times": ico_meeting_times_list,
                        "meeting_times_detail": meeting_times_detail,
                        "rooms": ico_room_list,
                        "instructors": ico_instructors,
                        "instructors_detail": ico_instructors_detail,
                        "available_instructors": available_instructors,
                        "snapshot": ico.snapshot,
                        "change_can_be_undone": {
                            "max_enrollment": False,
                            "comments": False,
                            "semester_fraction": False,
                            "instructors": False,
                            "meeting_times": False,
                            "delivery_method": False,
                        },
                        "load_available": ico.load_available,
                        "semester": ico.semester.name.name,
                        "semester_fraction": int(ico.semester_fraction),
                        "max_enrollment": int(ico.max_enrollment),
                        "course": ico.course.subject.abbrev+' '+ico.course.number,
                        "number": ico.course.number,
                        "credit_hours": ico.course.credit_hours,
                        "course_title": ico.course.title,
                        "comments": ico.comment_list(),
                        "delivery_method": create_delivery_method_dict(ico.delivery_method)
                    },
                    # options for possible matches (if the banner course offering is linked to an iChair course offering, this list remains empty)
                    "ichair_options": [],
                    "banner_options": banner_options,
                    "has_banner": False,
                    "has_ichair": True,
                    "linked": False,
                    "delta": delta_response,
                    "all_OK": schedules_match and inst_match and sem_fractions_match and enrollment_caps_match and comments_match and del_methods_match,
                    "crn": None,
                    "campus": None
                }
                index = index + 1
                course_offering_data.append(course_offering_item)

    sorted_course_offerings = sorted(course_offering_data, key=lambda item: (
        semester_sorter_dict[item["semester_id"]], item["course"]))

    available_rooms = [{
        "id": room.id,
        "short_name": room.short_name
        } for room in Room.objects.all()]

    available_delivery_methods = [{
        "id": delivery_method.id,
        "code": delivery_method.code,
        "description": delivery_method.description
    } for delivery_method in DeliveryMethod.objects.all()]

    data = {
        "course_data": sorted_course_offerings,  # course_offering_data,
        "semester_fractions": semester_fractions,
        "semester_fractions_reverse": semester_fractions_reverse,
        "available_rooms": available_rooms,
        "available_delivery_methods": available_delivery_methods,
    }
    return JsonResponse(data)

def create_delivery_method_dict(delivery_method_object):

    if delivery_method_object == None:
        return {"id": None, "code": "", "description": ""}
    else:
        return {"id": delivery_method_object.id, "code": delivery_method_object.code, "description": delivery_method_object.description}

def sort_rooms(presorted_meeting_times, sorted_meeting_times, presorted_rooms):
    """
    Sorts a room list in the same way that the meeting times have been sorted.
    """
    sorted_rooms = ['' for room in presorted_rooms]
    used_indices = []
    num_successes = 0
    for ii in range(len(presorted_meeting_times)):
        for jj in range(len(sorted_meeting_times)):
            if (presorted_meeting_times[ii] == sorted_meeting_times[jj]) and (jj not in used_indices):
                used_indices.append(jj)
                num_successes += 1
                sorted_rooms[jj] = presorted_rooms[ii]
                break
    if num_successes != len(presorted_meeting_times):
        print("There seems to have been an error in sorting the rooms!")
    return sorted_rooms

def construct_instructor_list(course_offering, include_loads = False):
    """
    Constructs a list of instructors for a given (banner or iChair) course offering.
    include_loads can only be set to True for iChair course offerings.
    """
    if not include_loads:
        return [instr.instructor.first_name+' ' +
                instr.instructor.last_name + ' (primary)' if (instr.is_primary and len(course_offering.offering_instructors.all())>1) else instr.instructor.first_name+' ' +
                instr.instructor.last_name for instr in course_offering.offering_instructors.all()]
    else:
        return ["{0} {1} [{2}/{3}] (primary)".format(instr.instructor.first_name, instr.instructor.last_name, 
                str(load_hour_rounder(instr.load_credit)), str(load_hour_rounder(course_offering.load_available))) 
            if (instr.is_primary and len(course_offering.offering_instructors.all())>1) 
            else "{0} {1} [{2}/{3}]".format(instr.instructor.first_name, instr.instructor.last_name, 
                str(load_hour_rounder(instr.load_credit)), str(load_hour_rounder(course_offering.load_available))) 
                for instr in course_offering.offering_instructors.all()]

def construct_instructor_detail_list(bco):
    """Constructs a list of instructors for a given banner course offering."""
    return [{
        "pidm": instr.instructor.pidm,
        "is_primary": instr.is_primary,
        "name": instr.instructor.first_name + ' ' + instr.instructor.last_name}  for instr in bco.offering_instructors.all()]

def construct_ichair_instructor_detail_list(ico):
    """Constructs a list of instructors for a given iChair course offering."""
    return [{
        "id": instr.instructor.id,
        "pidm": instr.instructor.pidm,
        "is_primary": instr.is_primary,
        "load_credit": instr.load_credit,
        "name": instr.instructor.first_name + ' ' + instr.instructor.last_name}  for instr in ico.offering_instructors.all()]

def delta_update_status(bco, ico, delta, check_rooms = False):
    """Uses a delta object to compare the current status of a banner course offering compared to its corresponding iChair course offering."""
    # at this point it is assumed that the delta object is of the "request that the registrar do an update" variety

    delta_response = {
        "id": delta.id,
        "requested_action": DeltaCourseOffering.actions_reverse_lookup(delta.requested_action),
        # True if this update is being requested by the user
        "request_update_meeting_times": delta.update_meeting_times,
        # True if this update is being requested by the user
        "request_update_instructors": delta.update_instructors,
        # True if this update is being requested by the user
        "request_update_semester_fraction": delta.update_semester_fraction,
        # True if this update is being requested by the user
        "request_update_max_enrollment": delta.update_max_enrollment,
        # True if this update is being requested by the user
        "request_update_public_comments": delta.update_public_comments,
        # True if this update is being requested by the user
        "request_update_delivery_method": delta.update_delivery_method,
        "meeting_times": None,
        "instructors": None,
        "semester_fraction": None,
        "max_enrollment": None,
        "delivery_method": None,
        "public_comments": None,
        "public_comments_summary": None,
        "registrar_comment": delta.extra_comment,
        "registrar_comment_exists": delta.extra_comment is not None, # if registrar_comment is None in python, it seems to translate to null in javascript, but not sure that's completely reliable; this seems safer
        "messages_exist": False,
    }

    # we only check if the meetings agree if the user has requested that a message be generated for this property
    if delta.update_meeting_times and (not scheduled_classes_match(bco, ico, check_rooms)):
        # this is not a great way to do this, but it avoid rewriting the class_time_and_room_summary() method....
        was_list = []
        change_to_list = []
        if not check_rooms:
            was_list = class_time_and_room_summary(bco.scheduled_classes.all(), include_rooms = check_rooms, new_format = True)
            change_to_list = class_time_and_room_summary(ico.scheduled_classes.all(), include_rooms = check_rooms, new_format = True)
        else:
            bco_meeting_times, bco_rooms = class_time_and_room_summary(bco.scheduled_classes.all(), include_rooms = check_rooms, new_format = True)
            ico_meeting_times, ico_rooms = class_time_and_room_summary(ico.scheduled_classes.all(), include_rooms = check_rooms, new_format = True)
            for ii in range(0, len(bco_meeting_times)):
                was_list.append(bco_meeting_times[ii] + ' / ' + bco_rooms[ii])
            for ii in range(0, len(ico_meeting_times)):
                change_to_list.append(ico_meeting_times[ii] + ' / ' + ico_rooms[ii])
        delta_response["meeting_times"] = {
            "was": was_list,
            "change_to": change_to_list
        }

    if delta.update_instructors and (not instructors_match(bco, ico)):
        delta_response["instructors"] = {
            "was": construct_instructor_list(bco),
            "change_to": construct_instructor_list(ico)
        }

    if delta.update_semester_fraction and (not semester_fractions_match(bco, ico)):
        delta_response["semester_fraction"] = {
            "was": bco.semester_fraction,
            "change_to": ico.semester_fraction
        }

    if delta.update_max_enrollment and (not max_enrollments_match(bco, ico)):
        delta_response["max_enrollment"] = {
            "was": bco.max_enrollment,
            "change_to": ico.max_enrollment
        }

    if delta.update_delivery_method and (not delivery_methods_match(bco, ico)):
        delta_response["delivery_method"] = {
            "was": bco.delivery_method.description if bco.delivery_method is not None else None,
            "change_to": ico.delivery_method.description if ico.delivery_method is not None else None
        }

    if delta.update_public_comments and (not public_comments_match(bco, ico)):
        delta_response["public_comments"] = {
            "was": [comment["text"] for comment in bco.comment_list()["comment_list"]],
            "change_to": [comment["text"] for comment in ico.comment_list()["comment_list"]]
        }
        delta_response["public_comments_summary"] = {
            "was": bco.comment_list()["summary"],
            "change_to": ico.comment_list()["summary"]
        }

    if (delta_response["registrar_comment"] is not None) or (delta_response["meeting_times"] is not None) or (delta_response["instructors"] is not None) or (delta_response["semester_fraction"] is not None) or (delta_response["max_enrollment"] is not None) or (delta_response["public_comments"] is not None) or (delta_response["delivery_method"] is not None):
        delta_response["messages_exist"] = True

    # print(delta_response)

    return delta_response


def delta_create_status(ico, delta, check_rooms = False):
    """
    Uses a delta "create" type of object to generate a delta response for an iChair course offering.
    No banner course offering object exists in this case, since this is something that we are requesting
    that the registrar create.
    """
    # at this point it is assumed that the delta object is of the "request that the registrar create a course offering" variety

    delta_response = {
        "id": delta.id,
        "requested_action": DeltaCourseOffering.actions_reverse_lookup(delta.requested_action),
        # True if the user is requesting that the registrar create this property for a given course offering
        "request_update_meeting_times": delta.update_meeting_times,
        # True if the user is requesting that the registrar create this property for a given course offering
        "request_update_instructors": delta.update_instructors,
        # True if the user is requesting that the registrar create this property for a given course offering
        "request_update_semester_fraction": delta.update_semester_fraction,
        # True if the user is requesting that the registrar create this property for a given course offering
        "request_update_max_enrollment": delta.update_max_enrollment,
        # True if the user is requesting that the registrar create this property for a given course offering
        "request_update_public_comments": delta.update_public_comments,
        # True if the user is requesting that the registrar create this property for a given course offering
        "request_update_delivery_method": delta.update_delivery_method,
        "meeting_times": None,
        "instructors": None,
        "semester_fraction": None,
        "max_enrollment": None,
        "delivery_method": None,
        "public_comments": None,
        "public_comments_summary": None,
        "registrar_comment": delta.extra_comment,
        "registrar_comment_exists": delta.extra_comment is not None, # if registrar_comment is None in python, it seems to translate to null in javascript, but not sure that's completely reliable; this seems safer
        "messages_exist": False
    }

    # we only check if there are meetings if the user has requested that a message be generated for this property
    if delta.update_meeting_times:

        # this is not a great way to do this, but it avoid rewriting the class_time_and_room_summary() method....
        change_to_list = []
        if not check_rooms:
            change_to_list = class_time_and_room_summary(ico.scheduled_classes.all(), include_rooms = check_rooms, new_format = True)
        else:
            ico_meeting_times, ico_rooms = class_time_and_room_summary(ico.scheduled_classes.all(), include_rooms = check_rooms, new_format = True)
            for ii in range(0, len(ico_meeting_times)):
                change_to_list.append(ico_meeting_times[ii] + ' / ' + ico_rooms[ii])
        delta_response["meeting_times"] = {
            "was": [],
            "change_to": change_to_list
        }

    if delta.update_instructors:
        delta_response["instructors"] = {
            "was": [],
            "change_to": construct_instructor_list(ico)
        }

    if delta.update_semester_fraction:
        delta_response["semester_fraction"] = {
            "was": None,
            "change_to": ico.semester_fraction
        }

    if delta.update_max_enrollment:
        delta_response["max_enrollment"] = {
            "was": None,
            "change_to": ico.max_enrollment
        }
    
    if delta.update_delivery_method:
        delta_response["delivery_method"] = {
            "was": None,
            "change_to": ico.delivery_method.description if ico.delivery_method is not None else None
        }

    if delta.update_public_comments:
        delta_response["public_comments"] = {
            "was": [],
            "change_to": [comment["text"] for comment in ico.comment_list()["comment_list"]]
        }
        delta_response["public_comments_summary"] = {
            "was": [],
            "change_to": ico.comment_list()["summary"]
        }

    if (delta_response["registrar_comment"]  is not None) or (delta_response["meeting_times"] is not None) or (delta_response["instructors"] is not None) or (delta_response["semester_fraction"] is not None) or (delta_response["max_enrollment"] is not None) or (delta_response["public_comments"] is not None) or (delta_response["delivery_method"] is not None):
        delta_response["messages_exist"] = True

    # print(delta_response)

    return delta_response


def delta_delete_status(delta):
    """
    Uses a delta "delete" type of object to generate a delta response for a banner course offering.
    No iChair course offering object exists in this case.  Also, we are actually generating a somewhat
    generic response in a "delta response" format.  We don't both to fetch any banner course offering
    data, since we don't really need it (all we need is the CRN, and we already have that).
    """
    # at this point it is assumed that the delta object is of the "request that the registrar delete a course offering" variety

    delta_response = {
        "id": delta.id,
        "requested_action": DeltaCourseOffering.actions_reverse_lookup(delta.requested_action),
        # Should be false, since the registrar is simply going to delete the course offering
        "request_update_meeting_times": delta.update_meeting_times,
        # Should be false, since the registrar is simply going to delete the course offering
        "request_update_instructors": delta.update_instructors,
        # Should be false, since the registrar is simply going to delete the course offering
        "request_update_semester_fraction": delta.update_semester_fraction,
        # Should be false, since the registrar is simply going to delete the course offering
        "request_update_max_enrollment": delta.update_max_enrollment,
        # Should be false, since the registrar is simply going to delete the course offering
        "request_update_public_comments": delta.update_public_comments,
        # we could fetch them, but there's not really much point....
        "request_update_delivery_method": delta.update_delivery_method,
        # Should be false, since the registrar is simply going to delete the course offering
        "meeting_times": None,
        "instructors": None,
        "semester_fraction": None,
        "max_enrollment": None,
        "delivery_method": None,
        "public_comments": None,
        "public_comments_summary": None,
        "registrar_comment": delta.extra_comment,
        "registrar_comment_exists": delta.extra_comment is not None, # if registrar_comment is None in python, it seems to translate to null in javascript, but not sure that's completely reliable; this seems safer
        "messages_exist": True  # the message is simply going to be "delete this course offering"
    }

    return delta_response


@login_required
@csrf_exempt
def generate_pdf(request):

    user = request.user
    user_preferences = user.user_preferences.all()[0]
    year = user_preferences.academic_year_to_view
    department = user_preferences.department_to_view

    year_text = '{0}-{1}'.format(year.begin_on.year, year.end_on.year)

    json_data = json.loads(request.body)
    course_data = json_data['courseData']

    #for cd in course_data:
    #    print(cd)

    """
    deltas format:
    term_code: item.term_code,
    term_name: item.term,
    banner: item.banner,
    delta: item.course_title
    """
    department_name = department.name

    # https://www.programiz.com/python-programming/datetime/strftime
    # file_name_time_string = datetime.datetime.now().strftime("%m-%d-%Y-%H%M%S")
    # https://stackoverflow.com/questions/1007481/how-do-i-replace-whitespaces-with-underscore-and-vice-versa
    # file_name = "ScheduleEdits-"+department_name.replace(" ", "-")+"-"+file_name_time_string+".pdf"

    # https://www.geeksforgeeks.org/generating-random-ids-using-uuid-python/
    uuid_int = uuid.uuid1().int
    #pdf.write(open("ScheduleEdits_"+department_name.replace(" ", "_")+"_"+file_name_time_string+".pdf","wb")) 

    #response = HttpResponse(content_type='application/pdf')
    #response['Content-Disposition'] = 'attachment; filename="searchable_file_name.pdf"'


    pdf = PdfFileWriter()

    # https://github.com/mstamy2/PyPDF2/blob/master/Sample_Code/basic_features.py
    # Using ReportLab Canvas to insert image into PDF
    buffer = BytesIO()
    
    #imgDoc = canvas.Canvas(imgTemp, pagesize=letter)
    imgDoc = canvas.Canvas(buffer, pagesize=letter)
    # 612 × 792, apparently...?
    
    # Draw image on Canvas and save PDF in buffer
    pdfmetrics.registerFont(TTFont('VeraIt', 'VeraIt.ttf'))
    
    
    pdfmetrics.registerFont(TTFont('Vera', 'Vera.ttf'))
    pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))
    pdfmetrics.registerFont(TTFont('VeraIt', 'VeraIt.ttf'))
    #pdfmetrics.registerFont(TTFont('VeraBI', 'VeraBI.ttf'))
    

    left_margin = 72
    top_margin = 72
    bottom_margin = 72
    top_page = 792 - top_margin
    title_height = 700
    horizontal_center_page = 612/2

    tab = 44
    number_width = 20
    tab0 = left_margin + number_width
    tab1 = left_margin + number_width + tab
    tab2 = left_margin + number_width + 2*tab
    tab3 = left_margin + number_width + 3.3*tab

    dy = 14
    registrar_comments_num_chars = 85

    layout = {
        "left_margin": left_margin,
        "top_margin": top_margin,
        "bottom_margin": bottom_margin,
        "top_page": top_page,
        "title_height": title_height,
        "horizontal_center_page": horizontal_center_page,
        "tabs": {
                "tab0": tab0,
                "tab1": tab1,
                "tab2": tab2,
                "tab3": tab3
            },
        "dy": dy,
        "registrar_comments_num_chars": registrar_comments_num_chars
    }

    
    
    imgDoc.setFont('Vera', 13)
    imgDoc.drawString(layout["left_margin"], layout["title_height"], "Schedule Edits - "+department_name  + " (" + year_text+")")
    imgDoc.setFont('Vera', 9)
    
    page_number = 0
    y = layout["title_height"] - layout["dy"]

    # https://stackoverflow.com/questions/3316882/how-do-i-get-a-string-format-of-the-current-date-time-in-python
    time_string = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
    imgDoc.drawString(layout["left_margin"], y, "Time: " + time_string)

    edit_number = 0
    for item in course_data:
        edit_number += 1
        crn = item["crn"] # will be None for 'create' requests
        campus = item["campus"] # will be None for 'create' requests; the campus propery is not currently being displayed in the pdf, but could be added if that's helpful
        term_code = item["term_code"]
        if require_page_break(y, layout, item):
            imgDoc.drawString(layout["horizontal_center_page"], layout["bottom_margin"]-2*layout["dy"], str(page_number+1))
            imgDoc.showPage()
            page_number += 1
            y = layout["top_page"]

        if item["delta"]["registrar_comment_exists"]:
            registrar_comment_string_array = split_long_string(item["delta"]["registrar_comment"], layout["registrar_comments_num_chars"])
            #print('registrar comments:')
            #print(registrar_comment_string_array)

        if item["delta"]["requested_action"] == 'update':
            #print('we have an update!')
            #print(' ')
            #print(item['delta'])
            course = item["banner"]["course"]
            course_title = item["banner"]["course_title"]
            credit_hours = item["banner"]["credit_hours"]
            if credit_hours == 1:
                hr_versus_hrs = 'hour'
            else:
                hr_versus_hrs = 'hours'
            y -= 2*layout["dy"]
            imgDoc.setFont('Vera', 9)
            imgDoc.drawString(layout["left_margin"], y, str(edit_number)+'.')
            if not item["courseOwnedByUser"]:
                imgDoc.setFont('VeraBd', 9)
                imgDoc.drawString(layout["tabs"]["tab0"], y, "Note: The department requesting this action does not own this course.")
                imgDoc.setFont('Vera', 9)
                y -= layout["dy"]
            imgDoc.setFont('VeraBd', 9)
            imgDoc.drawString(layout["tabs"]["tab0"], y, "Update:")
            imgDoc.setFont('Vera', 9)
            # https://pythonprinciples.com/blog/converting-integer-to-string-in-python/
            imgDoc.drawString(layout["tabs"]["tab1"], y, "CRN "+crn + " - "+course+",  "+course_title + " ("+str(credit_hours)+" credit "+hr_versus_hrs+")")
            y -= layout["dy"]
            imgDoc.drawString(layout["tabs"]["tab1"], y, "Term: "+term_code)

            if item["delta"]["instructors"] is not None:
                y, imgDoc = render_updates(imgDoc, y, layout, "Instructor(s): ", item["delta"]["instructors"], data_in_list = True)
            if item["delta"]["meeting_times"] is not None:
                if item["includeRoomComparisons"]:
                    y, imgDoc = render_updates(imgDoc, y, layout, "Meeting Times / Rooms: ", item["delta"]["meeting_times"], data_in_list = True)
                else:
                    y, imgDoc = render_updates(imgDoc, y, layout, "Meeting Times: ", item["delta"]["meeting_times"], data_in_list = True)
            if item["delta"]["max_enrollment"] is not None:
                y, imgDoc = render_updates(imgDoc, y, layout, "Enrollment Cap: ", item["delta"]["max_enrollment"], data_in_list = False)
            if item["delta"]["delivery_method"] is not None:
                y, imgDoc = render_updates(imgDoc, y, layout, "Delivery Method: ", item["delta"]["delivery_method"], data_in_list = False)
            if item["delta"]["semester_fraction"] is not None:
                y, imgDoc = render_updates(imgDoc, y, layout, "Semester Fraction: ", item["delta"]["semester_fraction"], data_in_list = False, data_is_sem_fraction = True)
            if item["delta"]["public_comments"] is not None:
                y, imgDoc = render_updates(imgDoc, y, layout, "Website Comments: ", item["delta"]["public_comments"], data_in_list = True)
            if item["delta"]["registrar_comment_exists"]:
                y, imgDoc = render_registrar_comment(imgDoc, y, layout, registrar_comment_string_array)

        if item["delta"]["requested_action"] == 'delete':
            #print('we have a delete!')
            #print(' ')
            #print(item['delta'])
            course = item["banner"]["course"]
            course_title = item["banner"]["course_title"]
            credit_hours = item["banner"]["credit_hours"]
            if credit_hours == 1:
                hr_versus_hrs = 'hour'
            else:
                hr_versus_hrs = 'hours'
            y -= 2*layout["dy"]
            imgDoc.setFont('Vera', 9)
            imgDoc.drawString(layout["left_margin"], y, str(edit_number)+'.')
            if not item["courseOwnedByUser"]:
                imgDoc.setFont('VeraBd', 9)
                imgDoc.drawString(layout["tabs"]["tab0"], y, "Note: The department requesting this action does not own this course.")
                imgDoc.setFont('Vera', 9)
                y -= layout["dy"]
            imgDoc.setFont('VeraBd', 9)
            imgDoc.drawString(layout["tabs"]["tab0"], y, "Delete:")
            imgDoc.setFont('Vera', 9)
            imgDoc.drawString(layout["tabs"]["tab1"], y, "CRN "+crn + " - "+course+",  "+course_title + " ("+str(credit_hours)+" credit "+hr_versus_hrs+")")
            y -= layout["dy"]
            imgDoc.drawString(layout["tabs"]["tab1"], y, "Term: "+term_code)
            if item["delta"]["registrar_comment_exists"]:
                y, imgDoc = render_registrar_comment(imgDoc, y, layout, registrar_comment_string_array)

        if item["delta"]["requested_action"] == 'create':
            #print('we have a create')
            #print(' ')
            #print(item['delta'])
            course = item["ichair"]["course"]
            course_title = item["ichair"]["course_title"]
            credit_hours = item["ichair"]["credit_hours"]
            if credit_hours == 1:
                hr_versus_hrs = 'hour'
            else:
                hr_versus_hrs = 'hours'
            y -= 2*layout["dy"]
            imgDoc.setFont('Vera', 9)
            imgDoc.drawString(layout["left_margin"], y, str(edit_number)+'.')
            if not item["courseOwnedByUser"]:
                imgDoc.setFont('VeraBd', 9)
                imgDoc.drawString(layout["tabs"]["tab0"], y, "Note: The department requesting this action does not own this course.")
                imgDoc.setFont('Vera', 9)
                y -= layout["dy"]
            imgDoc.setFont('VeraBd', 9)
            imgDoc.drawString(layout["tabs"]["tab0"], y, "Create:")
            imgDoc.setFont('Vera', 9)
            imgDoc.drawString(layout["tabs"]["tab1"], y, "New Section - "+course+",  "+course_title + " ("+str(credit_hours)+" credit "+hr_versus_hrs+")")
            y -= layout["dy"]
            imgDoc.drawString(layout["tabs"]["tab1"], y, "Term: "+term_code)
       
            if item["delta"]["instructors"] is not None:
                y, imgDoc = render_creates(imgDoc, y, layout, "Instructor(s): ", item["delta"]["instructors"], data_in_list = True)
            if item["delta"]["meeting_times"] is not None:
                print(item["delta"]["meeting_times"])
                y, imgDoc = render_creates(imgDoc, y, layout, "Meeting Times: ", item["delta"]["meeting_times"], data_in_list = True)
            if item["delta"]["max_enrollment"] is not None:
                y, imgDoc = render_creates(imgDoc, y, layout, "Enrollment Cap: ", item["delta"]["max_enrollment"], data_in_list = False)
            if item["delta"]["delivery_method"] is not None:
                y, imgDoc = render_creates(imgDoc, y, layout, "Delivery Method: ", item["delta"]["delivery_method"], data_in_list = False)
            if item["delta"]["semester_fraction"] is not None:
                y, imgDoc = render_creates(imgDoc, y, layout, "Semester Fraction: ", item["delta"]["semester_fraction"], data_in_list = False, data_is_sem_fraction = True)
            if item["delta"]["public_comments"] is not None:
                y, imgDoc = render_creates(imgDoc, y, layout, "Website Comments: ", item["delta"]["public_comments"], data_in_list = True)
            if item["delta"]["registrar_comment_exists"]:
                y, imgDoc = render_registrar_comment(imgDoc, y, layout, registrar_comment_string_array)

    imgDoc.drawString(layout["horizontal_center_page"], layout["bottom_margin"]-2*layout["dy"], str(page_number+1))
    imgDoc.showPage()

    # imgDoc.drawString(197,780,"Sudoku Project")
    # imgDoc.setFont('VeraIt', 8)
    # imgDoc.drawString(430,20,"By PantelisPanka, nikfot, TolisChal")
    # imgDoc.setFont('Vera', 8)
    # imgDoc.drawString(550,780,str(1))

    imgDoc.save()

    for i in range(page_number+1):    
        pdf.addPage(PdfFileReader(BytesIO(buffer.getvalue())).getPage(i))

    #pdf2 = buffer.getvalue()
    buffer.close()
    #response.write(pdf2)
    
    # the following writes the pdf to the server's harddrive....
    #pdf.write(open("ScheduleEdits-"+department_name.replace(" ", "-")+"-"+file_name_time_string+".pdf","wb")) 

    #https://stackoverflow.com/questions/961632/converting-integer-to-string
    uuid_string = '{}'.format(uuid_int) # str(...) seems to turn the long string into a string of a real....
    #print('uuid string: ', uuid_string)
    pdf.write(open("pdf/"+uuid_string+".pdf","wb"))

    data = {
        'UUID': uuid_string
    }
    return JsonResponse(data)


def require_page_break(y, layout, item):

    dy = layout["dy"]
    num_chars = layout["registrar_comments_num_chars"]

    delta_y = 3*dy # magnitude of the vertical space required, in px; first increment is for the extra vertical space, title and term code ....
    if not item["courseOwnedByUser"]:
        delta_y += dy # an extra row because of the warning that gets added in this case
    if item["delta"]["requested_action"] == 'update':
        if item["delta"]["instructors"] is not None:
            # https://www.programiz.com/python-programming/methods/built-in/min
            delta_y += dy + dy*max(len(item["delta"]["instructors"]["was"]), 1) + dy*max(len(item["delta"]["instructors"]["change_to"]), 1)
        if item["delta"]["meeting_times"] is not None:
            delta_y += dy + dy*max(len(item["delta"]["meeting_times"]["was"]), 1) + dy*max(len(item["delta"]["meeting_times"]["change_to"]), 1)
        if item["delta"]["public_comments"] is not None:
            delta_y += dy + dy*max(len(item["delta"]["public_comments"]["was"]), 1) + dy*max(len(item["delta"]["public_comments"]["change_to"]), 1)
        if item["delta"]["max_enrollment"] is not None:
            delta_y += 3*dy 
        if item["delta"]["delivery_method"] is not None:
            delta_y += 3*dy 
        if item["delta"]["semester_fraction"] is not None:
            delta_y += 3*dy
    if item["delta"]["requested_action"] == 'create':
        if item["delta"]["instructors"] is not None:
            delta_y += dy*max(len(item["delta"]["instructors"]["change_to"]), 1)
        if item["delta"]["meeting_times"] is not None:
            delta_y += dy*max(len(item["delta"]["meeting_times"]["change_to"]), 1)
        if item["delta"]["public_comments"] is not None:
            delta_y += dy*max(len(item["delta"]["public_comments"]["change_to"]), 1)
        if item["delta"]["max_enrollment"] is not None:
            delta_y += dy 
        if item["delta"]["delivery_method"] is not None:
            delta_y += dy
        if item["delta"]["semester_fraction"] is not None:
            delta_y += dy
    # nothing to do if 'delete', since the delta_y only corresponds to one line (except if there are registrar comments....)
    if item["delta"]["registrar_comment_exists"]:
        registrar_comment_string_array = split_long_string(item["delta"]["registrar_comment"], num_chars)
        delta_y += dy + dy*len(registrar_comment_string_array)

    #print("delta_y", item["crn"], "  ", delta_y/dy)
    return y - delta_y < layout["bottom_margin"]

def render_registrar_comment(imgDoc, y, layout, registrar_comment_string_array):
    #print(registrar_comment_string_array)
    
    dy = layout["dy"]
    tabs = layout["tabs"]
    y -= dy
    imgDoc.setFont('VeraBd', 9)
    imgDoc.drawString(tabs["tab0"], y, 'Note for Registrar:')
    imgDoc.setFont('Vera', 9)
    for comment_line in registrar_comment_string_array:
        y -= dy
        imgDoc.drawString(tabs["tab0"], y, comment_line)

    return y, imgDoc

def render_updates(imgDoc, y, layout, item_title, item_dict, data_in_list, data_is_sem_fraction = False, data_is_registrar_comments = False):
    #print(item_dict)

    # https://stackoverflow.com/questions/3593193/add-page-break-to-reportlab-canvas-object

    dy = layout["dy"]
    tabs = layout["tabs"]

    y -= dy
    imgDoc.drawString(tabs["tab1"], y, item_title)
    y -= dy
    if data_in_list:
        imgDoc.drawString(tabs["tab2"], y, "Was:")
        counter = 0
        for former_item in item_dict["was"]:
            if counter > 0:
                y -= dy
            imgDoc.drawString(tabs["tab3"], y, former_item)
            counter+=1
        y -= dy
        imgDoc.drawString(tabs["tab2"], y, "Change to:")
        counter = 0
        for future_item in item_dict["change_to"]:
            #print('change to: ', future_item)
            if counter > 0:
                y -= dy
            imgDoc.drawString(tabs["tab3"], y, future_item)
            counter+=1
    else:
        if data_is_sem_fraction:
            imgDoc.drawString(tabs["tab2"], y, "Was:")
            imgDoc.drawString(tabs["tab3"], y, CourseOffering.semester_fraction_long_name(item_dict["was"]))
            y -= dy
            imgDoc.drawString(tabs["tab2"], y, "Change to:")
            imgDoc.drawString(tabs["tab3"], y, CourseOffering.semester_fraction_long_name(item_dict["change_to"]))
        else:
            imgDoc.drawString(tabs["tab2"], y, "Was:")
            imgDoc.drawString(tabs["tab3"], y, str(item_dict["was"]))
            y -= dy
            imgDoc.drawString(tabs["tab2"], y, "Change to:")
            imgDoc.drawString(tabs["tab3"], y, str(item_dict["change_to"]))

    return y, imgDoc

def render_creates(imgDoc, y, layout, item_title, item_dict, data_in_list, data_is_sem_fraction = False):
    #print(item_dict)

    # https://stackoverflow.com/questions/3593193/add-page-break-to-reportlab-canvas-object

    dy = layout["dy"]
    tabs = layout["tabs"]

    y -= dy
    imgDoc.drawString(tabs["tab1"], y, item_title)
    #y -= dy
    if data_in_list:
        counter = 0
        for future_item in item_dict["change_to"]:
            if counter > 0:
                y -= dy
            imgDoc.drawString(tabs["tab3"], y, future_item)
            counter+=1
    else:
        if data_is_sem_fraction:
            imgDoc.drawString(tabs["tab3"], y, CourseOffering.semester_fraction_long_name(item_dict["change_to"]))
        else:
            imgDoc.drawString(tabs["tab3"], y, str(item_dict["change_to"]))

    return y, imgDoc

def split_long_string(original_string, num_chars):
    """Split a long string into a list of substrings, with each substring having a length of at most num_chars."""
    # https://stackoverflow.com/questions/743806/how-to-split-a-string-into-a-list
    words = original_string.split()
    string_list = []
    line_len = 0
    current_string = ''
    for word in words:
        line_len = len(current_string)
        if line_len + 1 + len(word) <= num_chars:
            if current_string == '':
                current_string = word
            else:
                current_string += ' '+word
        else:
            string_list.append(current_string)
            current_string = word
    if current_string != '':
        string_list.append(current_string)
    return string_list

def find_unlinked_ichair_course_offerings(bco, semester, subject):
    """Find the unlinked iChair course offerings that could correspond to a particular (unlinked) banner course offering."""
    if bco.is_linked:
        return []
    else:
        # we don't include the title or banner title in the filter, since we will eventually let the user decide
        # whether or not to link one of these courses to the banner course
        return CourseOffering.objects.filter(
            Q(semester=semester) &
            Q(course__subject=subject) &
            Q(course__number__startswith=bco.course.number) &
            Q(course__credit_hours=bco.course.credit_hours) &
            Q(crn__isnull=True))


def find_unlinked_banner_course_offerings(ico, term_code, subject):
    """Find the unlinked banner course offerings that could correspond to a particular (unlinked) iChair course offering."""
    if ico.crn is not None:
        print('something is wrong...this ico should not have a CRN, but it does...!')
        return []
    else:
        # we don't include the title or banner title in the filter, since we will eventually let the user decide
        # whether or not to link one of these courses to the iChair course
        candidate_banner_course_offerings = BannerCourseOffering.objects.filter(
            Q(term_code=term_code) &
            Q(course__subject__abbrev=subject.abbrev) &
            Q(course__credit_hours=ico.course.credit_hours) &
            Q(ichair_id__isnull=True))
        # print('finding unlinked banner course offerings for: ', ico)
        # print('found some possibilities: ', len(
        #    candidate_banner_course_offerings))
        # now find the course number matches, truncating the iChair ones to the same # of digits (in the comparison) as the banner ones
        # https://www.pythonforbeginners.com/basics/list-comprehensions-in-python
        # https://www.pythoncentral.io/cutting-and-slicing-strings-in-python/
        banner_options = [bco for bco in candidate_banner_course_offerings if bco.course.number ==
                          ico.course.number[:len(bco.course.number)]]
        #print(banner_options)
    return banner_options


def find_ichair_course_offering(bco, semester, subject):
    """Start the process of linking up this banner course offering (bco) with one in iChair."""

    # start by unlinking the banner course offering
    bco.ichair_id = None
    bco.save()

    # search for candidate course offerings
    # https://stackoverflow.com/questions/844556/filtering-for-empty-or-null-names-in-a-queryset
    candidate_ichair_matches = CourseOffering.objects.filter(
        Q(semester=semester) &
        Q(course__subject=subject) &
        Q(course__number__startswith=bco.course.number) &
        Q(course__credit_hours=bco.course.credit_hours) &
        Q(crn__isnull=True))
    # https://stackoverflow.com/questions/15474933/list-comprehension-with-if-statement/15474969
    #print('      ')
    #print('len(candidate matches) = ', len(candidate_ichair_matches))
    candidate_ichair_matches = [course_offering for course_offering in candidate_ichair_matches if course_offering.course.title == bco.course.title or (bco.course.title in course_offering.course.banner_title_list)]
        # &
        #(Q(course__title=bco.course.title) | Q(course__banner_title=bco.course.title)))
    #print('      ')
    #print('len(candidate matches) = ', len(candidate_ichair_matches))

    if len(candidate_ichair_matches) == 1:
        ichair_course_offering = candidate_ichair_matches[0]
        # if only one potential match at this stage, link the banner course to the ichair one
        bco.ichair_id = ichair_course_offering.id
        bco.save()
        ichair_course_offering.crn = bco.crn
        ichair_course_offering.save()
        # print('>>> Exactly one candidate match...banner course offering is now linked to corresponding iChair course offering!')
        # print('>>> scheduled classes agree: ', scheduled_classes_match(bco, ichair_course_offering))
    elif len(candidate_ichair_matches) > 1:
        # print('<<< More than one candidate match...checking to see if meeting times match for any of them')
        choose_course_offering_second_cut(bco, candidate_ichair_matches)

    return None


def choose_course_offering_second_cut(bco, candidate_ichair_matches):
    """Check candidate iChair course matches for this banner course offering, and possibly choose one based on agreement of weekly schedules."""
    # at this point we have several candidate ichair matches...which one is closest?

    # first check to see if any of them has a "delta object" that links it to the banner course;
    # might need to check through several; if so, find the most recent and link up the corresponding
    # banner and iChair course offerings

    # delta course offering actions from the model itself:
    delta_course_offering_actions = DeltaCourseOffering.actions()

    # print('>>>>>>>>>>>>>>>inside second cut')

    recent_delta_object = None
    chosen_ichair_match = None
    for ichair_match in candidate_ichair_matches:
        delta_objects = DeltaCourseOffering.objects.filter(
            Q(crn=bco.crn) &
            Q(course_offering=ichair_match) &
            Q(requested_action=delta_course_offering_actions["update"]))
        if len(delta_objects) > 0:
            # print('delta object(s) found for', ichair_match)
            if recent_delta_object is None:
                recent_delta_object = delta_objects[0]
                chosen_ichair_match = ichair_match
            for delta_object in delta_objects:
                # print(delta_object, delta_object.updated_at)
                if delta_object.updated_at > recent_delta_object.updated_at:
                    recent_delta_object = delta_object
                    chosen_ichair_match = ichair_match
                    # print('found more recent!',
                    #      recent_delta_object.updated_at)
    if chosen_ichair_match is not None:
        # we found one, based on looking at the delta(s)
        # print(
        #    '<<<<>>>><<<<>>>>choosing an iChair course offering based on the delta object')
        bco.ichair_id = chosen_ichair_match.id
        bco.save()
        chosen_ichair_match.crn = bco.crn
        chosen_ichair_match.save()
        return None

    # print('inside choose_course_offering_second_cut!')
    # meet above criteria, as well as being a match on meeting days and times (but don't check rooms)
    second_cut_ichair_matches = []
    for ichair_match in candidate_ichair_matches:
        # print(ichair_match)
        # print('banner_title of iChair course:', ichair_match.course.banner_title)
        if scheduled_classes_match(bco, ichair_match):
            second_cut_ichair_matches.append(ichair_match)

    if len(second_cut_ichair_matches) == 1:
        ichair_course_offering = second_cut_ichair_matches[0]
        # if only one potential match at this stage, link the banner course to the ichair one
        bco.ichair_id = ichair_course_offering.id
        bco.save()
        ichair_course_offering.crn = bco.crn
        ichair_course_offering.save()
        # print('>>><<<>>> Exactly one candidate match...banner course offering is now linked to corresponding iChair course offering!')
    elif len(second_cut_ichair_matches) > 1:
        # at this point, see if the instructors are an exact match...
        choose_course_offering_third_cut(bco, second_cut_ichair_matches)

    return None


def choose_course_offering_third_cut(bco, second_cut_ichair_matches):
    """
    Check candidate iChair course matches for this banner course offering, and possibly choose one based on faculty members.
    By this point, the weekly schedules are an exact match, but there are too many course offerings that are an exact match in this respect.
    """
    # print('inside 3rd cut!  Checking instructors now....')

    # meet above criteria, as well as being a match on meeting days and times
    third_cut_ichair_matches = []
    for ichair_match in second_cut_ichair_matches:
        # print(ichair_match)
        if instructors_match(bco, ichair_match):
            # print('instructors match exactly!')
            third_cut_ichair_matches.append(ichair_match)

    if len(third_cut_ichair_matches) == 0:
        # see if semester fraction helps to sort things out....
        # print('instructors do not match exactly, going to check semester fractions instead!')
        choose_course_offering_fourth_cut(bco, second_cut_ichair_matches)

    if len(third_cut_ichair_matches) == 1:
        ichair_course_offering = third_cut_ichair_matches[0]
        # if only one potential match at this stage, link the banner course to the ichair one
        bco.ichair_id = ichair_course_offering.id
        bco.save()
        ichair_course_offering.crn = bco.crn
        ichair_course_offering.save()
        # print('>>><<<>>> Exactly one candidate match for instructors...banner course offering is now linked to corresponding iChair course offering!')

    else:
        # at this point, check semester_fractions(!)
        # print('~~~~~~~~~~~~')
        # print('<<<there are several instructors that match...checking semester fractions')
        # print('~~~~~~~~~~~~')
        choose_course_offering_fourth_cut(bco, third_cut_ichair_matches)

    return None


def choose_course_offering_fourth_cut(bco, third_cut_ichair_matches):
    """Check candidate iChair course matches for this banner course offering, and possibly choose one based on semester fraction."""
    # print('inside 4th cut!  Checking semester fractions now....')

    fourth_cut_ichair_matches = []
    for ichair_match in third_cut_ichair_matches:
        # print(ichair_match)
        if semester_fractions_match(bco, ichair_match):
            # print('semester fractions match exactly!')
            fourth_cut_ichair_matches.append(ichair_match)

    if len(fourth_cut_ichair_matches) == 1:
        ichair_course_offering = fourth_cut_ichair_matches[0]
        # if only one potential match at this stage, link the banner course to the ichair one
        bco.ichair_id = ichair_course_offering.id
        bco.save()
        ichair_course_offering.crn = bco.crn
        ichair_course_offering.save()
        # print('>>><<<>>> Exactly one candidate match for semester fractions...banner course offering is now linked to corresponding iChair course offering!')

    # at this point we give up...!

    return None


def construct_meeting_times_detail(course_offering, include_room = False):
    """Returns details of the meeting times for the course offering in question.  Accepts either an iChair course offering or a Banner course offering."""
    meeting_times_detail = []
    for sc in course_offering.scheduled_classes.all():
        new_meeting_times_element = {
                "day": sc.day,
                "begin_at": sc.begin_at,
                "end_at": sc.end_at,
                "id": sc.id,
                #"room": None,
                "rooms": []
            }
        #if include_room and sc.room != None:
        #    new_meeting_times_element["room"] = {
        #            "id": sc.room.id,
        #            "short_name": sc.room.short_name,
        #            "capacity": sc.room.capacity
        #        }
        if include_room:
            for room in sc.rooms.all():
                new_meeting_times_element["rooms"].append({
                    "id": room.id,
                    "short_name": room.short_name,
                    "capacity": room.capacity
                })
        meeting_times_detail.append(new_meeting_times_element)
    return meeting_times_detail


def scheduled_classes_match(banner_course_offering, ichair_course_offering, check_rooms = False):
    """
    Returns true if the scheduled class objects for an iChair course offering exactly match those for 
    the corresponding banner course offering.  If check_rooms is True, also checks to see if the rooms
    match; if not, returns False."""
    banner_scheduled_classes = banner_course_offering.scheduled_classes.all()
    ichair_scheduled_classes = ichair_course_offering.scheduled_classes.all()
    classes_match = True
    if len(banner_scheduled_classes) != len(ichair_scheduled_classes):
        classes_match = False
        return classes_match
    for bsc in banner_scheduled_classes:
        # if the # of scheduled classes agree and there is an isc match for each bsc, 
        # then the overall schedules agree (assuming the bsc's are all different...this 
        # could eventually be an issue we need to think about)
        one_fits = False
        for isc in ichair_scheduled_classes:
            if bsc.day == isc.day and bsc.begin_at == isc.begin_at and bsc.end_at == isc.end_at:
                if check_rooms:
                    bsc_room_ids = [room.building.abbrev + '-' + room.number for room in bsc.rooms.all()]
                    isc_room_ids = [room.building.abbrev + '-' + room.number for room in isc.rooms.all()]
                    one_fits = listsOfIntegersMatch(bsc_room_ids, isc_room_ids)
                else:
                    one_fits = True
        if not one_fits:
            classes_match = False
    return classes_match

# https://stackoverflow.com/questions/8866652/determine-if-2-lists-have-the-same-elements-regardless-of-order
def listsOfIntegersMatch(list1, list2):
    return collections.Counter(list1) == collections.Counter(list2)

def instructors_match(banner_course_offering, ichair_course_offering):
    """
    Returns true if the instructors for an iChair course offering exactly match those for the corresponding banner course offering. 
    Regarding the is_primary flag, instructors are considered to match...
        - if there are 0 or 1 instructor (in the latter case, the iChair instructor might not have the flag set); or
        - if the is_primary flags match exactly (when there are two or more instructors)
    """
    banner_instructors = banner_course_offering.offering_instructors.all()
    ichair_instructors = ichair_course_offering.offering_instructors.all()

    inst_match = True
    is_primary_flags_match = True
    if len(banner_instructors) != len(ichair_instructors):
        inst_match = False
        # print('instructors match: ', inst_match)
        return inst_match
    for banner_instructor in banner_instructors:
        # print('banner instructor: ', banner_instructor.instructor)
        # if the # of instructors agree and there is an iChair instructor match for each banner instructor, then the overall set of instructors agrees
        one_fits = False
        for ichair_instructor in ichair_instructors:
            if banner_instructor.instructor.pidm == ichair_instructor.instructor.pidm:
                # print('ichair instructor: ', ichair_instructor.instructor)
                one_fits = True
                if banner_instructor.is_primary != ichair_instructor.is_primary:
                    is_primary_flags_match = False
        if not one_fits:
            inst_match = False

    if inst_match and (len(ichair_instructors) >= 2):
        if not is_primary_flags_match:
            inst_match = False
            
    # print('instructors match: ', inst_match)
    return inst_match


def semester_fractions_match(banner_course_offering, ichair_course_offering):
    return banner_course_offering.semester_fraction == ichair_course_offering.semester_fraction


def max_enrollments_match(banner_course_offering, ichair_course_offering):
    return banner_course_offering.max_enrollment == ichair_course_offering.max_enrollment

def delivery_methods_match(banner_course_offering, ichair_course_offering):
    if (banner_course_offering.delivery_method == None) and (ichair_course_offering.delivery_method == None):
        return True
    elif (banner_course_offering.delivery_method == None) or (ichair_course_offering.delivery_method == None):
        return False
    else:
        return banner_course_offering.delivery_method.code == ichair_course_offering.delivery_method.code

def public_comments_match(banner_course_offering, ichair_course_offering):
    bco_comments = banner_course_offering.comment_list()
    ico_comments = ichair_course_offering.comment_list()

    #if len(ico_comments["comment_list"])>0:
    #    print('bco comments:', bco_comments)
    #    print('ico comments:', ico_comments)

    if len(bco_comments["comment_list"]) != len(ico_comments["comment_list"]):
        return False
    else:
        comments_agree = True
        for ii in range(len(bco_comments["comment_list"])):
            #print(ii)
            #print(bco_comments["comment_list"][ii]["text"])
            #print(ico_comments["comment_list"][ii]["text"])
            #print('agree: ', bco_comments["comment_list"][ii]["text"] != ico_comments["comment_list"][ii]["text"])

            if bco_comments["comment_list"][ii]["text"] != ico_comments["comment_list"][ii]["text"]:
                comments_agree = False
        return comments_agree

@login_required
@csrf_exempt
def delete_delta(request):
    """Deletes an existing delta object."""
    json_data = json.loads(request.body)
    delta_id = json_data['deltaId']

    delta_course_offering = DeltaCourseOffering.objects.get(pk=delta_id)

    # the following could be useful if we eventually allow the deletion of the "update" types of delta objects; at present we don't bother doing that via the api
    # if (delta_course_offering.crn is not None) and (delta_course_offering.crn != ''):
    #     banner_course_offerings = BannerCourseOffering.objects.filter(
    #         Q(term_code=delta_course_offering.semester.banner_code) &
    #         Q(crn=delta_course_offering.crn))
    #     print(banner_course_offerings)

    # we assume that the delta object has requested_action of the 'create' or 'delete' type, in which case deleting it means that
    # the instructors, etc., no longer match

    delta_course_offering.delete()

    agreement_update = {
        "instructors_match": False,
        "meeting_times_match": False,
        "max_enrollments_match": False,
        "semester_fractions_match": False,
        "public_comments_match": False,
        "delivery_methods_match": False,
    }

    data = {
        'agreement_update': agreement_update
    }

    return JsonResponse(data)


@login_required
@csrf_exempt
def generate_update_delta(request):
    """Generates a new delta object or modifies an existing one, depending on whether or not deltaId is None."""

    json_data = json.loads(request.body)
    delta_mods = json_data['deltaMods']

    action = json_data['action']

    semester_id = json_data['semesterId']
    crn = json_data['crn']
    ichair_course_offering_id = json_data['iChairCourseOfferingId']
    banner_course_offering_id = json_data['bannerCourseOfferingId']
    include_room_comparisons = json_data['includeRoomComparisons']
    
    # None if null in the UI code (i.e., if creating a new delta)
    delta_id = json_data['deltaId']

    #print(delta_mods)

    #print('action: ', action)
    #print('crn: ', crn)
    #print('ichair id: ', ichair_course_offering_id)
    #print('banner id: ', banner_course_offering_id)
    #print('semester_id: ', semester_id)
    #print('delta id: ', delta_id)

    delta_generation_successful = True
    number_ichair_primary_instructors_OK = True

    if delta_id is None:
        #print('creating a new delta!')
        if action == 'delete':
            # in this case, there is no iChair course offering, so we simply set ico to None (which is the appropriate value to send along when creating the object in the database)
            ico = None
            try:
                semester = Semester.objects.get(pk=semester_id)
            except:
                delta_generation_successful = False
                print("Problem finding the semester...!")
        else:
            # for the 'create' and 'update' cases there should be an iChair course offering, so fetch it
            try:
                semester = Semester.objects.get(pk=semester_id)
                ico = CourseOffering.objects.get(pk=ichair_course_offering_id)
            except:
                delta_generation_successful = False
                print("Problem finding the semester or iChair course offering...!")

        # delta course offering actions from the model itself:
        delta_course_offering_actions = DeltaCourseOffering.actions()

        if action == 'create':
            requested_action = delta_course_offering_actions["create"]
        elif action == 'update':
            requested_action = delta_course_offering_actions["update"]
        elif action == 'delete':
            requested_action = delta_course_offering_actions["delete"]
        else:
            delta_generation_successful = False

        #print(delta_course_offering_actions)

        if delta_generation_successful:
            # https://www.geeksforgeeks.org/python-check-whether-given-key-already-exists-in-a-dictionary/
            if 'meetingTimes' in delta_mods.keys():
                update_meeting_times = delta_mods['meetingTimes']
            else:
                update_meeting_times = False

            if 'instructors' in delta_mods.keys():
                if delta_mods['instructors'] and ((requested_action == delta_course_offering_actions["create"]) or (requested_action == delta_course_offering_actions["update"])):
                    # check first to see if the iChair version of the instructors have at most one primary instructor, etc.
                    # if not, don't allow the update and send back a message
                    if number_primary_instructors_OK(ico):
                        update_instructors = delta_mods['instructors']
                    else:
                        update_instructors = False
                        number_ichair_primary_instructors_OK = False
                else: #...for example, if requested_action == delta_course_offering_actions["delete"]
                    update_instructors = delta_mods['instructors']
            else:
                update_instructors = False

            if 'semesterFraction' in delta_mods.keys():
                update_semester_fraction = delta_mods['semesterFraction']
            else:
                update_semester_fraction = False

            if 'enrollmentCap' in delta_mods.keys():
                update_max_enrollment = delta_mods['enrollmentCap']
            else:
                update_max_enrollment = False

            if 'deliveryMethod' in delta_mods.keys():
                update_delivery_method = delta_mods['deliveryMethod']
            else:
                update_delivery_method = False

            if 'publicComments' in delta_mods.keys():
                update_public_comments = delta_mods['publicComments']
            else:
                update_public_comments = False

            dco = DeltaCourseOffering.objects.create(
                course_offering=ico,
                semester=semester,
                crn=crn,
                requested_action=requested_action,
                update_meeting_times=update_meeting_times,
                update_instructors=update_instructors,
                update_semester_fraction=update_semester_fraction,
                update_max_enrollment=update_max_enrollment,
                update_public_comments=update_public_comments,
                update_delivery_method=update_delivery_method)
            dco.save()

    else:
        dco = DeltaCourseOffering.objects.get(pk=delta_id)
        #print('got delta object!')
        #print(dco)
        if 'meetingTimes' in delta_mods.keys():
            dco.update_meeting_times = delta_mods['meetingTimes']

        if 'instructors' in delta_mods.keys():
            dco.update_instructors = delta_mods['instructors']

        if 'semesterFraction' in delta_mods.keys():
            dco.update_semester_fraction = delta_mods['semesterFraction']

        if 'enrollmentCap' in delta_mods.keys():
            dco.update_max_enrollment = delta_mods['enrollmentCap']

        if 'deliveryMethod' in delta_mods.keys():
            dco.update_delivery_method = delta_mods['deliveryMethod']

        if 'publicComments' in delta_mods.keys():
            dco.update_public_comments = delta_mods['publicComments']

        dco.save()

    delta_response = {}
    if delta_generation_successful:
        if action == 'update':
            # in this case we should have both a banner id and an ichair id....
            bco = BannerCourseOffering.objects.get(
                pk=banner_course_offering_id)
            ico = CourseOffering.objects.get(pk=ichair_course_offering_id)
            delta_response = delta_update_status(bco, ico, dco, check_rooms = include_room_comparisons)
            agreement_update = {
                "instructors_match": instructors_match(bco, ico),
                "meeting_times_match": scheduled_classes_match(bco, ico, check_rooms = include_room_comparisons),
                "max_enrollments_match": max_enrollments_match(bco, ico),
                "semester_fractions_match": semester_fractions_match(bco, ico),
                "public_comments_match": public_comments_match(bco, ico),
                "delivery_methods_match": delivery_methods_match(bco, ico),
            }
        elif action == 'create':
            # in this case we only have an ichair id....
            ico = CourseOffering.objects.get(pk=ichair_course_offering_id)
            delta_response = delta_create_status(ico, dco, check_rooms = include_room_comparisons)
            agreement_update = {
                "instructors_match": False,
                "meeting_times_match": False,
                "max_enrollments_match": False,
                "semester_fractions_match": False,
                "public_comments_match": False,
                "delivery_methods_match": False,
            }
        elif action == 'delete':
            # in this case we only have a banner id....
            delta_response = delta_delete_status(dco)
            # these quantities _will_ match after the course offering is deleted
            agreement_update = {
                "instructors_match": True,
                "meeting_times_match": True,
                "max_enrollments_match": True,
                "semester_fractions_match": True,
                "public_comments_match": True,
                "delivery_methods_match": True,
            }

        # WORKING HERE: need to add some other functionality for the delete' action....

    data = {
        'number_ichair_primary_instructors_OK': number_ichair_primary_instructors_OK,
        'delta_generation_successful': delta_generation_successful,
        'delta': delta_response,
        'agreement_update': agreement_update
    }

    return JsonResponse(data)

def number_primary_instructors_OK(ico):
    """
    This method checks to the iChair instructors for this course offering.  It returns the following:
    0 instructors: True (no primary instructors, but that's OK)
    1 instructor: True (doesn't matter whether or not the instructor is labelled as primary, since there is only one)
    >=2 instructors: True if exactly one of them is primary; otherwise False
    """

    offering_instructors = ico.offering_instructors.all()
    num_instructors = 0
    num_primary_instructors = 0
    for oi in offering_instructors:
        num_instructors += 1
        if oi.is_primary:
            num_primary_instructors += 1
    if num_instructors >= 2:
        return num_primary_instructors == 1
    else:
        return True

@login_required
@csrf_exempt
def create_update_delete_note_for_registrar_api(request):
    """
    Update a note for the registrar for a course offering.  Can do any combination of delete, create and update.
    Note:
        - 'update' means update a note on an existing delta object
        - 'create' means that no delta object exists, so a new one must be created (of 'update' type, with update_meeting_times, etc., set to false)
        - 'delete' means delete a note on an existing delta object (but leave the rest of the delta object as is)
    """
    json_data = json.loads(request.body)
    #print('data: ', json_data)
    ichair_id = json_data["iChairId"]
    banner_id = json_data["bannerId"]
    text = json_data["text"]
    action = json_data["action"]
    has_delta = json_data["hasDelta"]
    delta_id = json_data["deltaId"]
    has_ichair = json_data["hasIChair"]
    has_banner = json_data["hasBanner"]
    include_room_comparisons = json_data['includeRoomComparisons']
    
    updates_successful = True

    if has_ichair:
        ico = CourseOffering.objects.get(pk=ichair_id)
    if has_banner:
            bco = BannerCourseOffering.objects.get(pk=banner_id)
    
    delta_course_offering_actions = DeltaCourseOffering.actions()
    delta_response = None

    if action == 'delete':
        # delta exists, need to delete the comment
        if has_delta:
            dco = DeltaCourseOffering.objects.get(pk=delta_id)
            dco.extra_comment = None
            dco.save()
        else:
            updates_successful = False
            print('trying to delete a delta extra_comment, but there is no delta object...!')
    elif action == 'update':
        # delta exists, need to update the comment
        if has_delta:
            dco = DeltaCourseOffering.objects.get(pk=delta_id)
            dco.extra_comment = text[:500]
            dco.save()
        else:
            updates_successful = False
            print('trying to delete a delta extra_comment, but there is no delta object...!')
    else:
        # no delta, so need to create one; there _should_ be a banner object, but not not necessarily an iChair one
        
        if has_ichair and has_banner:
            dco = DeltaCourseOffering.objects.create(
                course_offering=ico,
                semester=ico.semester,
                crn=bco.crn,
                requested_action=delta_course_offering_actions["update"],
                extra_comment=text[:500])
            dco.save()
        else:
            print('there should be both an iChair course offering and a banner course offering in this case...!')
            updates_successful = False

    if dco:
        if dco.requested_action == delta_course_offering_actions["update"]:
            if has_ichair and has_banner:
                delta_response = delta_update_status(bco, ico, dco, check_rooms = include_room_comparisons)
        elif dco.requested_action == delta_course_offering_actions["create"]:
            if has_ichair:
                delta_response = delta_create_status(ico, dco, check_rooms = include_room_comparisons)
        elif dco.requested_action == delta_course_offering_actions["delete"]:
            delta_response = delta_delete_status(dco)

    data = {
        'updates_successful': updates_successful,
        'delta_response': delta_response
    }

    return JsonResponse(data)

@login_required
@csrf_exempt
def update_public_comments_api(request):
    """Update the public comments for a course offering.  Can do any combination of delete, create and update."""

    user = request.user
    user_preferences = user.user_preferences.all()[0]
    user_department = user_preferences.department_to_view

    json_data = json.loads(request.body)
    #print('data: ', json_data)

    course_offering_id = json_data['courseOfferingId']
    snapshot = json_data['snapshot']
    delete_ids = json_data['delete']
    update_dict = json_data['update']
    create_dict = json_data['create']
    has_banner = json_data['hasBanner']
    banner_id = json_data['bannerId']
    has_delta = json_data['hasDelta']
    delta = json_data['delta']
    include_room_comparisons = json_data['includeRoomComparisons']

    # delta course offering actions from the model itself:
    delta_course_offering_actions = DeltaCourseOffering.actions()

    try:
        course_offering = CourseOffering.objects.get(pk=course_offering_id)
        course_department = course_offering.course.subject.department
        #print('course dept: ', course_department)
        original_co_snapshot = course_offering.snapshot
        #print('original snapshot: ', original_co_snapshot)
        year = course_offering.semester.year
        #print("year: ", year)
    except:
        course_offering = None
        print('could not find the course offering....')

    # delete comments
    deletes_successful = True
    for delete_id in delete_ids:
        try:
            pc = CourseOfferingPublicComment.objects.get(pk=delete_id)
            pc.delete()
        except CourseOfferingPublicComment.DoesNotExist:
            print('unable to delete comment id = ', delete_id,
                  '; it may be that the object no longer exists.')
            deletes_successful = False

    # updates first....
    # https://stackoverflow.com/questions/7108080/python-get-the-first-character-of-the-first-string-in-a-list
    updates_successful = True
    for comment in update_dict:
        try:
            pc = CourseOfferingPublicComment.objects.get(pk=comment["id"])
            pc.text = comment["text"][:60] #shouldn't be longer than 60 characters, but truncate it just in case....
            pc.save()
        except:
            updates_successful = False
            print('not able to complete comment updates')

    # now create new comments
    creates_successful = True
    if course_offering:
        creates_successful = True
        for comment in create_dict:
            pc = CourseOfferingPublicComment.objects.create(
                course_offering=course_offering,
                text=comment["text"][:60],
                sequence_number=comment["sequence_number"])
            pc.save()
    else:
        creates_successful = False

    # now retrieve the comments from the db again
    if course_offering:
        comments = course_offering.comment_list()
    else:
        comments = {
            "summary": "",
            "comment_list": [],
            "summary_contains_all_text": True
        }

    pc_match = False
    delta_response = None
    if has_banner and course_offering:
        bco = BannerCourseOffering.objects.get(pk=banner_id)
        pc_match = public_comments_match(bco, course_offering)
        #print('public comments match? ', pc_match)
        if has_delta:
            # if has_banner and has_delta, then we are talking about a delta requested action of "update"
            dco = DeltaCourseOffering.objects.get(pk=delta["id"])
            delta_response = delta_update_status(bco, course_offering, dco, check_rooms = include_room_comparisons)
    elif (not(has_banner)) and course_offering:
        if has_delta:
            # in this case we are talking about a delta requested action of "create"
            dco = DeltaCourseOffering.objects.get(pk=delta["id"])
            if dco.requested_action != delta_course_offering_actions["create"]:
                print('we have a problem!!! expecting that delta is of the create type, but it is not...!')
            else:
                delta_response = delta_create_status(course_offering, dco, check_rooms = include_room_comparisons)
                pc_match = delta_response["request_update_public_comments"]

    if course_offering:
        if user_department != course_department:
            revised_co_snapshot = course_offering.snapshot
            create_message_course_offering_update(user.username, user_department, course_department, year,
                                        original_co_snapshot, revised_co_snapshot, ["public_comments"])
        if (len(delete_ids) > 0) or (len(update_dict) > 0) or (len(create_dict) > 0):
            snapshot["public_comments"] = original_co_snapshot["public_comments"]
    data = {
        'snapshot': snapshot,
        'updates_successful': updates_successful,
        'creates_successful': creates_successful,
        'deletes_successful': deletes_successful,
        'comments': comments,
        'public_comments_match': pc_match,
        'has_delta': has_delta,
        'delta': delta_response # will be None if there is no delta object
    }

    return JsonResponse(data)


@login_required
@csrf_exempt
def update_class_schedule_api(request):
    """Update the class schedule for a course offering.  Can do any combination of delete, create and update."""
    
    user = request.user
    user_preferences = user.user_preferences.all()[0]
    user_department = user_preferences.department_to_view

    json_data = json.loads(request.body)

    course_offering_id = json_data['courseOfferingId']
    snapshot = json_data['snapshot']
    delete_ids = json_data['delete']
    update_dict = json_data['update']
    create_dict = json_data['create']
    has_banner = json_data['hasBanner']
    banner_id = json_data['bannerId']
    has_delta = json_data['hasDelta']
    delta = json_data['delta']
    update_semester_fraction = json_data["updateSemesterFraction"]
    update_enrollment_cap = json_data["updateEnrollmentCap"]
    update_delivery_method = json_data["updateDeliveryMethod"]
    semester_fraction = json_data["semesterFraction"]
    enrollment_cap = json_data["enrollmentCap"]
    delivery_method_id = json_data["deliveryMethodId"]
    include_room_comparisons = json_data['includeRoomComparisons']

    #print('include room comparisons?', include_room_comparisons)

    # delta course offering actions from the model itself:
    delta_course_offering_actions = DeltaCourseOffering.actions()

    #print('update delivery method? ', update_delivery_method)
    #print('delivery method id: ', delivery_method_id)

    #print('sem fraction update? ', update_semester_fraction)
    #print('enrollment cap update? ', update_enrollment_cap)
    #print('semester fraction ', semester_fraction)
    #print('enrollment_cap ', enrollment_cap)
    #print('has banner?', has_banner)

    #print('delete ids: ', delete_ids)
    #print('update_dict: ', update_dict)
    #print('create_dict: ', create_dict)

    try:
        course_offering = CourseOffering.objects.get(pk=course_offering_id)
        course_department = course_offering.course.subject.department
        original_co_snapshot = course_offering.snapshot
        year = course_offering.semester.year
        #print(original_co_snapshot)
    except:
        course_offering = None
        print('could not find the course offering....')

    if delivery_method_id == None:
        delivery_method = None
    else:
        try:
            delivery_method = DeliveryMethod.objects.get(pk=delivery_method_id)
        except:
            print('unable to find the delivery method with id = ', delivery_method_id)
            delivery_method = None

    if course_offering:
        #print('found the course offering')
        if update_semester_fraction:
            course_offering.semester_fraction = semester_fraction
            course_offering.save()
        if update_enrollment_cap:
            course_offering.max_enrollment = enrollment_cap
            course_offering.save()
        if update_delivery_method:
            course_offering.delivery_method = delivery_method
            course_offering.save()
            
    # delete scheduled classes
    deletes_successful = True
    for delete_id in delete_ids:
        try:
            sc = ScheduledClass.objects.get(pk=delete_id)
            sc.delete()
        except ScheduledClass.DoesNotExist:
            print('unable to delete scheduled class id = ', delete_id,
                  '; it may be that the object no longer exists.')
            deletes_successful = False

    # define a regular expression to use for matching times....
    # https://docs.python.org/3/howto/regex.html#matching-characters
    p = re.compile('([0-1]?[0-9]|2[0-3]):([0-5][0-9])(:[0-5][0-9])?')

    # updates first....
    updates_successful = True
    for meeting in update_dict:
        try:
            sc = ScheduledClass.objects.get(pk=meeting['id'])
            # if begin_at or end_at does not match, begin or end evaluates to None
            begin = p.match(meeting['begin_at'])
            end = p.match(meeting['end_at'])
            day = int(meeting['day'])
            #room_id = meeting['roomId']
            room_ids = meeting['roomIds']
            if (begin and end and (day <= 4) and (day >= 0)):
                sc.begin_at = meeting['begin_at']
                sc.end_at = meeting['end_at']
                sc.day = day
                # first clear all rooms, then add in the ones in the rooms_ids list
                # https://docs.djangoproject.com/en/3.2/ref/models/relations/#django.db.models.fields.related.RelatedManager.clear
                sc.rooms.clear()
                for room_id in meeting['roomIds']:
                    room = Room.objects.get(pk=int(room_id))
                    sc.rooms.add(room)
                #if room_id == None:
                #    sc.room = None
                #else:
                #    room = Room.objects.get(pk=int(room_id))
                #    sc.room = room
                sc.save()
            else:
                updates_successful = False
        except:
            updates_successful = False
            print('not able to complete class schedule updates')

    # now create new scheduled classes
    if course_offering:
        creates_successful = True
        for meeting in create_dict:
            # if begin_at or end_at does not match, begin or end evaluates to None
            begin = p.match(meeting['begin_at'])
            end = p.match(meeting['end_at'])
            day = int(meeting['day'])
            #room_id = meeting['roomId']
            if (begin and end and (day <= 4) and (day >= 0)):
                sc = ScheduledClass.objects.create(
                    course_offering=course_offering,
                    day=day,
                    begin_at=meeting['begin_at'],
                    end_at=meeting['end_at'])
                #if room_id != None:
                #    room = Room.objects.get(pk=int(room_id))
                #    sc.room = room
                for room_id in meeting['roomIds']:
                    room = Room.objects.get(pk=int(room_id))
                    sc.rooms.add(room)
                sc.save()
            else:
                creates_successful = False
                print('not able to create new scheduled classes')
    else:
        creates_successful = False

    # now retrieve the scheduled classes, etc., from the db again
    if course_offering:
        meeting_times_list, room_list = class_time_and_room_summary(
            course_offering.scheduled_classes.all(), new_format = True)
        meeting_times_detail = construct_meeting_times_detail(course_offering, True)
        max_enrollment = course_offering.max_enrollment
        semester_fraction = course_offering.semester_fraction

        if user_department != course_department:
            revised_co_snapshot = course_offering.snapshot
            updated_fields = []
            if original_co_snapshot["semester_fraction"] != revised_co_snapshot["semester_fraction"]:
                updated_fields.append("semester_fraction")
            updated_fields.append("scheduled_classes")
            if original_co_snapshot["max_enrollment"] != revised_co_snapshot["max_enrollment"]:
                updated_fields.append("max_enrollment")
            create_message_course_offering_update(user.username, user_department, course_department, year,
                                        original_co_snapshot, revised_co_snapshot, updated_fields)

    else:
        meeting_times_list = []
        room_list = []
        meeting_times_detail = []
        max_enrollment = None
        semester_fraction = None

    schedules_match = False
    enrollment_caps_match = False
    sem_fractions_match = False
    del_methods_match = False
    delta_response = None
    if has_banner and course_offering:
        bco = BannerCourseOffering.objects.get(pk=banner_id)
        schedules_match = scheduled_classes_match(bco, course_offering, check_rooms = include_room_comparisons)
        #print('schedules match? ', schedules_match)
        enrollment_caps_match = max_enrollments_match(bco, course_offering)
        sem_fractions_match = semester_fractions_match(bco, course_offering)
        del_methods_match = delivery_methods_match(bco, course_offering)
        if has_delta:
            dco = DeltaCourseOffering.objects.get(pk=delta["id"])
            delta_response = delta_update_status(bco, course_offering, dco, check_rooms = include_room_comparisons)
    elif (not(has_banner)) and course_offering:
        if has_delta:
            # in this case we are talking about a delta requested action of "create"
            dco = DeltaCourseOffering.objects.get(pk=delta["id"])
            if dco.requested_action != delta_course_offering_actions["create"]:
                print('we have a problem!!! expecting that delta is of the create type, but it is not...!')
            else:
                delta_response = delta_create_status(course_offering, dco, check_rooms = include_room_comparisons)
                schedules_match = delta_response["request_update_meeting_times"]
                sem_fractions_match = delta_response["request_update_semester_fraction"]
                enrollment_caps_match = delta_response["request_update_max_enrollment"]
                del_methods_match = delta_response["request_update_delivery_method"]
    if update_semester_fraction:
        snapshot["semester_fraction"] = original_co_snapshot["semester_fraction"]
    if update_enrollment_cap:
        snapshot["max_enrollment"] = original_co_snapshot["max_enrollment"]
    if update_delivery_method:
        snapshot["delivery_method"] = original_co_snapshot["delivery_method"]
    if (len(delete_ids) > 0) or (len(update_dict) > 0) or (len(create_dict) > 0):
        snapshot["scheduled_classes"] = original_co_snapshot["scheduled_classes"]

    data = {
        'snapshot': snapshot,
        'updates_successful': updates_successful,
        'creates_successful': creates_successful,
        'deletes_successful': deletes_successful,
        'meeting_times': meeting_times_list,
        'rooms': room_list,
        'meeting_times_detail': meeting_times_detail,
        'schedules_match': schedules_match,
        'max_enrollments_match': enrollment_caps_match,
        'semester_fractions_match': sem_fractions_match,
        'delivery_methods_match': del_methods_match,
        'max_enrollment': max_enrollment,
        'semester_fraction': semester_fraction,
        'delivery_method': create_delivery_method_dict(delivery_method),
        'has_delta': has_delta,
        'delta': delta_response # will be None if there is no delta object
    }

    return JsonResponse(data)


@login_required
@csrf_exempt
def copy_course_offering_data_to_ichair(request):
    """
    Update properties of an existing course offering either by copying data from a banner course offering 
    or by copying it from a "snapshot" object.  The "copyFromBanner" boolean dictates which action is being done.
    """
    # user = request.user
    # user_preferences = user.user_preferences.all()[0]

    user = request.user
    user_preferences = user.user_preferences.all()[0]
    user_department = user_preferences.department_to_view

    faculty_to_view_ids = [fm.id for fm in user_preferences.faculty_to_view.all()]

    day_sorter_dict = {
        'M': 0,
        'T': 1,
        'W': 2,
        'R': 3,
        'F': 4
    }

    json_data = json.loads(request.body)

    action = json_data['action']
    # if action == 'update', we are updating an existing course offering, in which case only the 'update' properties will be present in course_offering_properties

    ichair_course_offering_id = json_data['iChairCourseOfferingId']
    banner_course_offering_id = json_data['bannerCourseOfferingId']

    has_banner = json_data['hasBanner']
    copy_from_banner = json_data['copyFromBanner'] # if False, will use the data in the snapshot object; if True, will get the data from the Banner version of the course offering
    
    snapshot = json_data['snapshot']
    properties_to_update = json_data["propertiesToUpdate"]

    department_id = json_data['departmentId']
    year_id = json_data['yearId']

    department = Department.objects.get(pk=department_id)
    academic_year = AcademicYear.objects.get(pk = year_id)
    # if there is no banner course offering id, this will be None
    delta_id = json_data['deltaId']
    # if delta is None (i.e., null in the the javascript code), then there is no known delta object for this iChair course offering;
    # if there is a delta object, then we will search for it and be sure to update it as appropriate after making the iChair changes....

    include_room_comparisons = json_data['includeRoomComparisons']
    #print("include room comparisons?", include_room_comparisons)

    #print('banner course offering id: ', banner_course_offering_id)
    #print('delta id: ', delta_id)
    #print('properties_to_update', properties_to_update)

    delta_response = None
    agreement_update = None
    course_offering_update = None
    offering_instructors_copied_successfully = True
    load_manipulation_performed = False
    classrooms_unassigned = False

    if action == 'update':
        # try:
        ico = CourseOffering.objects.get(
            pk=ichair_course_offering_id)  # iChair course offering
        course_department = ico.course.subject.department
        snapshot_from_db = ico.snapshot
    
        if has_banner:
            bco = BannerCourseOffering.objects.get(
                pk=banner_course_offering_id)
            #print('banner course offering: ', bco)
        #print('ichair course offering: ', ico)
        
        if 'max_enrollment' in properties_to_update:
            if copy_from_banner:
                ico.max_enrollment = bco.max_enrollment
                ico.save()
                snapshot["max_enrollment"] = snapshot_from_db["max_enrollment"]
            else:
                ico.max_enrollment = snapshot["max_enrollment"]
                ico.save()
        if 'delivery_method' in properties_to_update:
            if copy_from_banner:
                if bco.delivery_method == None:
                    ico.delivery_method = None
                    ico.save()
                else:
                    delivery_methods = DeliveryMethod.objects.filter(code = bco.delivery_method.code)
                    if len(delivery_methods) == 1:
                        ico.delivery_method = delivery_methods[0]
                        ico.save()
                snapshot["delivery_method"] = snapshot_from_db["delivery_method"]
            else:
                if snapshot["delivery_method"]["id"] == None:
                    ico.delivery_method = None
                    ico.save()
                else:
                    delivery_method = DeliveryMethod.objects.get(pk=snapshot["delivery_method"]["id"])
                    ico.delivery_method = delivery_method
                    ico.save()
        if 'comments' in properties_to_update:
            # first delete any existing iChair comments
            existing_iChair_comments = ico.comment_list()
            for ico_comment_data in existing_iChair_comments["comment_list"]:
                ico_comment = CourseOfferingPublicComment.objects.get(pk=ico_comment_data["id"])
                deleted_comment = ico_comment.delete()
                #print('iChair comment was deleted: ', deleted_comment)
            if copy_from_banner:
                # now copy over the banner comments
                banner_comments = bco.comment_list()
                for comment in banner_comments["comment_list"]:
                    new_comment = CourseOfferingPublicComment.objects.create(
                        course_offering = ico,
                        text = comment["text"],
                        sequence_number = comment["sequence_number"])
                    new_comment.save()
                snapshot["public_comments"] = snapshot_from_db["public_comments"]
            else:
                for comment in snapshot["public_comments"]:
                    new_comment = CourseOfferingPublicComment.objects.create(
                        course_offering = ico,
                        text = comment["text"],
                        sequence_number = comment["sequence_number"])
                    new_comment.save()
        if 'semester_fraction' in properties_to_update:
            if copy_from_banner:
                ico.semester_fraction = bco.semester_fraction
                ico.save()
                snapshot["semester_fraction"] = snapshot_from_db["semester_fraction"]
            else:
                ico.semester_fraction = snapshot["semester_fraction"]
                ico.save()
        if 'instructors' in properties_to_update:
            ichair_offering_instructors = ico.offering_instructors.all()
            if copy_from_banner:
                # we take a conservative approach here:
                # - if any of the ichair offering instructors does not have a pidm, leave things alone for that instructor
                banner_offering_instructors = bco.offering_instructors.all()
                banner_instructor_pidms = [
                    boi.instructor.pidm for boi in banner_offering_instructors]

                for ichair_oi in ichair_offering_instructors:
                    if (ichair_oi.instructor.pidm is None) or (ichair_oi.instructor.pidm == ''):
                        print(
                            'one of the iChair instructors does not have a pidm...bailing!')
                        offering_instructors_copied_successfully = False
                        #break
                    elif ichair_oi.instructor.pidm not in banner_instructor_pidms:
                        #print('the following iChair instructor is not in the banner list: ',
                        #    ichair_oi.instructor.first_name, ichair_oi.instructor.last_name)
                        #print('...this instructor will be deleted')
                        # the object may be deleted inside the loop: https://stackoverflow.com/questions/16466945/iterating-over-a-django-queryset-while-deleting-objects-in-the-same-queryset
                        ichair_oi.delete()
                    else:
                        # the current iChair instructor is in the banner list, so pop the person out of the banner list so we don't create them later
                        # first, though, set the is_primary flag to the correct value
                        matching_boi = None
                        for boi in banner_offering_instructors:
                            if boi.instructor.pidm == ichair_oi.instructor.pidm:
                                matching_boi = boi
                        if matching_boi is not None:
                            # align the is_primary flag....
                            ichair_oi.is_primary = matching_boi.is_primary
                            ichair_oi.save()
                            #print('now pop out of the banner pidm list....')
                            #print('before: ', banner_instructor_pidms)
                            # now pop the matching banner instructor out of the pidm list (https://stackoverflow.com/questions/4915920/how-to-delete-an-item-in-a-list-if-it-exists)
                            while ichair_oi.instructor.pidm in banner_instructor_pidms:
                                banner_instructor_pidms.remove(
                                    ichair_oi.instructor.pidm)
                            #print('after: ', banner_instructor_pidms)
                        else:
                            # something has gone wrong
                            offering_instructors_copied_successfully = False
                            break

                # now that the ichair offering_instructor list has been culled, go through and add in any other instructors from the banner list
                for boi in banner_offering_instructors:
                    if boi.instructor.pidm in banner_instructor_pidms:
                        ichair_instructors = FacultyMember.objects.filter(
                            pidm=boi.instructor.pidm)
                        if len(ichair_instructors) != 1:
                            offering_instructors_copied_successfully = False
                            print(
                                'there seem to be more than one iChair instructor with this pidm: ', boi.instructor.pidm)
                        else:
                            instructor = ichair_instructors[0]
                            if instructor.is_active(academic_year):
                                offering_instructor = OfferingInstructor.objects.create(
                                    course_offering=ico,
                                    instructor=instructor,
                                    load_credit=0,
                                    is_primary=boi.is_primary)
                                offering_instructor.save()
                            else:
                                #print('this instructor is not active, so not copying data over....')
                                offering_instructors_copied_successfully = False

                # now go through the list of offering instructors again and adjust loads....
                # trying to be careful about rounding and floats....
                if ico.load_difference() > 0.001:
                    #print('load difference is: ', ico.load_difference())
                    ichair_offering_instructors = ico.offering_instructors.all()
                    for offering_instructor in ichair_offering_instructors:
                        if len(ichair_offering_instructors) == 1:
                            # give this person all of the load credit
                            offering_instructor.load_credit = ico.load_available
                            offering_instructor.save()
                            load_manipulation_performed = True
                        # trying to be careful about rounding and floats....
                        elif (offering_instructor.load_credit < 0.001) and (ico.load_difference() > 0):
                            # if there is more than one instructor, the first one in the list who doesn't have load gets the remaining load....
                            # ...at least this way the loads add up to the correct total
                            offering_instructor.load_credit = ico.load_difference()
                            offering_instructor.save()
                            #print('and now load difference is: ',
                            #    ico.load_difference())
                            load_manipulation_performed = True
                snapshot["offering_instructors"] = snapshot_from_db["offering_instructors"]
            else:
                ico.load_available = snapshot["load_available"]
                ico.save()
                for ichair_oi in ichair_offering_instructors:
                    ichair_oi.delete()
                for oi in snapshot["offering_instructors"]:
                    instructor = FacultyMember.objects.get(pk=oi["instructor"]["id"])
                    if instructor.is_active(academic_year):
                        offering_instructor = OfferingInstructor.objects.create(
                            course_offering=ico,
                            instructor=instructor,
                            load_credit=oi["load_credit"],
                            is_primary=oi["is_primary"])
                        offering_instructor.save()
                    else:
                        #print('this instructor is not active, so not copying data over....')
                        offering_instructors_copied_successfully = False

        if 'meeting_times' in properties_to_update:
            if copy_from_banner:
                
                banner_scheduled_classes = bco.scheduled_classes.all()

                if not include_room_comparisons:
                    # in this case, we don't want to unintentionally lose room information, so we can't just delete all existing meeting times and start over....
                    for ichair_sc in ico.scheduled_classes.all():
                        # first, check to see if there is a similar object in the banner list....
                        #  - if not, delete the scheduled class from iChair
                        #  - if it is found in the banner list, pop the corresponding item out of the banner list
                        banner_match = None
                        #print('ichair meeting time: ', ichair_sc)
                        for banner_sc in banner_scheduled_classes:
                            if (ichair_sc.day == banner_sc.day) and (ichair_sc.begin_at == banner_sc.begin_at) and (ichair_sc.end_at == banner_sc.end_at):
                                banner_match = banner_sc
                                print('found a banner match!', banner_match)
                        if banner_match is None:
                            #print(
                            #    'no corresponding banner match; deleting iChair meeting time....')
                            # apparently this is OK to do while iterating through the queryset....
                            ichair_sc.delete()
                        else:
                            #print('popping the banner match out of the list')
                            #print('before: ', banner_scheduled_classes)
                            # https://stackoverflow.com/questions/1207406/how-to-remove-items-from-a-list-while-iterating
                            banner_scheduled_classes = [
                                bsc for bsc in banner_scheduled_classes if not banner_match.id == bsc.id]
                            #print('after: ', banner_scheduled_classes)
                else:
                    # in this case, we assume the user wants to copy over both meeting time and room information
                    for ichair_sc in ico.scheduled_classes.all():
                        ichair_sc.delete()

                # now we go through the remaining banner meeting times and copy them over to iChair
                for banner_sc in banner_scheduled_classes:
                    # if the banner scheduled class has a room, try to find a corresponding room in the iChair database
                    ichair_room = None
                    classrooms_unassigned = True

                    #sc.rooms.clear()
                    #for room_id in meeting['roomIds']:
                    #    room = Room.objects.get(pk=int(room_id))
                    #    sc.rooms.add(room)
                    ichair_rooms_to_add = []
                    for banner_room in banner_sc.rooms.all():
                        ichair_rooms = Room.objects.filter(Q(number=banner_room.number) & Q(building__abbrev=banner_room.building.abbrev))
                        if len(ichair_rooms) > 1:
                            print("ERROR!!!  There appear to be more than one iChair room with the same name.")
                        elif len(ichair_rooms) == 1:
                            ichair_rooms_to_add.append(ichair_rooms[0])
                            classrooms_unassigned = False
                        else:
                            print("ERROR!!!  There does not appear to be an iChair room for this Banner room.", banner_room)

                    isc = ScheduledClass.objects.create(
                        day=banner_sc.day,
                        begin_at=banner_sc.begin_at,
                        end_at=banner_sc.end_at,
                        course_offering=ico
                    )
                    
                    for ichair_room in ichair_rooms_to_add:
                        isc.rooms.add(ichair_room)

                    isc.save()
                
                snapshot["scheduled_classes"] = snapshot_from_db["scheduled_classes"]
            else:
                for ichair_sc in ico.scheduled_classes.all():
                    ichair_sc.delete()
                for sc in snapshot["scheduled_classes"]:
                    isc = ScheduledClass.objects.create(
                            day=sc["day"],
                            begin_at=sc["begin_at"],
                            end_at=sc["end_at"],
                            course_offering=ico
                        )
                    for room in sc["rooms"]:
                        room = Room.objects.get(pk=int(room["id"]))
                        print("found room in snapshot!", room)
                        isc.rooms.add(room)
                    isc.save()
                    
                    
        # the following code is copied from above...if we need it again somewhere, should
        # consider putting this all in a function
        presorted_ico_meeting_times_list, presorted_ico_room_list = class_time_and_room_summary(ico.scheduled_classes.all(), new_format = True)
        ico_meeting_times_list = sorted(presorted_ico_meeting_times_list, key=lambda item: (day_sorter_dict[item[:1]]))

        # sort the rooms so that the sort order matches that of the meeting times....
        ico_room_list = sort_rooms(presorted_ico_meeting_times_list, ico_meeting_times_list, presorted_ico_room_list)

        ico_instructors = construct_instructor_list(ico, True)
        ico_instructors_detail = construct_ichair_instructor_detail_list(ico)
        available_instructors = department.available_instructors(academic_year, ico, faculty_to_view_ids)

        meeting_times_detail = construct_meeting_times_detail(ico, True)

        if has_banner:
            if delta_id is not None:
                dco = DeltaCourseOffering.objects.get(pk=delta_id)
                #print('delta course offering: ', dco)
                delta_response = delta_update_status(bco, ico, dco, check_rooms = include_room_comparisons)

                schedules_match = scheduled_classes_match(
                    bco, ico, check_rooms = include_room_comparisons) or delta_response["request_update_meeting_times"]
                inst_match = instructors_match(
                    bco, ico) or delta_response["request_update_instructors"]
                sem_fractions_match = semester_fractions_match(
                    bco, ico) or delta_response["request_update_semester_fraction"]
                enrollment_caps_match = max_enrollments_match(
                    bco, ico) or delta_response["request_update_max_enrollment"]
                comments_match = public_comments_match(
                    bco, ico) or delta_response["request_update_public_comments"]
                del_methods_match = delivery_methods_match(
                    bco, ico) or delta_response["request_update_delivery_method"]
            else:
                schedules_match = scheduled_classes_match(bco, ico, check_rooms = include_room_comparisons)
                inst_match = instructors_match(bco, ico)
                sem_fractions_match = semester_fractions_match(
                    bco, ico)
                enrollment_caps_match = max_enrollments_match(bco, ico)
                # KK: increased the indent of the following line because it seemed to be incorrect....from the git history, it looks like an
                # a block of text was indented together, but the last line was missed....
                comments_match = public_comments_match(bco, ico)
                del_methods_match = delivery_methods_match(bco, ico)

        agreement_update = {
            "instructors_match": inst_match if has_banner else False,
            "meeting_times_match": schedules_match if has_banner else False,
            "max_enrollments_match": enrollment_caps_match if has_banner else False,
            "semester_fractions_match": sem_fractions_match if has_banner else False,
            "public_comments_match": comments_match if has_banner else False,
            "delivery_methods_match": del_methods_match if has_banner else False
        }

        # "change_can_be_undone" here is just looking locally at what has been done; the client can make a better judgement
        # about this than the server can, so some of these settings might be overruled by the client-side code....
        if copy_from_banner:
            change_can_be_undone = {
                "max_enrollment": 'max_enrollment' in properties_to_update,
                "public_comments": 'comments' in properties_to_update,
                "semester_fraction": 'semester_fraction' in properties_to_update,
                "instructors": 'instructors' in properties_to_update,
                "meeting_times": 'meeting_times' in properties_to_update,
                "delivery_method": 'delivery_method' in properties_to_update,
            }
        else:
            change_can_be_undone = {
                "max_enrollment": False,
                "comments": False,
                "semester_fraction": False,
                "instructors": False,
                "meeting_times": False,
                "delivery_method": False,
            }

        course_offering_update = {
            "course_offering_id": ico.id,
            "course_id": ico.course.id,
            "meeting_times": ico_meeting_times_list,
            "meeting_times_detail": meeting_times_detail,
            "rooms": ico_room_list,
            "instructors": ico_instructors,
            "instructors_detail": ico_instructors_detail,
            "available_instructors": available_instructors,
            "snapshot": snapshot,
            "change_can_be_undone": change_can_be_undone,
            "load_available": ico.load_available,
            "semester": ico.semester.name.name,
            "semester_fraction": int(ico.semester_fraction),
            "max_enrollment": int(ico.max_enrollment),
            "comments": ico.comment_list(),
            "delivery_method": create_delivery_method_dict(ico.delivery_method)}

        if user_department != course_department:
            revised_co_snapshot = ico.snapshot
            updated_fields = []
            if snapshot_from_db["semester_fraction"] != revised_co_snapshot["semester_fraction"]:
                updated_fields.append("semester_fraction")
            if 'meeting_times' in properties_to_update:
                updated_fields.append("scheduled_classes")
            if 'instructors' in properties_to_update:
                updated_fields.append("offering_instructors")
            if snapshot_from_db["load_available"] != revised_co_snapshot["load_available"]:
                updated_fields.append("load_available")
            if snapshot_from_db["max_enrollment"] != revised_co_snapshot["max_enrollment"]:
                updated_fields.append("max_enrollment")
            if 'comments' in properties_to_update:
                updated_fields.append("public_comments")
            if 'delivery_method' in properties_to_update:
                updated_fields.append("delivery_method")
            create_message_course_offering_update(user.username, user_department, course_department, academic_year,
                                                snapshot_from_db, revised_co_snapshot, updated_fields)

    data = {
        'delta_response': delta_response,
        'agreement_update': agreement_update,
        'course_offering_update': course_offering_update,
        'offering_instructors_copied_successfully': offering_instructors_copied_successfully,
        'load_manipulation_performed': load_manipulation_performed,
        'classrooms_unassigned': classrooms_unassigned
    }

    return JsonResponse(data)


@login_required
@csrf_exempt
def update_view_list(request):
    """Add a faculty member to the list of faculty to view; used for AJAX requests."""
    user = request.user
    user_preferences = user.user_preferences.all()[0]
    faculty_id = request.POST.get('facultyId')

    try:
        faculty = FacultyMember.objects.get(pk=faculty_id)
    except FacultyMember.DoesNotExist:
        data = {
            'success': False,
            'message': 'This faculty member could not be found; please try again later or contact the site administrator.'
        }
        return JsonResponse(data)
    if faculty not in user_preferences.faculty_to_view.all():
        user_preferences.faculty_to_view.add(faculty)
        data = {
            'success': True,
            'message': 'Faculty member added!'
        }
        return JsonResponse(data)
    else:
        data = {
            'success': False,
            'message': 'It appears that '+faculty.first_name+' '+faculty.last_name+' is already in your list of faculty to view.'
        }
        return JsonResponse(data)

    data = {
        'success': False,
        'message': 'Sorry, we were not able to process this request.'
    }
    return JsonResponse(data)


@login_required
def load_courses(request):

    subject_id = request.GET.get('subjectId')
    courses = Course.objects.filter(subject__id=subject_id).order_by('number')
    return render(request, 'course_dropdown_list_options.html', {'courses': courses})
