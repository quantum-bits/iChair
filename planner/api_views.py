from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from .models import *

from django.shortcuts import render

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@login_required
def banner_comparison_data(request):
    data = {
        "message": "hello!"
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

