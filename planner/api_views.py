from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from .models import *
from .helper_functions import *

from django.shortcuts import render

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@login_required
def banner_comparison_data(request):

    department_id = request.GET.get('departmentId')
    year_id = request.GET.get('yearId')
    print('dept: ', department_id)
    print('year: ', year_id)

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
        course_data.append({
            "semester": 'Fall',
            "course_id": co1.course.id,
            "course": co1.course.subject.abbrev+' '+co1.course.number,
            "course_title": co1.course.title,
            "banner": { 
                "course_offering_id": co1.id,
                "meeting_times": co1meeting_times_list,
                "rooms": co1room_list,
                "instructors": instructors1
            },
            "ichair": { 
                "course_offering_id": co2.id,
                "meeting_times": co2meeting_times_list,
                "rooms": co2room_list,
                "instructors": instructors2
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
                "instructors": instructors
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
    course_data.append({
        "semester": 'Spring',
        "course_id": co.course.id,
        "course": co.course.subject.abbrev+' '+co.course.number,
        "course_title": co.course.title,
        "ichair": { 
                "course_offering_id": co.id,
                "meeting_times": meeting_times_list,
                "rooms": room_list,
                "instructors": instructors
            },
        "banner": None,
        "has_banner": False,
        "has_ichair": True,
        "linked": False,
        "delta": None,
        "needs_work": True,
        "crn": None
    })

    print(course_data)

    data = {
        "message": "hello!",
        "course_data": course_data
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

