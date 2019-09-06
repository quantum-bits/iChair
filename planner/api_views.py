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
    academic_year = AcademicYear.objects.get(pk = year_id)
    department = Department.objects.get(pk = department_id)

    unmatched_courses = []
    for subject in department.subjects.all():
        print(subject, subject.abbrev)
        #print(BannerCourse.objects.all
        for banner_course in BannerCourse.objects.filter(subject__abbrev = subject.abbrev):
            ichair_courses = Course.objects.filter(
                Q(subject__abbrev = banner_course.subject.abbrev)&
                Q(number__startswith = banner_course.number)&
                Q(credit_hours = banner_course.credit_hours))
            
            exact_match = False
            multiple_potential_matches = False

            for ichair_course in ichair_courses:
                if (banner_course.title == ichair_course.title) or (banner_course.title == ichair_course.banner_title): # found a match...
                    if (exact_match == True) and (multiple_potential_matches == False): # uh-oh...we had already found a match -- this means we have more than one potential match, so we will list them all
                        exact_match = False
                        multiple_potential_matches = True
                    elif (exact_match == False) and (multiple_potential_matches == False):
                        exact_match = True

            if exact_match == False:
                ichair_course_data = [ # all the candidate iChair courses
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

    json_data=json.loads(request.body)
    update_dict = json_data['update']
    create_dict = json_data['create']

    print('update: ', update_dict)
    print('create: ', create_dict)

    creates_successful = True
    updates_successful = True
    print('updating....')
    for update_item in update_dict:
        print(update_item)
        #course = Course.objects.get(pk = update_item.ichair_course_id)
        try:
            course = Course.objects.get(pk = update_item["ichair_course_id"])
            print(course)
            course.banner_title = update_item["banner_title"]
            course.save()
        except:
            creates_successful = False

    print('creating...')
    for create_item in create_dict:
        print(create_item)
        try:
            subject = Subject.objects.get(pk = create_item["subject_id"])
            print(subject)
            course = Course.objects.create(
                title = create_item["title"],
                credit_hours = create_item["credit_hours"],
                subject = subject,
                number = create_item["number"])
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

    json_data=json.loads(request.body)
    department_id = json_data['departmentId']
    year_id = json_data['yearId']
    semester_ids = json_data['semesterIds']



    print('dept id: ', department_id)
    print('year id: ', year_id)
    print('semester ids:', semester_ids)

    department = Department.objects.get(pk = department_id)
    #academic_year = AcademicYear.objects.get(pk = year_id)

    semester_fractions = {
        'full': CourseOffering.FULL_SEMESTER,
        'first_half': CourseOffering.FIRST_HALF_SEMESTER,
        'second_half': CourseOffering.SECOND_HALF_SEMESTER
    }

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
        semester = Semester.objects.get(pk = semester_id)
        term_code = semester.banner_code
        for subject in department.subjects.all(): # eventually expand this to include extra-departmental courses taught by dept...?
            # first should reset all crns of the iChair course offerings, so we start with a clean slate
            # should also reset all ichair_ids for the Banner course offerings, for the same reason (that's done below)

            # RESET CRNs of all corresponding iChair course offerings (i.e., start from scratch)
            for course_offering in CourseOffering.objects.filter(
                    Q(semester = semester)&
                    Q(course__subject = subject)):
                course_offering.crn = None
                course_offering.save()

            banner_course_offerings = BannerCourseOffering.objects.filter(Q(course__subject__abbrev = subject.abbrev)&Q(term_code = term_code))

            # the following is an initial round of attempting to link up banner courses with iChair courses
            # once this is done, we can cycle through the linked courses (which should be 1-to-1 at that point) and add them to a list
            # then we can cycle through any unlinked courses on both sides and add them to the list
            # then we should sort the list so the order doesn't seem crazy

            for bco in banner_course_offerings:
                # attempt to assign an iChair course offering to the banner one
                find_ichair_course_offering(bco, semester, subject)
            
            # once all of the course offerings have been cycled through, we have done as much matching as possible between iChair and banner courses for this subject and semester
            # now we can go again, and simply pick out the ones that have been matched, etc.

            for bco in banner_course_offerings:

                bco_meeting_times_list = class_time_and_room_summary(bco.scheduled_classes.all(), include_rooms = False)
                bco_instructors = [instr.instructor.first_name+' '+instr.instructor.last_name for instr in bco.offering_instructors.all()]

                if bco.is_linked:
                    # get the corresponding iChair course offering
                    try:
                        ico = CourseOffering.objects.get(pk = bco.ichair_id)
                        ico_meeting_times_list, ico_room_list = class_time_and_room_summary(ico.scheduled_classes.all())
                        ico_instructors = [instr.instructor.first_name+' '+instr.instructor.last_name for instr in ico.offering_instructors.all()]
                        meeting_times_detail = construct_meeting_times_detail(ico)

                        schedules_match = scheduled_classes_match(bco, ico)
                        inst_match = instructors_match(bco, ico)
                        sem_fractions_match = semester_fractions_match(bco, ico)

                        #######
                        # now use the functions already defined to say whether various properties agree or not!
                        # EASY!!!!!
                        #######
                        course_offering_data.append({
                            "semester": semester.name.name,
                            "course_id": ico.course.id,
                            "course": ico.course.subject.abbrev+' '+ico.course.number,
                            "course_title": ico.course.title,
                            "schedules_match": schedules_match,
                            "instructors_match": inst_match,
                            "semester_fractions_match": sem_fractions_match,
                            "banner": { 
                                "course_offering_id": bco.id,
                                "meeting_times": bco_meeting_times_list,
                                "rooms": [],
                                "instructors": bco_instructors,
                                "term_code": bco.term_code,
                                "semester_fraction": bco.semester_fraction
                            },
                            "ichair": { 
                                "course_offering_id": ico.id,
                                "meeting_times": ico_meeting_times_list,
                                "meeting_times_detail": meeting_times_detail,
                                "rooms": ico_room_list,
                                "instructors": ico_instructors,
                                "semester": ico.semester.name.name,
                                "semester_fraction": ico.semester_fraction
                            },
                            "has_banner": True,
                            "has_ichair": True,
                            "linked": True,
                            "delta": None,
                            "all_OK": schedules_match and inst_match and sem_fractions_match,
                            "crn": bco.crn
                        })
                    except CourseOffering.DoesNotExist:
                        print('OOPS!  Looking for a course offering that does not exist....')
                        print(bco)


        




    courses = [
        Course.objects.filter(title='Modern Physics')[0],
        Course.objects.filter(title='University Physics II')[0],
        Course.objects.filter(title='Engineering Thermodynamics')[0],
        Course.objects.filter(title='Analytical Mechanics')[0]
    ]
    
    course_data = []
    for course in courses:
        num_offerings = len(course.offerings.all())
        
        co1 = course.offerings.all()[num_offerings-1]
        co2 = course.offerings.all()[num_offerings-2]
        co1meeting_times_list, co1room_list = class_time_and_room_summary(co1.scheduled_classes.all())
        co2meeting_times_list, co2room_list = class_time_and_room_summary(co2.scheduled_classes.all())
        instructors1 = [instr.instructor.first_name+' '+instr.instructor.last_name for instr in co1.offering_instructors.all()]
        instructors2 = [instr.instructor.first_name+' '+instr.instructor.last_name for instr in co2.offering_instructors.all()]
        meeting_times_detail = construct_meeting_times_detail(co2)
        
        course_data.append({
            "semester": 'Fall',
            "course_id": co1.course.id,
            "course": co1.course.subject.abbrev+' '+co1.course.number,
            "course_title": co1.course.title,
            "banner": { 
                "course_offering_id": co1.id,
                "meeting_times": co1meeting_times_list,
                "rooms": co1room_list,
                "instructors": instructors1,
                "semester": co1.semester.name.name,
                "semester_fraction": co1.semester_fraction
            },
            "ichair": { 
                "course_offering_id": co2.id,
                "meeting_times": co2meeting_times_list,
                "meeting_times_detail": meeting_times_detail,
                "rooms": co2room_list,
                "instructors": instructors2,
                "semester": co2.semester.name.name,
                "semester_fraction": co2.semester_fraction
            },
            "has_banner": True,
            "has_ichair": True,
            "linked": True,
            "delta": None,
            "needs_work": True,
            "crn": '12354'
        })

    course = Course.objects.filter(title='Quantum Mechanics I')[0]
    num_offerings = len(course.offerings.all())
    co = course.offerings.all()[num_offerings-1]
    meeting_times_list, room_list = class_time_and_room_summary(co1.scheduled_classes.all())
    instructors = [instr.instructor.first_name+' '+instr.instructor.last_name for instr in co.offering_instructors.all()]
    course_data.append({
        "semester": "J-term",
        "course_id": co.course.id,
        "course": co.course.subject.abbrev+' '+co.course.number,
        "course_title": co.course.title,
        "banner": { 
                "course_offering_id": co.id,
                "meeting_times": meeting_times_list,
                "rooms": room_list,
                "instructors": instructors,
                "semester": co.semester.name.name,
                "semester_fraction": co.semester_fraction
            },
        "ichair": None,
        "has_banner": True,
        "has_ichair": False,
        "linked": False,
        "delta": None,
        "needs_work": False,
        "crn": '52846'
    })

    course = Course.objects.filter(title='Quantum Mechanics II - SP')[0]
    num_offerings = len(course.offerings.all())
    co = course.offerings.all()[num_offerings-1]
    meeting_times_list, room_list = class_time_and_room_summary(co1.scheduled_classes.all())
    instructors = [instr.instructor.first_name+' '+instr.instructor.last_name for instr in co.offering_instructors.all()]
    meeting_times_detail = construct_meeting_times_detail(co)
   
    course_data.append({
        "semester": 'Spring',
        "course_id": co.course.id,
        "course": co.course.subject.abbrev+' '+co.course.number,
        "course_title": co.course.title,
        "ichair": { 
                "course_offering_id": co.id,
                "meeting_times": meeting_times_list,
                 "meeting_times_detail": meeting_times_detail,
                "rooms": room_list,
                "instructors": instructors,
                "semester": co.semester.name.name,
                "semester_fraction": co.semester_fraction
            },
        "banner": None,
        "has_banner": False,
        "has_ichair": True,
        "linked": False,
        "delta": None,
        "needs_work": True,
        "crn": None
    })

    data = {
        "message": "hello!",
        "course_data": course_offering_data,
        "semester_fractions": semester_fractions
    }
    return JsonResponse(data)

def find_ichair_course_offering(bco, semester, subject):
    """Start the process of linking up this banner course offering (bco) with one in iChair."""

    # start by unlinking the banner course offering
    bco.ichair_id = None
    bco.save()

    # search for candidate course offerings
    # https://stackoverflow.com/questions/844556/filtering-for-empty-or-null-names-in-a-queryset
    candidate_ichair_matches = CourseOffering.objects.filter(
        Q(semester = semester)&
        Q(course__subject = subject)&
        Q(course__number__startswith = bco.course.number)&
        Q(course__credit_hours = bco.course.credit_hours)&
        Q(crn__isnull=True)&
        (Q(course__title = bco.course.title)|Q(course__banner_title = bco.course.title)))

    if len(candidate_ichair_matches) == 1:
        ichair_course_offering = candidate_ichair_matches[0]
        # if only one potential match at this stage, link the banner course to the ichair one
        bco.ichair_id = ichair_course_offering.id
        bco.save()
        ichair_course_offering.crn = bco.crn
        ichair_course_offering.save()
        #print('>>> Exactly one candidate match...banner course offering is now linked to corresponding iChair course offering!')
        #print('>>> scheduled classes agree: ', scheduled_classes_match(bco, ichair_course_offering))
    elif len(candidate_ichair_matches) > 1:
        print('<<< More than one candidate match...checking to see if meeting times match for any of them')
        choose_course_offering_second_cut(bco, candidate_ichair_matches)

    return None

def choose_course_offering_second_cut(bco, candidate_ichair_matches):
    """Check candidate iChair course matches for this banner course offering, and possibly choose one based on agreement of weekly schedules."""
    # at this point we have several candidate matches...which one is closest?
    
    #print('inside choose_course_offering_second_cut!')
    second_cut_ichair_matches = [] # meet above criteria, as well as being a match on meeting days and times
    for ichair_match in candidate_ichair_matches:
        #print(ichair_match)
        #print('banner_title of iChair course:', ichair_match.course.banner_title)
        if scheduled_classes_match(bco, ichair_match):
            second_cut_ichair_matches.append(ichair_match)
    
    if len(second_cut_ichair_matches) == 1:
        ichair_course_offering = second_cut_ichair_matches[0]
        # if only one potential match at this stage, link the banner course to the ichair one
        bco.ichair_id = ichair_course_offering.id
        bco.save()
        ichair_course_offering.crn = bco.crn
        ichair_course_offering.save()
        #print('>>><<<>>> Exactly one candidate match...banner course offering is now linked to corresponding iChair course offering!')
    elif len(second_cut_ichair_matches) > 1:
        # at this point, see if the instructors are an exact match...
        choose_course_offering_third_cut(bco, second_cut_ichair_matches)
       
    return None

def choose_course_offering_third_cut(bco, second_cut_ichair_matches):
    """
    Check candidate iChair course matches for this banner course offering, and possibly choose one based on faculty members.
    By this point, the weekly schedules are an exact match, but there are too many course offerings that are an exact match in this respect.
    """
    print('inside 3rd cut!  Checking instructors now....')

    third_cut_ichair_matches = [] # meet above criteria, as well as being a match on meeting days and times
    for ichair_match in second_cut_ichair_matches:
        #print(ichair_match)
        if instructors_match(bco, ichair_match):
            #print('instructors match exactly!')
            third_cut_ichair_matches.append(ichair_match)
    
    if len(third_cut_ichair_matches) == 0:
        # see if semester fraction helps to sort things out....
        print('instructors do not match exactly, going to check semester fractions instead!')
        choose_course_offering_fourth_cut(bco, second_cut_ichair_matches)

    if len(third_cut_ichair_matches) == 1:
        ichair_course_offering = third_cut_ichair_matches[0]
        # if only one potential match at this stage, link the banner course to the ichair one
        bco.ichair_id = ichair_course_offering.id
        bco.save()
        ichair_course_offering.crn = bco.crn
        ichair_course_offering.save()
        print('>>><<<>>> Exactly one candidate match for instructors...banner course offering is now linked to corresponding iChair course offering!')

    else:
        # at this point, check semester_fractions(!)
        print('~~~~~~~~~~~~')
        print('<<<there are several instructors that match...checking semester fractions')
        print('~~~~~~~~~~~~')
        choose_course_offering_fourth_cut(bco, third_cut_ichair_matches)

    return None

def choose_course_offering_fourth_cut(bco, third_cut_ichair_matches):
    """Check candidate iChair course matches for this banner course offering, and possibly choose one based on semester fraction."""
    print('inside 4th cut!  Checking semester fractions now....')

    fourth_cut_ichair_matches = [] 
    for ichair_match in third_cut_ichair_matches:
        print(ichair_match)
        if semester_fractions_match(bco, ichair_match):
            print('semester fractions match exactly!')
            fourth_cut_ichair_matches.append(ichair_match)
    
    if len(fourth_cut_ichair_matches) == 1:
        ichair_course_offering = fourth_cut_ichair_matches[0]
        # if only one potential match at this stage, link the banner course to the ichair one
        bco.ichair_id = ichair_course_offering.id
        bco.save()
        ichair_course_offering.crn = bco.crn
        ichair_course_offering.save()
        print('>>><<<>>> Exactly one candidate match for semester fractions...banner course offering is now linked to corresponding iChair course offering!')

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

    print('banner instructors: ')
    for bi in banner_instructors:
        print(bi.instructor, bi.instructor.pidm)
    
    print('ichair instructors: ')
    for ii in ichair_instructors:
        print(ii.instructor, ii.instructor.pidm)

    inst_match = True
    if len(banner_instructors) != len(ichair_instructors):
        inst_match = False
        print('instructors match: ', inst_match)
        return inst_match
    for banner_instructor in banner_instructors:
        print('banner instructor: ', banner_instructor.instructor)
        # if the # of instructors agree and there is an iChair instructor match for each banner instructor, then the overall set of instructors agrees
        one_fits = False
        for ichair_instructor in ichair_instructors:
            if banner_instructor.instructor.pidm == ichair_instructor.instructor.pidm:
                print('ichair instructor: ', ichair_instructor.instructor)
                one_fits = True
        if not one_fits:
            inst_match = False

    print('instructors match: ', inst_match)
    return inst_match

def semester_fractions_match(banner_course_offering, ichair_course_offering):
    return banner_course_offering.semester_fraction == ichair_course_offering.semester_fraction

@login_required
@csrf_exempt
def update_class_schedule_api(request):
    """Update the class schedule for a course offering.  Can do any combination of delete, create and update."""
    #user = request.user
    #user_preferences = user.user_preferences.all()[0]

    json_data=json.loads(request.body)
    
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
            print('unable to delete scheduled class id = ', delete_id,'; it may be that the object no longer exists.')
            deletes_successful = False

    # define a regular expression to use for matching times....
    # https://docs.python.org/3/howto/regex.html#matching-characters
    p = re.compile('([0-1]?[0-9]|2[0-3]):([0-5][0-9])(:[0-5][0-9])?')

    # updates first....
    updates_successful = True
    for meeting in update_dict:
        try:
            sc = ScheduledClass.objects.get(pk=meeting['id'])
            begin = p.match(meeting['begin_at']) # if begin_at or end_at does not match, begin or end evaluates to None
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
            begin = p.match(meeting['begin_at']) # if begin_at or end_at does not match, begin or end evaluates to None
            end = p.match(meeting['end_at'])
            day = int(meeting['day'])
            if (begin and end and (day <= 4) and (day >= 0)):
                sc = ScheduledClass.objects.create(
                        course_offering = course_offering,
                        day = day,
                        begin_at = meeting['begin_at'],
                        end_at = meeting['end_at'])
                sc.save()
            else:
                creates_successful = False
                print('not able to create new scheduled classes')
    else:
        creates_successful = False

    # now retrieve the scheduled classes from the db again
    if course_offering:
        meeting_times_list, room_list = class_time_and_room_summary(course_offering.scheduled_classes.all())
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
def update_view_list(request):
    """Add a faculty member to the list of faculty to view; used for AJAX requests."""
    user = request.user
    user_preferences = user.user_preferences.all()[0]
    faculty_id = request.POST.get('facultyId')
    
    try:
        faculty = FacultyMember.objects.get(pk = faculty_id)
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
    courses = Course.objects.filter(subject__id = subject_id).order_by('number')
    return render(request, 'course_dropdown_list_options.html', {'courses': courses})

