from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from .models import *
from banner.models import Course as BannerCourse
from banner.models import CourseOffering as BannerCourseOffering
from banner.models import ScheduledClass as BannerScheduledClass
from banner.models import FacultyMember as BannerFacultyMember
from banner.models import OfferingInstructor as BannerOfferingInstructor

from .helper_functions import *

from django.shortcuts import render

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import re


@login_required
def fetch_semesters(request):
    department_id = request.GET.get('departmentId')
    year_id = request.GET.get('yearId')

    academic_year = AcademicYear.objects.get(pk=year_id)
    semesters = academic_year.semesters.all()
    semester_choices = []
    for semester in semesters:
        semester_choices.append({
            "semester_name": '{0} {1}'.format(semester.name, semester.year),
            "id": semester.id,
            "banner_code": semester.banner_code
        })
    data = {
        "semester_choices": semester_choices
    }
    return JsonResponse(data)


@login_required
def fetch_courses_to_be_aligned(request):
    department_id = request.GET.get('departmentId')
    year_id = request.GET.get('yearId')
    academic_year = AcademicYear.objects.get(pk=year_id)
    department = Department.objects.get(pk=department_id)

    unmatched_courses = []
    for subject in department.subjects.all():
        print(subject, subject.abbrev)
        # print(BannerCourse.objects.all
        for banner_course in BannerCourse.objects.filter(subject__abbrev=subject.abbrev):
            ichair_courses = Course.objects.filter(
                Q(subject__abbrev=banner_course.subject.abbrev) &
                Q(number__startswith=banner_course.number) &
                Q(credit_hours=banner_course.credit_hours))

            exact_match = False
            multiple_potential_matches = False

            for ichair_course in ichair_courses:
                # found a match...
                if (banner_course.title == ichair_course.title) or (banner_course.title == ichair_course.banner_title):
                    # uh-oh...we had already found a match -- this means we have more than one potential match, so we will list them all
                    if (exact_match == True) and (multiple_potential_matches == False):
                        exact_match = False
                        multiple_potential_matches = True
                    elif (exact_match == False) and (multiple_potential_matches == False):
                        exact_match = True

            if exact_match == False:
                ichair_course_data = [  # all the candidate iChair courses
                    {
                        "subject": c.subject.abbrev,
                        "number": c.number,
                        "credit_hours": c.credit_hours,
                        "title": c.title,
                        "id": c.id,
                        "banner_title": c.banner_title,
                        "number_offerings_this_year": c.number_offerings_this_year(academic_year)
                    } for c in ichair_courses]
                unmatched_courses.append({
                    "ichair_subject_id": subject.id,
                    "banner_course": {
                        "id": banner_course.id,
                        "subject": banner_course.subject.abbrev,
                        "number": banner_course.number,
                        "credit_hours": banner_course.credit_hours,
                        "title": banner_course.title
                    },
                    "ichair_courses": ichair_course_data
                })

    for bc in unmatched_courses:
        print(bc)

    data = {
        "unmatched_courses": unmatched_courses
    }
    return JsonResponse(data)


@login_required
@csrf_exempt
def create_update_courses(request):

    json_data = json.loads(request.body)
    update_dict = json_data['update']
    create_dict = json_data['create']

    print('update: ', update_dict)
    print('create: ', create_dict)

    creates_successful = True
    updates_successful = True
    print('updating....')
    for update_item in update_dict:
        print(update_item)
        # course = Course.objects.get(pk = update_item.ichair_course_id)
        try:
            course = Course.objects.get(pk=update_item["ichair_course_id"])
            print(course)
            course.banner_title = update_item["banner_title"]
            course.save()
        except:
            creates_successful = False

    print('creating...')
    for create_item in create_dict:
        print(create_item)
        try:
            subject = Subject.objects.get(pk=create_item["subject_id"])
            print(subject)
            course = Course.objects.create(
                title=create_item["title"],
                credit_hours=create_item["credit_hours"],
                subject=subject,
                number=create_item["number"])
            course.save()
            print(course)
        except:
            updates_successful = False

    data = {
        'updates_successful': updates_successful,
        'creates_successful': creates_successful
    }
    return JsonResponse(data)


