from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from .models import *
from .helper_functions import *

from django.shortcuts import render

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import re

@login_required
def banner_comparison_data(request):

    department_id = request.GET.get('departmentId')
    year_id = request.GET.get('yearId')

    semester_fractions = {
        'full': CourseOffering.FULL_SEMESTER,
        'first_half': CourseOffering.FIRST_HALF_SEMESTER,
        'second_half': CourseOffering.SECOND_HALF_SEMESTER
    }

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
        "course_data": course_data,
        "semester_fractions": semester_fractions
    }
    return JsonResponse(data)

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