@login_required
@csrf_exempt
def banner_comparison_data(request):

    json_data = json.loads(request.body)
    department_id = json_data['departmentId']
    year_id = json_data['yearId']
    semester_ids = json_data['semesterIds']

    day_sorter_dict = {
        'M': 0,
        'T': 1,
        'W': 2,
        'R': 3,
        'F': 4
    }

    print('dept id: ', department_id)
    print('year id: ', year_id)
    print('semester ids:', semester_ids)

    semester_sorter_dict = {}
    counter = 0
    for semester_id in semester_ids:
        semester_sorter_dict[semester_id] = counter
        counter = counter+1

    print('semesters')
    print(semester_sorter_dict)

    department = Department.objects.get(pk=department_id)
    # academic_year = AcademicYear.objects.get(pk = year_id)

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

    course_offering_data = []

    for semester_id in semester_ids:
        semester = Semester.objects.get(pk=semester_id)
        term_code = semester.banner_code
        # eventually expand this to include extra-departmental courses taught by dept...?
        for subject in department.subjects.all():
            # first should reset all crns of the iChair course offerings, so we start with a clean slate
            # should also reset all ichair_ids for the Banner course offerings, for the same reason (that's done below)

            # RESET CRNs of all corresponding iChair course offerings (i.e., start from scratch)
            for course_offering in CourseOffering.objects.filter(
                    Q(semester=semester) &
                    Q(course__subject=subject)):
                course_offering.crn = None
                course_offering.save()

            banner_course_offerings = BannerCourseOffering.objects.filter(
                Q(course__subject__abbrev=subject.abbrev) & Q(term_code=term_code))

            # the following is an initial round of attempting to link up banner courses with iChair courses
            # once this is done, we can cycle through the linked courses (which should be 1-to-1 at that point) and add them to a list
            # then we can cycle through any unlinked courses on both sides and add them to the list
            # then we should sort the list so the order doesn't seem crazy

            for bco in banner_course_offerings:
                print(bco)
                # attempt to assign an iChair course offering to the banner one
                find_ichair_course_offering(bco, semester, subject)

            # now we cycle through all the banner course offerings and add them to the list
            for bco in banner_course_offerings:
                presorted_bco_meeting_times_list = class_time_and_room_summary(
                    bco.scheduled_classes.all(), include_rooms=False)
                # >>> Note: if the room list is ever included in the above, will need to be more careful about the sorting
                # >>> that is done below, since the room list order and the meeting times order are correlated!
                bco_meeting_times_list = sorted(
                    presorted_bco_meeting_times_list, key=lambda item: (day_sorter_dict[item[:1]]))
                # https://stackoverflow.com/questions/7108080/python-get-the-first-character-of-the-first-string-in-a-list
                # do some sorting so that the meeting times (hopefully) come out in the same order for the bco and ico cases....
                bco_instructors = construct_instructor_list(bco)

                course_offering_item = {
                    "semester": semester.name.name,
                    "semester_id": semester.id,
                    "course": bco.course.subject.abbrev+' '+bco.course.number,
                    "credit_hours": bco.course.credit_hours,
                    "course_title": bco.course.title,
                    "schedules_match": False,
                    "instructors_match": False,
                    "semester_fractions_match": False,
                    "enrollment_caps_match": False,
                    "banner": {
                        "course_offering_id": bco.id,
                        "meeting_times": bco_meeting_times_list,
                        "rooms": [],
                        "instructors": bco_instructors,
                        "term_code": bco.term_code,
                        "semester_fraction": int(bco.semester_fraction),
                        "max_enrollment": int(bco.max_enrollment)
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
                    "crn": bco.crn
                }

                if bco.is_linked:
                    # get the corresponding iChair course offering
                    try:
                        ico = CourseOffering.objects.get(pk=bco.ichair_id)
                        # ico_meeting_times_list, ico_room_list = class_time_and_room_summary(ico.scheduled_classes.all(), include_rooms = False)
                        # >>> Note: if the room list is ever included (as above), will need to be more careful about the sorting
                        # >>> that is done below, since the room list order and the meeting times order are correlated!
                        presorted_ico_meeting_times_list = class_time_and_room_summary(
                            ico.scheduled_classes.all(), include_rooms=False)
                        # do some sorting so that the meeting times (hopefully) come out in the same order for the bco and ico cases....
                        ico_meeting_times_list = sorted(
                            presorted_ico_meeting_times_list, key=lambda item: (day_sorter_dict[item[:1]]))

                        ico_instructors = construct_instructor_list(ico)

                        meeting_times_detail = construct_meeting_times_detail(
                            ico)

                        # schedules_match = scheduled_classes_match(bco, ico)
                        # inst_match = instructors_match(bco, ico)
                        # sem_fractions_match = semester_fractions_match(
                        #    bco, ico)
                        # enrollment_caps_match = max_enrollments_match(bco, ico)

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
                            print('delta object(s) found for', bco)
                            recent_delta_object = delta_objects[0]
                            for delta_object in delta_objects:
                                print(delta_object, delta_object.updated_at)
                                if delta_object.updated_at > recent_delta_object.updated_at:
                                    recent_delta_object = delta_object
                                    print('found more recent!',
                                          recent_delta_object.updated_at)

                            delta_response = delta_update_status(
                                bco, ico, recent_delta_object)
                            course_offering_item["delta"] = delta_response

                        if delta_exists:
                            # either these properties already match, or we are going to request a change from the registrar so that they do match
                            schedules_match = scheduled_classes_match(
                                bco, ico) or delta_response["request_update_meeting_times"]
                            inst_match = instructors_match(
                                bco, ico) or delta_response["request_update_instructors"]
                            sem_fractions_match = semester_fractions_match(
                                bco, ico) or delta_response["request_update_semester_fraction"]
                            enrollment_caps_match = max_enrollments_match(
                                bco, ico) or delta_response["request_update_max_enrollment"]
                        else:
                            schedules_match = scheduled_classes_match(bco, ico)
                            inst_match = instructors_match(bco, ico)
                            sem_fractions_match = semester_fractions_match(
                                bco, ico)
                            enrollment_caps_match = max_enrollments_match(
                                bco, ico)

                        course_offering_item["ichair"] = {
                            "course_offering_id": ico.id,
                            "meeting_times": ico_meeting_times_list,
                            "meeting_times_detail": meeting_times_detail,
                            # "rooms": ico_room_list,
                            "instructors": ico_instructors,
                            "semester": ico.semester.name.name,
                            "semester_fraction": int(ico.semester_fraction),
                            "max_enrollment": int(ico.max_enrollment),
                        }
                        course_offering_item["has_ichair"] = True
                        course_offering_item["linked"] = True
                        course_offering_item["schedules_match"] = schedules_match
                        course_offering_item["instructors_match"] = inst_match
                        course_offering_item["semester_fractions_match"] = sem_fractions_match
                        course_offering_item["enrollment_caps_match"] = enrollment_caps_match

                        course_offering_item["all_OK"] = schedules_match and inst_match and sem_fractions_match and enrollment_caps_match

                    except CourseOffering.DoesNotExist:
                        print(
                            'OOPS!  Looking for a course offering that does not exist....')
                        print(bco)

                else:
                    # look for possible ichair course offering matches for this unlinked banner course offering
                    unlinked_ichair_course_offerings = find_unlinked_ichair_course_offerings(
                        bco, semester, subject)
                    print('bco...', bco)
                    print('some iChair options:')
                    for unlinked_ico in unlinked_ichair_course_offerings:
                        print(unlinked_ico)
                        presorted_ico_meeting_times_list = class_time_and_room_summary(
                            unlinked_ico.scheduled_classes.all(), include_rooms=False)
                        # do some sorting so that the meeting times (hopefully) come out in the same order for the bco and ico cases....
                        ico_meeting_times_list = sorted(
                            presorted_ico_meeting_times_list, key=lambda item: (day_sorter_dict[item[:1]]))

                        ico_instructors = construct_instructor_list(
                            unlinked_ico)

                        meeting_times_detail = construct_meeting_times_detail(
                            unlinked_ico)
                        course_offering_item["ichair_options"].append({
                            "course_title": unlinked_ico.course.title,
                            "course": unlinked_ico.course.subject.abbrev+' '+unlinked_ico.course.number,
                            "credit_hours": unlinked_ico.course.credit_hours,
                            "course_offering_id": unlinked_ico.id,
                            "meeting_times": ico_meeting_times_list,
                            "meeting_times_detail": meeting_times_detail,
                            # "rooms": ico_room_list,
                            "instructors": ico_instructors,
                            "semester": unlinked_ico.semester.name.name,
                            "semester_fraction": int(unlinked_ico.semester_fraction),
                            "max_enrollment": int(unlinked_ico.max_enrollment)})

                course_offering_data.append(course_offering_item)

            # and now we go through the remaining iChair course offerings (i.e., the ones that have not been linked to banner course offerings)
            for ico in CourseOffering.objects.filter(
                    Q(semester=semester) &
                    Q(course__subject=subject) &
                    Q(crn__isnull=True)):

                # ico_meeting_times_list, ico_room_list = class_time_and_room_summary(ico.scheduled_classes.all(), include_rooms = False)
                # >>> Note: if the room list is ever included (as above), will need to be more careful about the sorting
                # >>> that is done below, since the room list order and the meeting times order are correlated!
                presorted_ico_meeting_times_list = class_time_and_room_summary(
                    ico.scheduled_classes.all(), include_rooms=False)
                # do some sorting so that the meeting times (hopefully) come out in the same order for the bco and ico cases....
                ico_meeting_times_list = sorted(
                    presorted_ico_meeting_times_list, key=lambda item: (day_sorter_dict[item[:1]]))

                ico_instructors = construct_instructor_list(ico)
                meeting_times_detail = construct_meeting_times_detail(ico)

                course_offering_item = {
                    "semester": semester.name.name,
                    "semester_id": semester.id,
                    "course": ico.course.subject.abbrev+' '+ico.course.number,
                    "credit_hours": ico.course.credit_hours,
                    "course_title": ico.course.title,
                    "schedules_match": False,
                    "instructors_match": False,
                    "semester_fractions_match": False,
                    "enrollment_caps_match": False,
                    "banner": {},
                    "ichair": {
                        "course_offering_id": ico.id,
                        "meeting_times": ico_meeting_times_list,
                        "meeting_times_detail": meeting_times_detail,
                        # "rooms": ico_room_list,
                        "instructors": ico_instructors,
                        "semester": ico.semester.name.name,
                        "semester_fraction": int(ico.semester_fraction),
                        "max_enrollment": int(ico.max_enrollment)
                    },
                    # options for possible matches (if the banner course offering is linked to an iChair course offering, this list remains empty)
                    "ichair_options": [],
                    "banner_options": [],
                    "has_banner": False,
                    "has_ichair": True,
                    "linked": False,
                    "delta": None,
                    "all_OK": False,
                    "crn": None
                }
                course_offering_data.append(course_offering_item)

    sorted_course_offerings = sorted(course_offering_data, key=lambda item: (
        semester_sorter_dict[item["semester_id"]], item["course"]))

    data = {
        "message": "hello!",
        "course_data": sorted_course_offerings,  # course_offering_data,
        "semester_fractions": semester_fractions,
        "semester_fractions_reverse": semester_fractions_reverse
    }
    return JsonResponse(data)


def construct_instructor_list(course_offering):
    """Constructs a list of instructors for a given (banner or iChair) course offering."""
    return [instr.instructor.first_name+' ' +
            instr.instructor.last_name for instr in course_offering.offering_instructors.all()]


def delta_update_status(bco, ico, delta):
    """Uses a delta object to compare the current status of a banner course offering compared to its corresponding iChair course offering."""
    # at this point it is assumed that the delta object is of the "request that the registrar do an update" variety

    delta_response = {
        "id": delta.id,
        # True if this update is being requested by the user
        "request_update_meeting_times": delta.update_meeting_times,
        # True if this update is being requested by the user
        "request_update_instructors": delta.update_instructors,
        # True if this update is being requested by the user
        "request_update_semester_fraction": delta.update_semester_fraction,
        # True if this update is being requested by the user
        "request_update_max_enrollment": delta.update_max_enrollment,
        "meeting_times": None,
        "instructors": None,
        "semester_fraction": None,
        "max_enrollment": None,
        "messages_exist": False
    }

    # we only check if the meetings agree if the user has requested that a message be generated for this property
    if delta.update_meeting_times and (not scheduled_classes_match(bco, ico)):
        delta_response["meeting_times"] = {
            "was": class_time_and_room_summary(bco.scheduled_classes.all(), include_rooms=False),
            "change_to": class_time_and_room_summary(ico.scheduled_classes.all(), include_rooms=False)
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

    if (delta_response["meeting_times"] is not None) or (delta_response["instructors"] is not None) or (delta_response["semester_fraction"] is not None) or (delta_response["max_enrollment"] is not None):
        delta_response["messages_exist"] = True

    print(delta_response)

    return delta_response


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
        Q(crn__isnull=True) &
        (Q(course__title=bco.course.title) | Q(course__banner_title=bco.course.title)))

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

    print('>>>>>>>>>>>>>>>inside second cut')

    recent_delta_object = None
    chosen_ichair_match = None
    for ichair_match in candidate_ichair_matches:
        delta_objects = DeltaCourseOffering.objects.filter(
            Q(crn=bco.crn) &
            Q(course_offering=ichair_match) &
            Q(requested_action=delta_course_offering_actions["update"]))
        if len(delta_objects) > 0:
            print('delta object(s) found for', ichair_match)
            if recent_delta_object is None:
                recent_delta_object = delta_objects[0]
                chosen_ichair_match = ichair_match
            for delta_object in delta_objects:
                print(delta_object, delta_object.updated_at)
                if delta_object.updated_at > recent_delta_object.updated_at:
                    recent_delta_object = delta_object
                    chosen_ichair_match = ichair_match
                    print('found more recent!',
                          recent_delta_object.updated_at)
    if chosen_ichair_match is not None:
        # we found one, based on looking at the delta(s)
        print(
            '<<<<>>>><<<<>>>>choosing an iChair course offering based on the delta object')
        bco.ichair_id = chosen_ichair_match.id
        bco.save()
        chosen_ichair_match.crn = bco.crn
        chosen_ichair_match.save()
        return None

    # print('inside choose_course_offering_second_cut!')
    # meet above criteria, as well as being a match on meeting days and times
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


def construct_meeting_times_detail(course_offering):
    meeting_times_detail = []
    for sc in course_offering.scheduled_classes.all():
        meeting_times_detail.append({
            "day": sc.day,
            "begin_at": sc.begin_at,
            "end_at": sc.end_at,
            "id": sc.id
        })
    return meeting_times_detail


def scheduled_classes_match(banner_course_offering, ichair_course_offering):
    """Returns true if the scheduled class objects for an iChair course offering exactly match those for the corresponding banner course offering."""
    banner_scheduled_classes = banner_course_offering.scheduled_classes.all()
    ichair_scheduled_classes = ichair_course_offering.scheduled_classes.all()
    classes_match = True
    if len(banner_scheduled_classes) != len(ichair_scheduled_classes):
        classes_match = False
        return classes_match
    for bsc in banner_scheduled_classes:
        # if the # of scheduled classes agree and there is an isc match for each bsc, then the overall schedules agree
        one_fits = False
        for isc in ichair_scheduled_classes:
            if bsc.day == isc.day and bsc.begin_at == isc.begin_at and bsc.end_at == isc.end_at:
                one_fits = True
        if not one_fits:
            classes_match = False
    return classes_match


def instructors_match(banner_course_offering, ichair_course_offering):
    """Returns true if the instructors for an iChair course offering exactly match those for the corresponding banner course offering."""
    banner_instructors = banner_course_offering.offering_instructors.all()
    ichair_instructors = ichair_course_offering.offering_instructors.all()

    inst_match = True
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
        if not one_fits:
            inst_match = False

    # print('instructors match: ', inst_match)
    return inst_match


def semester_fractions_match(banner_course_offering, ichair_course_offering):
    return banner_course_offering.semester_fraction == ichair_course_offering.semester_fraction


def max_enrollments_match(banner_course_offering, ichair_course_offering):
    return banner_course_offering.max_enrollment == ichair_course_offering.max_enrollment


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

    # None if null in the UI code (i.e., if creating a new delta)
    delta_id = json_data['deltaId']

    print(delta_mods)

    print('action: ', action)
    print('crn: ', crn)
    print('ichair id: ', ichair_course_offering_id)
    print('banner id: ', banner_course_offering_id)
    print('semester_id: ', semester_id)
    print('delta id: ', delta_id)

    delta_generation_successful = True

    if delta_id is None:
        print('creating a new delta!')
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

        print(delta_course_offering_actions)

        if delta_generation_successful:
            # https://www.geeksforgeeks.org/python-check-whether-given-key-already-exists-in-a-dictionary/
            if 'meetingTimes' in delta_mods.keys():
                update_meeting_times = delta_mods['meetingTimes']
            else:
                update_meeting_times = False

            if 'instructors' in delta_mods.keys():
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

            dco = DeltaCourseOffering.objects.create(
                course_offering=ico,
                semester=semester,
                crn=crn,
                requested_action=requested_action,
                update_meeting_times=update_meeting_times,
                update_instructors=update_instructors,
                update_semester_fraction=update_semester_fraction,
                update_max_enrollment=update_max_enrollment)
            dco.save()

    else:
        dco = DeltaCourseOffering.objects.get(pk=delta_id)
        print('got delta object!')
        print(dco)
        if 'meetingTimes' in delta_mods.keys():
            dco.update_meeting_times = delta_mods['meetingTimes']

        if 'instructors' in delta_mods.keys():
            dco.update_instructors = delta_mods['instructors']

        if 'semesterFraction' in delta_mods.keys():
            dco.update_semester_fraction = delta_mods['semesterFraction']

        if 'enrollmentCap' in delta_mods.keys():
            dco.update_max_enrollment = delta_mods['enrollmentCap']

        dco.save()

    delta_response = {}
    if delta_generation_successful:
        if action == 'update':
            # in this case we should have both a banner id and an ichair id....
            bco = BannerCourseOffering.objects.get(
                pk=banner_course_offering_id)
            ico = CourseOffering.objects.get(pk=ichair_course_offering_id)
            delta_response = delta_update_status(bco, ico, dco)
            agreement_update = {
                "instructors_match": instructors_match(bco, ico),
                "meeting_times_match": scheduled_classes_match(bco, ico),
                "max_enrollments_match": max_enrollments_match(bco, ico),
                "semester_fractions_match": semester_fractions_match(bco, ico)
            }

        # WORKING HERE: need to add some other functionality for the 'create' and 'delete' actions....

    data = {
        'delta_generation_successful': delta_generation_successful,
        'delta': delta_response,
        'agreement_update': agreement_update
    }

    return JsonResponse(data)


@login_required
@csrf_exempt
def update_class_schedule_api(request):
    """Update the class schedule for a course offering.  Can do any combination of delete, create and update."""
    # user = request.user
    # user_preferences = user.user_preferences.all()[0]

    json_data = json.loads(request.body)

    course_offering_id = json_data['courseOfferingId']
    delete_ids = json_data['delete']
    update_dict = json_data['update']
    create_dict = json_data['create']

    try:
        course_offering = CourseOffering.objects.get(pk=course_offering_id)
    except:
        course_offering = None
        print('could not find the course offering....')

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
            if (begin and end and (day <= 4) and (day >= 0)):
                sc.begin_at = meeting['begin_at']
                sc.end_at = meeting['end_at']
                sc.day = day
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
            if (begin and end and (day <= 4) and (day >= 0)):
                sc = ScheduledClass.objects.create(
                    course_offering=course_offering,
                    day=day,
                    begin_at=meeting['begin_at'],
                    end_at=meeting['end_at'])
                sc.save()
            else:
                creates_successful = False
                print('not able to create new scheduled classes')
    else:
        creates_successful = False

    # now retrieve the scheduled classes from the db again
    if course_offering:
        meeting_times_list, room_list = class_time_and_room_summary(
            course_offering.scheduled_classes.all())
        meeting_times_detail = construct_meeting_times_detail(course_offering)
    else:
        meeting_times_list = []
        meeting_times_detail = []

    data = {
        'updates_successful': updates_successful,
        'creates_successful': creates_successful,
        'deletes_successful': deletes_successful,
        "meeting_times": meeting_times_list,
        "meeting_times_detail": meeting_times_detail
    }

    return JsonResponse(data)


@login_required
@csrf_exempt
def copy_registrar_course_offering_data_to_ichair(request):
    """Create a new course offering or update properties of an existing course offering by copying data from a banner course offering."""
    # user = request.user
    # user_preferences = user.user_preferences.all()[0]

    day_sorter_dict = {
        'M': 0,
        'T': 1,
        'W': 2,
        'R': 3,
        'F': 4
    }

    json_data = json.loads(request.body)

    action = json_data['action']
    # if action == 'create', we are creating a new course offering, in which case all of the properties must be present in course_offering_properties:
    #   - course_id
    #   - semester_id
    #   - ...what to do about instructors?
    #   - load_available
    #   - max_enrollment
    #   - crn (possibly?!?)
    #   - course_offering_id will be None in this case
    # if action == 'update', we are updating an existing course offering, in which case only the 'update' properties will be present in course_offering_properties

    ichair_course_offering_id = json_data['iChairCourseOfferingId']
    banner_course_offering_id = json_data['bannerCourseOfferingId']
    properties_to_update = json_data["propertiesToUpdate"]

    # if there is no banner course offering id, this will be None
    delta_id = json_data['deltaId']
    # if delta is None (i.e., null in the the javascript code), then there is no known delta object for this iChair course offering;
    # if there is a delta object, then we will search for it and be sure to update it as appropriate after making the iChair changes....

    print('banner course offering id: ', banner_course_offering_id)
    print('delta id: ', delta_id)
    print('properties_to_update', properties_to_update)

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
        bco = BannerCourseOffering.objects.get(
            pk=banner_course_offering_id)
        print('ichair course offering: ', ico)
        print('banner course offering: ', bco)
        if 'max_enrollment' in properties_to_update:
            ico.max_enrollment = bco.max_enrollment
            ico.save()
        if 'semester_fraction' in properties_to_update:
            ico.semester_fraction = bco.semester_fraction
            ico.save()
        if 'instructors' in properties_to_update:
            # we take a conservative approach here:
            # - if any of the ichair offering instructors does not have a pidm, leave things alone for that instructor
            ichair_offering_instructors = ico.offering_instructors.all()
            banner_offering_instructors = bco.offering_instructors.all()
            banner_instructor_pidms = [
                boi.instructor.pidm for boi in banner_offering_instructors]

            for ichair_oi in ichair_offering_instructors:
                if (ichair_oi.instructor.pidm is None) or (ichair_oi.instructor.pidm == ''):
                    print(
                        'one of the iChair instructors does not have a pidm...bailing!')
                    offering_instructors_copied_successfully = False
                    break
                elif ichair_oi.instructor.pidm not in banner_instructor_pidms:
                    print('the following iChair instructor is not in the banner list: ',
                          ichair_oi.instructor.first_name, ichair_oi.instructor.last_name)
                    print('...this instructor will be deleted')
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
                        print('now pop out of the banner pidm list....')
                        print('before: ', banner_instructor_pidms)
                        # now pop the matching banner instructor out of the pidm list (https://stackoverflow.com/questions/4915920/how-to-delete-an-item-in-a-list-if-it-exists)
                        while ichair_oi.instructor.pidm in banner_instructor_pidms:
                            banner_instructor_pidms.remove(
                                ichair_oi.instructor.pidm)
                        print('after: ', banner_instructor_pidms)
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
                        # WORKING HERE: assign load in a better way by summing up for the previous instructors and giving the remaining person what's left
                        instructor = ichair_instructors[0]
                        offering_instructor = OfferingInstructor.objects.create(
                            course_offering=ico,
                            instructor=instructor,
                            load_credit=0,
                            is_primary=boi.is_primary)
                        offering_instructor.save()

            # now go through the list of offering instructors again and adjust loads....
            # trying to be careful about rounding and floats....
            if ico.load_difference() > 0.001:
                print('load difference is: ', ico.load_difference())
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
                        print('and now load difference is: ',
                              ico.load_difference())
                        load_manipulation_performed = True

        if 'meeting_times' in properties_to_update:
            # we don't want to unintentionally lose room information, so we can't just delete all existing meeting times and start over....
            banner_scheduled_classes = bco.scheduled_classes.all()

            for ichair_sc in ico.scheduled_classes.all():
                # first, check to see if there is a similar object in the banner list....
                #  - if not, delete the scheduled class from iChair
                #  - if it is found in the banner list, pop the corresponding item out of the banner list
                banner_match = None
                print('ichair meeting time: ', ichair_sc)
                for banner_sc in banner_scheduled_classes:
                    if (ichair_sc.day == banner_sc.day) and (ichair_sc.begin_at == banner_sc.begin_at) and (ichair_sc.end_at == banner_sc.end_at):
                        banner_match = banner_sc
                        print('found a banner match!', banner_match)
                if banner_match is None:
                    print(
                        'no corresponding banner match; deleting iChair meeting time....')
                    # apparently this is OK to do while iterating through the queryset....
                    ichair_sc.delete()
                else:
                    print('popping the banner match out of the list')
                    print('before: ', banner_scheduled_classes)
                    # https://stackoverflow.com/questions/1207406/how-to-remove-items-from-a-list-while-iterating
                    banner_scheduled_classes = [
                        bsc for bsc in banner_scheduled_classes if not banner_match.id == bsc.id]
                    print('after: ', banner_scheduled_classes)

            # now we go through the remaining banner meeting times and copy them over to iChair
            for banner_sc in banner_scheduled_classes:
                classrooms_unassigned = True
                isc = ScheduledClass.objects.create(
                    day=banner_sc.day,
                    begin_at=banner_sc.begin_at,
                    end_at=banner_sc.end_at,
                    course_offering=ico
                )
                isc.save()

        # the following code is copied from above...if we need it again somewhere, should
        # consider putting this all in a function
        presorted_ico_meeting_times_list = class_time_and_room_summary(
            ico.scheduled_classes.all(), include_rooms=False)
        ico_meeting_times_list = sorted(
            presorted_ico_meeting_times_list, key=lambda item: (day_sorter_dict[item[:1]]))
        ico_instructors = construct_instructor_list(ico)
        meeting_times_detail = construct_meeting_times_detail(ico)

        if delta_id is not None:
            dco = DeltaCourseOffering.objects.get(pk=delta_id)
            print('delta course offering: ', dco)
            delta_response = delta_update_status(bco, ico, dco)

            schedules_match = scheduled_classes_match(
                bco, ico) or delta_response["request_update_meeting_times"]
            inst_match = instructors_match(
                bco, ico) or delta_response["request_update_instructors"]
            sem_fractions_match = semester_fractions_match(
                bco, ico) or delta_response["request_update_semester_fraction"]
            enrollment_caps_match = max_enrollments_match(
                bco, ico) or delta_response["request_update_max_enrollment"]
        else:
            schedules_match = scheduled_classes_match(bco, ico)
            inst_match = instructors_match(bco, ico)
            sem_fractions_match = semester_fractions_match(
                bco, ico)
            enrollment_caps_match = max_enrollments_match(bco, ico)

        agreement_update = {
            "instructors_match": inst_match,
            "meeting_times_match": schedules_match,
            "max_enrollments_match": enrollment_caps_match,
            "semester_fractions_match": sem_fractions_match
        }

        course_offering_update = {
            "course_offering_id": ico.id,
            "meeting_times": ico_meeting_times_list,
            "meeting_times_detail": meeting_times_detail,
            # "rooms": ico_room_list,
            "instructors": ico_instructors,
            "semester": ico.semester.name.name,
            "semester_fraction": int(ico.semester_fraction),
            "max_enrollment": int(ico.max_enrollment)}

        # except:
        #    ico = None
        #    print('could not find the course offering....')

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
