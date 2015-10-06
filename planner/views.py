from collections import namedtuple

from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.forms.models import inlineformset_factory
from django.shortcuts import render, redirect
from django.template import RequestContext
from django.utils import simplejson
from django.utils.functional import curry

from .models import *
from .forms import *

import json
import csv
from django.http import HttpResponse, HttpResponseRedirect
import xlwt
from os.path import expanduser
from datetime import date

from reportlab.pdfgen import canvas

import cStringIO as StringIO
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from cgi import escape


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    context = Context(context_dict)
    html  = template.render(context)
    result = StringIO.StringIO()

    pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))



# TO DO:

# Idea from Art White: State total # of hours being taught on the fac ld summary
# Another idea from Art: Make columns hide-able in faculty load summary page; need some way to indicate
#                        which columns are hidden, though...!
# !!! add something to the Faculty Load Summary page that checks
#     if there are faculty members who are receiving load, but who are
#     not being displayed; if so, put a warning of some sort on the faculty
#     load page !!!
# !!! shorten the KSAC names for rooms (too long to fit on room selector
#     widget !!!
# WHY is Chrome giving the "resize window" message when you first log in?!?
# maybe the variable should be set to null/false right away upon login or something?  maybe there's some junk there and it's triggering on that.

# 0. OOPS! ids (for html elements) are not supposed to start with #'s; should
#    fix this, so my code does not get deprecated too quickly!  ACTUALLY: it 
#    appears that it's OK on the html side, but CSS says that the ids need to 
#    start with a letter.  Still, might be safest to fix it!
# 1. update help topics
# 2. (somewhat optional): remove the ?next= stuff where it's not being used anyways

# THINGS TO ADD EVENTUALLY(?):
# 1. CRNs for course offerings
# 2. office hours
# 3. department meetings
# 4. other types of meetings?
# 5. should meetings have rooms associated with them?
# 6. meetings should probably have a comments field; possibly a drop-down
#    with "type" (dept, school, faculty, other); comments field could be
#    something like (every other week; etc.)
# 7. meetings need to have a semester field, too.
# 8. maybe something on preferences about whether office hours/mtgs should show
#    up in schedules?!?
# 9. >>> IF OFFICE HOURS ARE ADDED...add a "custom" schedule thing that would
#        merge together the schedules for ANY faculty member so that that could
#        be used by Barb/Lara for scheduling meetings
#
# maybe there could be one object, which is something like Commitment;
# its fields could be:
# - faculty member
# - start_at, end_at, day
# - room (optional)
# - type (office hour; dept mtg; school mtg; dept chair mtg; faculty mtg; (generic) mtg)
# - comment box
# - some of those other things could be objects in the db, too (dept mtg, etc.),
#   they could be associated with depts...then they could be a bit more
#   automatic, etc.  That's probably going a bit overboard.

#---------

# to prevent accidental resubmission of a form after using the back button:
# http://stackoverflow.com/questions/15671335/prevent-multiple-form-submissions-in-django
# ...actually, maybe use HTTPResponseRedirect (?)
# search on django prevent resubmit form back button

# there is generally an issue with these forms if you use the "back"
# button and then submit again; it makes a second copy!!!
#  -> I added an "alert" at the beginning of the "form" submission process.

# when trying to do a search on the admin, courseoffering page, it gives an error!

# NOTE: changed .page-name in bootstrap.css to have width: 51% (instead of 61%)...might want to change that back

ALL_FACULTY_DIV_ID = 100001
UNDERASSIGNED_LOAD_DIV_ID = 100002


@login_required
def home(request):
    close_all_divs(request)
    return render(request, 'home.html')

@login_required
def profile(request):
    close_all_divs(request)
    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]

    # Note: to access the email address in the view, you could set it to
    # email = student.user.email

    room_list = []
    for room in user_preferences.rooms_to_view.all():
        room_name = room.building.abbrev+' '+room.number
        room_list.append(room_name)

    faculty_list = []
    for faculty in user_preferences.faculty_to_view.all():
        faculty_list.append(faculty.first_name+' '+faculty.last_name)

    other_load_types = []
    for load in user_preferences.other_load_types_to_view.all():
        other_load_types.append(load)

    context = { 'department': user_preferences.department_to_view,
                'academic_year': user_preferences.academic_year_to_view,
                'permission_level': user_preferences.permission_level,
                'room_list': room_list,
                'other_load_types': other_load_types,
                'faculty_list': faculty_list,
                'id': user_preferences.id,
                'username': user.username
                }
    return render(request, 'profile.html', context)





def generate_pdf(request):
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="somefilename.pdf"'

    # Create the PDF object, using the response object as its "file."
    p = canvas.Canvas(response)

    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    p.drawString(100, 100, "Hello world.")

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    return response


@login_required
def display_notes(request):
    close_all_divs(request)
    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view.begin_on.year
    academic_year_string = str(academic_year)+'-'+str(academic_year+1)

    temp_data = Note.objects.all().filter(Q(department__abbrev=department.abbrev)&Q(year__begin_on__year=academic_year))

    can_edit = False
    if user_preferences.permission_level == 1:
        can_edit = True
        

#    print temp_data

    datablock = []
    ii = 0
    for adv_notes in temp_data:
        ii = ii + 1
        datablock.append([adv_notes.updated_at, adv_notes.note, adv_notes.id, ii])

#    print datablock

    context = {
        'department': department,
        'datablock': datablock,
        'can_edit': can_edit,
        'year': academic_year_string,
        'id': user_preferences.id,
        }
    return render(request, 'notes.html', context)


@login_required
def add_new_note(request):
    # The following list should just have one element(!)...hence "listofstudents[0]" is
    # used in the following....

    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view

    if request.method == 'POST':
        form = AddNoteForm(request.POST)
        if form.is_valid():
            p1 = Note.objects.create(department=department,
                                     year=academic_year
                                     )
            p1.note = form.cleaned_data['note']
            p1.save()
            return redirect('display_notes')
        else:
            return render(request, 'addNote.html', {'form': form})
    else:
        # user is not submitting the form; show them the blank add semester form
        form = AddNoteForm()
        context = {'form': form}
        return render(request, 'addNote.html', context)


@login_required
def update_note(request, id):

    instance = Note.objects.get(pk = id)
#    print instance.note
#    print instance.department
#    print instance.year

    if request.method == 'POST':
        form = AddNoteForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('display_notes')
        else:
            return render(request, 'addNote.html', {'form': form})
    else:
        form = AddNoteForm(instance=instance)
        context = {'form': form}
        return render(request, 'addNote.html', context)

@login_required
def delete_note(request, id):
    instance = Note.objects.get(pk = id)

    instance.delete()
    return redirect('display_notes')

@login_required
def department_load_summary(request):
    """Display loads for professors in the department"""
    request.session["return_to_page"] = "/planner/deptloadsummary/"

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]

    context = collect_data_for_summary(request)
    context['all_faculty_div_id']=ALL_FACULTY_DIV_ID
    context['underassigned_load_div_id']=UNDERASSIGNED_LOAD_DIV_ID
    json_open_div_id_list = construct_json_open_div_id_list(request)
    context['open_div_id_list']=json_open_div_id_list
    context['num_faculty']=simplejson.dumps(len(user_preferences.faculty_to_view.all()))
    return render(request, 'dept_load_summary.html', context)

def collect_data_for_summary(request):
    """Collects the data to be displayed in the dept load summary"""
    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view
    academic_year_object = user_preferences.academic_year_to_view
    academic_year = user_preferences.academic_year_to_view.begin_on.year
    academic_year_string = str(academic_year)+'-'+str(academic_year+1)
    can_edit = False
    if user_preferences.permission_level == 1:
        can_edit = True


#
# NOTE:
# 1.  Summer has been deleted from the load schedule.  If there is any load for summer,
#     it is added to the fall.  This is HARDCODED (yech!)  Also, the indexing in the array
#     assumes that Fall will be "0", etc., and this is tied to "seq" in the database.  UGLY!!!
#

    ii = 0
    load_list_initial=[]
    instructordict=dict()
    instructor_id_list=[]
    instructor_name_list=[]
    instructor_name_dict=dict()
    instructor_integer_list=[]
    faculty_to_view = user_preferences.faculty_to_view.filter(department=department)
    for faculty in faculty_to_view:
        instructordict[faculty.id] = ii
        instructor_name_list.append(faculty.first_name[0]+'. '+faculty.last_name)
        instructor_name_dict[faculty.id] = faculty.first_name[0]+'. '+faculty.last_name
        instructor_id_list.append(faculty.id)
        instructor_integer_list.append(ii)
        ii=ii+1

    number_faculty=ii
# the following assumes that semesters are returned in the order Summer, Fall, J-term, Spring, so that
# Fall ends up being 0, J-term is 1 and Spring is 2.
    ii = -1
    semesterdict=dict()
    for semester in SemesterName.objects.all():
        semesterdict[semester.name] = ii
        ii=ii+1

#
# load for summer is added to the fall....
#
    semesterdict[u'Summer']=0

    data_list = []
    unassigned_overassigned_data_list = []

    number_semesters = 4

    faculty_summary_load_list = []
    for ii in range(number_faculty):
        faculty_summary_load_list.append([0,0,0])

    course_offerings = CourseOffering.objects.filter(
        Q(course__subject__department=department)&
        Q(semester__year=academic_year_object)).select_related(
            'semester__name__name',
            'semester__year__begin_on__year',
            'course__subject')

    scheduled_classes = ScheduledClass.objects.filter(
        Q(course_offering__course__subject__department=department)&
        Q(course_offering__semester__year=academic_year_object)).select_related(
            'room__building',
            'course_offering__semester__name__name',
            'course_offering__semester__year__begin_on__year',
            'course_offering__course__subject')


    offering_instructors = OfferingInstructor.objects.filter(
        Q(course_offering__course__subject__department=department)&
        Q(course_offering__semester__year=academic_year_object)).select_related(
            'course_offering',
            'instructor__last_name',
            'instructor__first_name')
        
    course_offering_dict = dict()
    
    for course_offering in course_offerings:
        course_offering_dict[course_offering.id] = {
            'course_offering': course_offering,
            'scheduled_classes': [],
            'offering_instructors': []
            }

    for scheduled_class in scheduled_classes:
        co_id = scheduled_class.course_offering.id
        course_offering_dict[co_id]['scheduled_classes'].append(scheduled_class)

    for offering_instructor in offering_instructors:
        co_id = offering_instructor.course_offering.id
        course_offering_dict[co_id]['offering_instructors'].append(offering_instructor)

    for key in course_offering_dict:
        semester_name = course_offering_dict[key]['course_offering'].semester.name.name
        classes = course_offering_dict[key]['scheduled_classes']
        if not classes:
            meetings_scheduled = False
            meeting_times_list = ["---"]
            room_list = ["---"]
        else:
            meetings_scheduled = True
            meeting_times_list, room_list = class_time_and_room_summary(classes)
            
        number = u"{0} {1}".format(course_offering_dict[key]['course_offering'].course.subject,
                                   course_offering_dict[key]['course_offering'].course.number)
        course_name = course_offering_dict[key]['course_offering'].course.title
        available_load_hours = course_offering_dict[key]['course_offering'].load_available

        if abs(round(available_load_hours)-available_load_hours)<0.01:
            # if the load is close to an int, round it, then int it (adding 0.01 to be on the safe side)
            available_load_hours = int(round(available_load_hours)+0.01)

        load_list = []
        load_assigned = 0
        for ii in range(number_faculty):
            load_list.append([-1,0])

        instructor_list = []  
        for instructor in course_offering_dict[key]['offering_instructors']:
            load_assigned+=instructor.load_credit

            instructor_list.append(instructor.instructor.first_name[:1]+' '+instructor.instructor.last_name+
                                   ' ['+str(load_hour_rounder(instructor.load_credit))+'/'
                                   +str(load_hour_rounder(available_load_hours))+']'
            )
            
            if instructor.instructor in faculty_to_view:
                instructor_load = load_hour_rounder(instructor.load_credit)
                instructor_id = instructor.instructor.id
                ii = instructordict[instructor_id]
                jj = semesterdict[semester_name]
                load_list[ii][0] = instructor_load
                load_list[ii][1] = jj
                faculty_summary_load_list[ii][jj] = faculty_summary_load_list[ii][jj]+instructor_load

        if len(instructor_list)==0:
            instructor_list = ['TBA']
            
        load_diff = load_hour_rounder(course_offering_dict[key]['course_offering'].load_available - load_assigned)

        data_list.append({'number':number,
                          'name':course_name,
                          'rooms':room_list,
                          'load_hours': available_load_hours,
                          'load_difference': load_diff,
                          'load_hour_list': load_list,
                          'instructor_list': instructor_list,
                          'course_id':course_offering_dict[key]['course_offering'].course.id,
                          'id':course_offering_dict[key]['course_offering'].id,
                          'comment':course_offering_dict[key]['course_offering'].comment,
                          'semester':semester_name,
                          'meeting_times':meeting_times_list,
                          'meetings_scheduled':meetings_scheduled
        })
        if ((meetings_scheduled == False) or (load_diff != 0)):
            unassigned_overassigned_data_list.append({
                'number':number,
                'name':course_name,
                'rooms':room_list,
                'load_hours': available_load_hours,
                'load_difference': load_diff,
                'load_hour_list': load_list,
                'instructor_list': instructor_list,
                'course_id':course_offering_dict[key]['course_offering'].course.id,
                'id':course_offering_dict[key]['course_offering'].id,
                'comment':course_offering_dict[key]['course_offering'].comment,
                'semester':semester_name,
                'meeting_times':meeting_times_list,
                'meetings_scheduled':meetings_scheduled
            })

    data_list_unsorted = data_list
    data_list = sorted(data_list_unsorted, key=lambda row: row['number'])

    unsorted_list = unassigned_overassigned_data_list
    unassigned_overassigned_data_list = sorted(unsorted_list, key=lambda row: row['number'])
    
    admin_data_list=[]
    unassigned_admin_data_list=[]

    other_load_types = user_preferences.other_load_types_to_view.all()
    other_loads = OtherLoad.objects.filter(
        Q(semester__year=academic_year_object)&
        Q(instructor__department=department)).select_related(
            'load_type',
            'instructor__last_name',
            'instructor__first_name',
            'semester__name__name')

    other_load_type_dict = dict()
    for other_load_type in other_load_types:
        other_load_type_dict[other_load_type.id] = {
            'load_type': other_load_type,
            'loads': []
        }

    for load in other_loads:
        if (load.load_type in other_load_types) and (load.instructor in faculty_to_view):
            other_load_type_dict[load.load_type.id]['loads'].append(load)
    
#    assert False
    for key in other_load_type_dict:
        load_list = []
        total_other_load=0
        for ii in range(number_faculty):
            load_list.append([0,0,0])

        instructor_loads_abbrev = []  
            
        for other_load in other_load_type_dict[key]['loads']:
            instructor_id = other_load.instructor.id
            semester_name = other_load.semester.name.name
            ii = instructordict[instructor_id]
            jj = semesterdict[semester_name]
            load_list[ii][jj] = load_list[ii][jj]+load_hour_rounder(other_load.load_credit)
            faculty_summary_load_list[ii][jj] = faculty_summary_load_list[ii][jj]+other_load.load_credit

            instructor_loads_abbrev.append(other_load.instructor.first_name[:1]+
                                           ' '+other_load.instructor.last_name+
                                           ' ['+str(load_hour_rounder(other_load.load_credit))+' - '
                                           +semester_name+']'
            )
            
        for ii in range(number_faculty):
            total_other_load=total_other_load+sum(load_list[ii])
        admin_data_list.append({'load_type': other_load_type_dict[key]['load_type'].load_type,
                                'load_hour_list': load_list,
                                'instructor_loads_abbrev': instructor_loads_abbrev,
                                'id':other_load_type_dict[key]['load_type'].id,
                                'total_load':load_hour_rounder(total_other_load)
                                })
        if load_hour_rounder(total_other_load)==0:
            print other_load_type_dict[key]
            
            unassigned_admin_data_list.append({
                'load_type': other_load_type_dict[key]['load_type'].load_type,
                'load_hour_list': load_list,
                'instructor_loads_abbrev': instructor_loads_abbrev,
                'id':other_load_type_dict[key]['load_type'].id,
                'total_load':load_hour_rounder(total_other_load)
            })

    
#    assert False
            
#    for other_load_type in user_preferences.other_load_types_to_view.all():
#        load_list = []
#        total_other_load=0
#        for ii in range(number_faculty):
#            load_list.append([0,0,0])
#        for other_load in other_load_type.other_loads.all():
#            instructor_id = other_load.instructor.id
#            if other_load.semester.year.begin_on.year == academic_year and instructor_id in instructor_id_list:
#                semester_name = other_load.semester.name.name
#                ii = instructordict[instructor_id]
#                jj = semesterdict[semester_name]
#                load_list[ii][jj] = load_list[ii][jj]+load_hour_rounder(other_load.load_credit)
#                faculty_summary_load_list[ii][jj] = faculty_summary_load_list[ii][jj]+other_load.load_credit
#        for ii in range(number_faculty):
#            total_other_load=total_other_load+sum(load_list[ii])
#        admin_data_list.append({'load_type': other_load_type.load_type,
#                                'load_hour_list': load_list,
#                                'id':other_load_type.id,
#                                'total_load':load_hour_rounder(total_other_load)
#                                })
#        if load_hour_rounder(total_other_load)==0:
#            unassigned_admin_data_list.append({
#                    'load_type': other_load_type.load_type,
#                    'load_hour_list': load_list,
#                    'id':other_load_type.id,
#                    'total_load':load_hour_rounder(total_other_load)
#                    })

    total_load_hours=[]
    for ii in range(number_faculty):
        total_load_hours.append(load_hour_rounder(sum(faculty_summary_load_list[ii])))
        for jj in range(3):
            faculty_summary_load_list[ii][jj]=load_hour_rounder(faculty_summary_load_list[ii][jj])

    data_list_by_instructor = []
    for instructor_id in instructor_id_list:
        instructor_data = []
        admin_data = []
        for row in data_list:
            if row['load_hour_list'][instructordict[instructor_id]][0] >= 0:
                instructor_data.append({'comment':row['comment'],
                                        'semester':row['semester'],
                                        'meetings_scheduled': row['meetings_scheduled'],
                                        'name': row['name'],
                                        'load_hour_list': [row['load_hour_list'][instructordict[instructor_id]][0],
                                                           row['load_hour_list'][instructordict[instructor_id]][1]],
                                        'id': row['id'],
                                        'load_hours': row['load_hours'],
                                        'meeting_times': row['meeting_times'],
                                        'rooms': row['rooms'],
                                        'number': row['number'],
                                        'load_difference': row['load_difference']
                                        })
        for row in admin_data_list:
            total_other_load = 0
            for key in instructordict:
                total_other_load = total_other_load + sum(row['load_hour_list'][instructordict[key]])
            element = row['load_hour_list'][instructordict[instructor_id]]
            if element[0] > 0 or element[1] > 0 or element[2] > 0:
                admin_data.append({'load_type':row['load_type'],
                                   'load_hour_list':element,
                                   'id': row['id'],
                                   'total_load':load_hour_rounder(total_other_load)
                                   })


        data_list_by_instructor.append({'instructor_id':instructor_id,
                                        'course_info':instructor_data,
                                        'instructor':instructor_name_dict[instructor_id],
                                        'admin_data_list':admin_data,
                                        'load_summary':faculty_summary_load_list[instructordict[instructor_id]],
                                        'total_load_hours':total_load_hours[instructordict[instructor_id]]
                                        })



    context={'course_data_list':data_list,
             'instructor_list':instructor_name_list,
             'faculty_load_summary':faculty_summary_load_list,
             'admin_data_list':admin_data_list,
             'total_load_hours':total_load_hours,
             'department':department,
             'academic_year':academic_year_string,
             'instructordict':instructordict,
             'instructorlist':instructor_id_list,
             'instructor_integer_list':instructor_integer_list,
             'data_list_by_instructor':data_list_by_instructor,
             'can_edit': can_edit,
             'id': user_preferences.id,
             'unassigned_overassigned_data_list':unassigned_overassigned_data_list,
             'unassigned_admin_data_list':unassigned_admin_data_list
             }

    return context

@login_required
def export_data(request):
    """
    Exports data to an Excel file in 'actual load' or 'projected load' format.
    """
    close_all_divs(request)
    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view
    faculty_to_view = user_preferences.faculty_to_view.all()

    home = expanduser("~")
    today = date.today()
    date_string = str(today.month)+'/'+str(today.day)+'/'+str(today.year)

    can_edit = False
    if user_preferences.permission_level == 1:
        can_edit = True

# the following assumes that semesters are returned in the order Summer, Fall, J-term, Spring, so that
# Fall ends up being 0, J-term is 1 and Spring is 2.
    ii = -1
    semesterdict=dict()
    for semester in SemesterName.objects.all():
        semesterdict[semester.name] = ii
        ii=ii+1

#
# load for summer is added to the fall....
#
    semesterdict[u'Summer']=0

    if request.method == 'POST':
        faculty_export_list= request.POST.getlist('faculty_for_export')
        if len(faculty_export_list)==0:
            context = {'file_name': '', 'success': False}
            return render(request, 'export_complete.html', context)
        doc_type = request.POST.getlist('doc_type')[0]
        name_preparer = request.POST.getlist('name_preparer')[0]
        year_string = str(academic_year.begin_on.year)+'-'+str(extract_two_digits(academic_year.begin_on.year+1))
        if doc_type == u'actual':
            load_sheet_type = 'actual'
            due_date = 'March 12, '+str(academic_year.begin_on.year+1)
            file_name = 'ActualLoads_'+year_string+'.xls'       
        else:
            load_sheet_type = 'projected'
            due_date = 'February 26, '+str(academic_year.begin_on.year)
            file_name = 'ProjectedLoads_'+year_string+'.xls'

        # the following list is used later on to check if there are two people with the same last name
        faculty_last_names = [] 
        for faculty_id in faculty_export_list:
            faculty = FacultyMember.objects.get(pk = faculty_id)
            faculty_last_names.append(faculty.last_name)

        faculty_data_list = []
        for faculty_id in faculty_export_list:
            faculty = FacultyMember.objects.get(pk = faculty_id)
            course_load_dict=dict()
            course_name_dict=dict()
            course_number_dict=dict()
            course_comment_dict=dict()
            other_load_dict=dict()
            other_load_name_dict=dict()
            other_load_comment_dict=dict()
            for semester in academic_year.semesters.all():
# summer is still included...drop it?!?  Maybe just put a note in RED at the bottom of the spreadsheet if there is
# any summer load in the database, which didn't make it into the Excel spreadsheet.
                offering_instructors = faculty.offering_instructors.filter(course_offering__semester=semester)
                for oi in offering_instructors:
                    course_id = oi.course_offering.course.id
                    if course_id not in course_load_dict:
                        course_load_dict[course_id]=[0,0,0]
                        course_name_dict[course_id]=oi.course_offering.course.title
                        course_number_dict[course_id]=oi.course_offering.course.subject.abbrev+oi.course_offering.course.number
                        course_comment_dict[course_id]=oi.course_offering.comment
                    else: 
                        if course_comment_dict[course_id]=='':
                            course_comment_dict[course_id]=oi.course_offering.comment
                        else:
                            course_comment_dict[course_id]=course_comment_dict[course_id]+'; '+oi.course_offering.comment

                    course_load_dict[course_id][semesterdict[oi.course_offering.semester.name.name]] = course_load_dict[course_id][semesterdict[oi.course_offering.semester.name.name]] + oi.load_credit


                other_loads = faculty.other_loads.filter(semester=semester)
                for ol in other_loads:
                    other_load_id = ol.load_type.id
                    if other_load_id not in other_load_dict:
                        other_load_dict[other_load_id]=[0,0,0]
                        other_load_name_dict[other_load_id]=ol.load_type.load_type
                        other_load_comment_dict[other_load_id]=ol.comments
                    else: 
                        if other_load_comment_dict[other_load_id]=='':
                            other_load_comment_dict[other_load_id]=ol.comments
                        else:
                            other_load_comment_dict[other_load_id]=other_load_comment_dict[other_load_id]+'; '+ol.comments
                        
                    other_load_dict[other_load_id][semesterdict[ol.semester.name.name]] = other_load_dict[other_load_id][semesterdict[ol.semester.name.name]] + ol.load_credit


            faculty_data_list.append({'last_name':faculty.last_name, 
                                      'first_name':faculty.first_name, 
                                      'course_load_dict':course_load_dict,
                                      'course_name_dict':course_name_dict,
                                      'course_number_dict':course_number_dict,
                                      'course_comment_dict':course_comment_dict,
                                      'other_load_dict':other_load_dict,
                                      'other_load_name_dict':other_load_name_dict,
                                      'other_load_comment_dict':other_load_comment_dict})
        data_dict ={'school':department.school.name, 
                    'load_sheet_type': load_sheet_type, 
                    'department': department.name,
                    'prepared_by': name_preparer,
                    'date': date_string,
                    'academic_year': str(academic_year.begin_on.year)+'-'+str(extract_two_digits(academic_year.begin_on.year+1)),
                    'due_date': due_date,
                    'two_digit_year_fall': str(extract_two_digits(academic_year.begin_on.year)),
                    'two_digit_year_spring': str(extract_two_digits(academic_year.begin_on.year+1)),
                    'faculty_last_names':faculty_last_names
                    }
        book = prepare_excel_workbook(faculty_data_list,data_dict)
#        next = request.GET.get('next', 'profile')
        response = HttpResponse(mimetype="application/ms-excel")
#        response = HttpResponseRedirect('/planner/deptloadsummary', mimetype="application/ms-excel")
        response['Content-Disposition'] = 'attachment; filename=%s' % file_name
        book.save(response)

#        return redirect(next)
        
        return response
    


#        book.save(home+file_name)
#    response = HttpResponse(content_type='text/csv')
#    response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'
#    return response

#        next = request.GET.get('next', 'profile')
#        return redirect(next)
#        context = {'file_name': home+file_name, 'success': True}
#        return render(request, 'export_complete.html', context)
    else:
#        context = {'data_list': data_list, 'comment_list': comment_list, 
#                   'academic_year_copy_from':academic_year_copy_from,
#                   'academic_year_copy_to':academic_year_copy_to, 
#                   'check_all': check_all, 'check_all_flag_table':check_all_flag_table, 'year_id': id}
        faculty_list = []
        for faculty in department.faculty.all().order_by('last_name'):
            load = 0
            for semester in academic_year.semesters.all():
                offering_instructors = faculty.offering_instructors.filter(course_offering__semester=semester)
                for oi in offering_instructors:
                    load = load+oi.load_credit
                other_loads = faculty.other_loads.filter(semester=semester)
                for ol in other_loads:
                    load = load + ol.load_credit

            faculty_list.append({'name':faculty.first_name+' '+faculty.last_name,
                                 'id':faculty.id,
                                 'hrs': str(load_hour_rounder(load))+' hrs',
                                 })
        context = {'faculty_list': faculty_list, 'academic_year': academic_year,'can_edit': can_edit}
        return render(request, 'export_data.html', context)

def extract_two_digits(year):
    """
    Extracts the last two digits from a year; e.g., 2014 -> 14.  year is an
    int; returns an int.
    """
    return year-int(float(year)/100)*100

def prepare_excel_workbook(faculty_list_dict, global_data):
    """
    Prepares some content for an Excel file based on data contained in two lists of dictionaries.
    """

    one_inch = 3333
    styles = dict(
        bold = 'font: bold 1',
        italic = 'font: italic 1',
        # Wrap text in the cell
        wrap_bold = 'font: bold 1; align: wrap 1;',
        # White text on a blue background
        reversed = 'pattern: pattern solid, fore_color blue; font: color white;',
        # Light orange checkered background
        light_orange_bg = 'pattern: pattern fine_dots, fore_color white, back_color orange;',
        # Heavy borders
        bordered = 'border: top thick, right thick, bottom thick, left thick;',
        # 16 pt red text
        big_red = 'font: height 320, color red;',
        calibri_font = 'font: height 220, color black, name Calibri;',
        calibri_bold_bordered = 'font: height 220, color black, name Calibri, bold 1;border: top thin, right thin, bottom thin, left thin;',
        calibri_bordered = 'font: height 220, color black, name Calibri;border: top thin, right thin, bottom thin, left thin;',
        calibri_bold_bordered_centered = 'alignment: horizontal center; font: height 220, color black, name Calibri, bold 1;border: top thin, right thin, bottom thin, left thin;',
        calibri_centered = 'font: height 220, color black, name Calibri; alignment:horizontal center;',
        bold_title = 'alignment:horizontal center; font: height 240, color black, name Calibri, bold 1;',
        bold_title_red = 'alignment:horizontal center; font: height 240, color red, name Calibri, bold 1;',
        )

    column_widths = [int(1.41*one_inch),
                     int(0.81*one_inch),
                     int(2.11*one_inch),
                     int(0.7*one_inch),
                     int(0.7*one_inch),
                     int(0.7*one_inch),
                     int(0.7*one_inch),
                     int(2.58*one_inch)]

    # note: row heights are set automatically by the font size
    
    book = xlwt.Workbook()
    style_calibri_bordered = xlwt.easyxf(styles['calibri_bordered'])
    style_calibri_bordered_grey = xlwt.easyxf(styles['calibri_bordered']+'pattern: pattern solid, fore_color 22')
    style_calibri_centered = xlwt.easyxf(styles['calibri_centered'])
    style_calibri_bold_bordered = xlwt.easyxf(styles['calibri_bold_bordered'])

    if global_data['load_sheet_type']=='actual':
        type_text = 'ACTUAL Faculty Loads'
        type_text2 = 'Actual Load for:'
        table_title = 'This Year Actual Hours'
    else:
        type_text = 'PROJECTED Faculty Loads'
        type_text2 = 'Projected Load for:'
        table_title = 'Next Year Projected Hours'

    for faculty in faculty_list_dict:
        
        number_names = global_data['faculty_last_names'].count(faculty['last_name'])
        if number_names > 1:
            sheet = book.add_sheet(faculty['first_name']+' '+faculty['last_name'])
            sheet.portrait = False
        else:
            sheet = book.add_sheet(faculty['last_name'])
            sheet.portrait = False

        col = 0
        for width in column_widths:
            sheet.col(col).width = width
            col = col+1
        
        sheet.write_merge(0,0,0,7,global_data['school'],xlwt.easyxf(styles['bold_title']))
        sheet.write_merge(1,1,0,7,type_text,xlwt.easyxf(styles['bold_title_red']))
        sheet.write_merge(3,3,0,7,'Department: '+global_data['department'],style_calibri_centered)
        sheet.write_merge(5,5,0,7,'Prepared by (Dept Chair): '+global_data['prepared_by']+
                          '                           Date: '+global_data['date'],style_calibri_centered)
        sheet.write(7,4,type_text2,xlwt.easyxf(styles['calibri_font']))
        sheet.write(7,6,global_data['academic_year'],xlwt.easyxf(styles['calibri_bold_bordered']))
        sheet.write_merge(9,9,0,7,'Instructions:   Use one sheet per faculty member.  Include all assignments for which load credit is granted.  Non-teaching load (e.g. department',xlwt.easyxf(styles['calibri_font']+'border: top thin, right thin, left thin;'))
        sheet.write_merge(10,10,0,7,'chair duties) should be included and clearly identified.  DO NOT include independent studies/practicums.  For adjuncts, use one sheet with a',xlwt.easyxf(styles['calibri_font']+'border: right thin, left thin;'))
        sheet.write_merge(11,11,0,7,'combined total of load credit for each applicable term',xlwt.easyxf(styles['calibri_font']+'border: right thin, left thin;'))
        sheet.write_merge(12,12,0,7,'Forms should be emailed to your School Administrative Assistant by '+global_data['due_date']+'.',xlwt.easyxf(styles['calibri_centered']+'border: bottom thin, right thin, left thin;'))
        sheet.write_merge(13,13,2,5,table_title,xlwt.easyxf(styles['calibri_bold_bordered_centered']))
        sheet.write(14,0,'Faculty Member',xlwt.easyxf(styles['calibri_centered']+'border: top thin, right thin, bottom thin, left thin;'))
        sheet.write_merge(15,16,0,0,faculty['first_name']+' '+faculty['last_name'],xlwt.easyxf(styles['calibri_centered']+'border: top thin, right thin, bottom thin, left thin;'))
        sheet.write(14,1,'Course No.',xlwt.easyxf(styles['calibri_font']+'border: top thin, right thin, bottom thin;'))
        sheet.write(14,2,'Course Title',xlwt.easyxf(styles['calibri_centered']+'border: top thin, right thin, bottom thin;'))
        sheet.write(14,3,'Fall '+global_data['two_digit_year_fall'],xlwt.easyxf(styles['calibri_centered']+'border: top thin, right thin, bottom thin;'))
        sheet.write(14,4,'Jan '+global_data['two_digit_year_spring'],xlwt.easyxf(styles['calibri_centered']+'border: top thin, right thin, bottom thin;'))
        sheet.write(14,5,'Spring '+global_data['two_digit_year_spring'],xlwt.easyxf(styles['calibri_centered']+'border: top thin, right thin, bottom thin;'))
        sheet.write(14,6,'TOTAL',xlwt.easyxf(styles['calibri_centered']+'border: top thin, right thin, bottom thin;'))
        sheet.write(14,7,'Remarks',xlwt.easyxf(styles['calibri_centered']+'border: top thin, right thin, bottom thin;'))

        row_data_start = 15
        col_data_start = 3
        i = 0
        # add in load data for courses
        for key in sorted(faculty['course_number_dict'],key=faculty['course_number_dict'].get):
            if i>1:
                sheet.write(row_data_start+i,0,'',style_calibri_bordered_grey)
            sheet.write(row_data_start+i,1,faculty['course_number_dict'][key],style_calibri_bordered)
            sheet.write(row_data_start+i,2,faculty['course_name_dict'][key],style_calibri_bordered)
            for j, load in enumerate(faculty['course_load_dict'][key]):
                if load > 0:
                    sheet.write(row_data_start+i,col_data_start+j,load,style_calibri_bordered)
                else:
                    sheet.write(row_data_start+i,col_data_start+j,'',style_calibri_bordered)
            sum_string = 'SUM(D'+str(row_data_start+1+i)+':F'+str(row_data_start+1+i)+')'
            sheet.write(row_data_start+i,6,xlwt.Formula(sum_string),style_calibri_bordered)
            sheet.write(row_data_start+i,7,faculty['course_comment_dict'][key],style_calibri_bordered)
            i=i+1

        # add in "other" types of load
        for key in sorted(faculty['other_load_name_dict'],key=faculty['other_load_name_dict'].get):
            if i>1:
                sheet.write(row_data_start+i,0,'',style_calibri_bordered_grey)
            sheet.write(row_data_start+i,1,'',style_calibri_bordered)
            sheet.write(row_data_start+i,2,faculty['other_load_name_dict'][key],style_calibri_bordered)
            for j, load in enumerate(faculty['other_load_dict'][key]):
                if load > 0:
                    sheet.write(row_data_start+i,col_data_start+j,load,style_calibri_bordered)
                else:
                    sheet.write(row_data_start+i,col_data_start+j,'',style_calibri_bordered)
            sum_string = 'SUM(D'+str(row_data_start+1+i)+':F'+str(row_data_start+1+i)+')'
            sheet.write(row_data_start+i,6,xlwt.Formula(sum_string),style_calibri_bordered)
            sheet.write(row_data_start+i,7,faculty['other_load_comment_dict'][key],style_calibri_bordered)
            i=i+1

        # add in three blank rows for good measure
        for k in range(3):
            if i>1:
                sheet.write(row_data_start+i,0,'',style_calibri_bordered_grey)
            sheet.write(row_data_start+i,1,'',style_calibri_bordered)
            sheet.write(row_data_start+i,2,'',style_calibri_bordered)
            for j in range(3):
                sheet.write(row_data_start+i,col_data_start+j,'',style_calibri_bordered)
            sheet.write(row_data_start+i,6,'',style_calibri_bordered)
            sheet.write(row_data_start+i,7,'',style_calibri_bordered)
            i=i+1
        # Totals row
        sheet.write(row_data_start+i,0,'Totals',xlwt.easyxf(styles['calibri_bold_bordered']))
        sheet.write(row_data_start+i,1,'',style_calibri_bordered_grey)
        sheet.write(row_data_start+i,2,'',style_calibri_bordered_grey)
        sum_string = 'SUM(D'+str(row_data_start+1)+':D'+str(row_data_start+i)+')'
        sheet.write(row_data_start+i,3,xlwt.Formula(sum_string),style_calibri_bold_bordered)
        sum_string = 'SUM(E'+str(row_data_start+1)+':E'+str(row_data_start+i)+')'
        sheet.write(row_data_start+i,4,xlwt.Formula(sum_string),style_calibri_bold_bordered)
        sum_string = 'SUM(F'+str(row_data_start+1)+':F'+str(row_data_start+i)+')'
        sheet.write(row_data_start+i,5,xlwt.Formula(sum_string),style_calibri_bold_bordered)
        sum_string = 'SUM(G'+str(row_data_start+1)+':G'+str(row_data_start+i)+')'
        sheet.write(row_data_start+i,6,xlwt.Formula(sum_string),style_calibri_bold_bordered)
        sheet.write(row_data_start+i,7,'',style_calibri_bordered)
        i=i+1

        for k in range(7):
            sheet.write(row_data_start+i,k,'',style_calibri_bordered_grey)
        sheet.write(row_data_start+i,7,'',style_calibri_bordered)
        i=i+1

        sheet.write(row_data_start+i,0,'Adjuncts (hrs only)',xlwt.easyxf(styles['calibri_bold_bordered']))
        sheet.write(row_data_start+i,1,'',style_calibri_bordered_grey)
        sheet.write(row_data_start+i,2,'',style_calibri_bordered_grey)
        sheet.write(row_data_start+i,3,'',style_calibri_bold_bordered)
        sheet.write(row_data_start+i,4,'',style_calibri_bold_bordered)
        sheet.write(row_data_start+i,5,'',style_calibri_bold_bordered)
        sheet.write(row_data_start+i,6,'',style_calibri_bold_bordered)
        sheet.write(row_data_start+i,7,'',style_calibri_bordered)
        i=i+1

    return book

def load_hour_rounder(load):
    """Rounds load if the load is close to an int"""
    if abs(round(load)-load)<0.01:
        # if the load is close to an int, round it, then int it (adding 0.01 to be on the safe side)
        if load>0:
            rounded_load = int(round(load)+0.01)
        else:
            rounded_load = int(round(load)-0.01)
    else:
        rounded_load = load
    return rounded_load

def room_list_summary(scheduled_classes):
    """
    Returns a list of the rooms in which a given class occurs during a given semester;
    scheduled_classes is assumed to be a list of ScheduledClass objects with at least one element.
    """
    room_list = []
    for sc in scheduled_classes:
        room = sc.room.building.abbrev+' '+sc.room.number
        if room not in room_list:
            room_list.append(room)

    return room_list


def class_time_summary(scheduled_classes):
# Returns a class time summary list, such as ['MWF 9-9:50','T 10-10:50']
# scheduled_classes is assumed to be a list of ScheduledClass objects with at least one element

    day_list = ['M','T','W','R','F']
    time_dict = dict()
    schedule_list = []
    for sc in scheduled_classes:
        time_string=start_end_time_string(sc.begin_at.hour, sc.begin_at.minute, sc.end_at.hour, sc.end_at.minute)
        schedule_list.append([sc.day, time_string])
        time_dict[time_string]=''

    schedule_sorted = sorted(schedule_list, key=lambda row: (row[0], row[1]))

    for item in schedule_sorted:
        time_dict[item[1]]=time_dict[item[1]]+day_list[item[0]]

#    print time_dict

    class_times = ''
    ii = len(time_dict.keys())
    for key in time_dict.keys():
        class_times = class_times+time_dict[key]+' '+key
        ii = ii-1
        if ii > 0:
            class_times = class_times + "; "

    class_times_list = []
    for key in time_dict.keys():
        class_times_list.append(time_dict[key]+' '+key)

#    print class_times_list
# Note: class_times could be sent as well; it is a string of meeting times separated by semi-colons
#       ===> if this is done, need to edit the template a bit and also the "---" case, to make it
#            a simple string instead of a list
    return class_times_list

def class_time_and_room_summary(scheduled_classes):
# Returns a class time summary list and an accompanying room list, such as ['MWF 9-9:50','T 10-10:50'] and ['NS 210', 'ESC 141']
# scheduled_classes is assumed to be a list of ScheduledClass objects with at least one element

    day_list = ['M','T','W','R','F']
    time_dict = dict()
    room_dict = dict()
    day_dict = dict()
    schedule_list = []
    for sc in scheduled_classes:
        time_string=start_end_time_string(sc.begin_at.hour, sc.begin_at.minute, sc.end_at.hour, sc.end_at.minute)
        room = sc.room.building.abbrev+' '+sc.room.number
        schedule_list.append([sc.day, time_string, room])
        day_dict[time_string+room]=''
        room_dict[time_string+room] = room
        time_dict[time_string+room] = time_string

    schedule_sorted = sorted(schedule_list, key=lambda row: (row[0], row[1]))

    for item in schedule_sorted:
        day_dict[item[1]+item[2]]=day_dict[item[1]+item[2]]+day_list[item[0]]

    class_times_list = []
    room_list = []
    for key in day_dict.keys():
        class_times_list.append(day_dict[key]+' '+time_dict[key])
        room_list.append(room_dict[key])

    return class_times_list, room_list




def start_end_time_string(start_hour,start_minute,end_hour,end_minute):
# given starting and ending data, returns a string such as '9-9:50' or '9:15-10:30'

    time = str(start_hour)
    if 0<start_minute < 9:
        time = time+':0'+str(start_minute)
    elif start_minute>9:
        time = time+':'+str(start_minute)
    time = time+'-'+str(end_hour)
    if 0<end_minute < 9:
        time = time+':0'+str(end_minute)
    elif end_minute > 9:
        time = time+':'+str(end_minute)
    return time


@login_required
def update_course_offering(request,id, daisy_chain):
# daisy_chain is "0" (False) or "1" (True) and says whether the page should display a "skip this step" link at the bottom

    if int(daisy_chain):
        daisy_chaining = True
    else:
        daisy_chaining = False

    if "return_to_page" in request.session:
        next = request.session["return_to_page"]
    else:
        next = "home"

    instance = CourseOffering.objects.get(pk = id)
    form = CourseOfferingForm(instance=instance)
    department_abbrev = instance.course.subject.department.abbrev
    dept_id = instance.course.subject.department.id
    # create the formset class

    InstructorFormset = inlineformset_factory(CourseOffering, OfferingInstructor,
                                              formset=BaseInstructorFormSet)
    InstructorFormset.form = staticmethod(curry(InstructorForm, department_id=dept_id))

    # create the formset
    formset = InstructorFormset(instance = instance)

    errordict={}
    dict1 = {
        "form": form
        , "formset": formset
        , "instance": instance
        , "course": instance
        , "errordict": errordict
        , "daisy_chaining": daisy_chaining
        , "next": next
    }

    if request.method == 'POST':
        form = CourseOfferingForm(request.POST, instance = instance)
        formset = InstructorFormset(request.POST, instance = instance)

        formset.is_valid()
        prof_repeated_errors=formset.non_form_errors()

        if form.is_valid() and formset.is_valid() and not prof_repeated_errors:
            form.save()
            formset.save()
#            next = request.GET.get('next', 'profile')
            if "return_to_page" in request.session:
                next = request.session["return_to_page"]
            else:
                next = "home"
                return redirect(next)

            return redirect(next)
#            return redirect('department_load_summary')
        else:
            dict1["form"]=form
            dict1["formset"]=formset

            if form.errors.has_key('load_available'):
                errordict.update({'load_available': form.errors['load_available']})
            if form.errors.has_key('max_enrollment'):
                errordict.update({'max_enrollment': form.errors['max_enrollment']})


            if prof_repeated_errors:
                errordict.update({'prof_repeated_error':prof_repeated_errors})
            if form.errors.has_key('__all__'):
                errordict.update({'over_all_form_errors':form.errors['__all__']})
            for subform in formset:
                if subform.errors:
                    errordict.update(subform.errors)

            return render(request, 'update_course_offering.html', dict1)
    else:
        # User is not submitting the form; show them the blank add create your own course form
        return render(request, 'update_course_offering.html', dict1)




@login_required
def update_class_schedule(request,id, daisy_chain):
# daisy_chain is "0" (False) or "1" (True) and says whether the page should advance to set up professors next, or just
# return to the "return_to_page".

    if int(daisy_chain):
        daisy_chaining = True
    else:
        daisy_chaining = False

    instance = CourseOffering.objects.get(pk = id)

#    form = CourseOfferingForm(instance=instance)
# create the formset class
    ClassScheduleFormset = inlineformset_factory(CourseOffering, ScheduledClass, formset = BaseClassScheduleFormset, extra=4)
# create the formset
    formset = ClassScheduleFormset(instance=instance)

    errordict={}
    dict = {"formset": formset
        , "instance": instance
        , "course": instance
        , "errordict": errordict
        , "daisy_chaining": daisy_chaining
    }

    if request.method == 'POST':
#        form = CourseOfferingForm(request.POST, instance=instance)
        formset = ClassScheduleFormset(request.POST, instance = instance)

        formset.is_valid()
        formset_error=formset.non_form_errors()

        if formset.is_valid() and not formset_error:
#            form.save()
            formset.save()
            if not int(daisy_chain):
                if "return_to_page" in request.session:
                    next = request.session["return_to_page"]
                else:
                    next = "home"
                return redirect(next)
            else:
                url_string = '/planner/updatecourseoffering/'+str(instance.id)+'/1/'
                print url_string
                return redirect(url_string)
        else:
            dict["formset"]=formset
            if formset_error:
                errordict.update({'formset_error':formset_error})
            for subform in formset:
                if subform.errors:
                    errordict.update(subform.errors)

            return render(request, 'update_class_schedule.html', dict)
    else:
        # User is not submitting the form; show them the blank add create your own course form
        return render(request, 'update_class_schedule.html', dict)


@login_required
def weekly_schedule(request):
    """Display schedules for professors in the department"""

# things that are currently hard-coded and could/should be fixed:
# - earliest course is 7 a.m.
# - hard-coded the semester "exclusion" list...could pass it instead
#
# NEED TO CHECK FOR COURSE TIME CONFLICTS!!!!!!!
#
    close_all_divs(request)
    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view.begin_on.year
    academic_year_string = str(academic_year)+'-'+str(academic_year+1)


#    department = Department.objects.filter(abbrev=u'PEN')[0]
#    academic_year = 2013

    semester_names_to_exclude = [u'Summer']

    semester_list = []
    for semester in SemesterName.objects.all():
        if semester.name not in semester_names_to_exclude:
            semester_list.append(semester.name)

    num_data_columns = 5
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    data_list =[]
    idnum = 0
    prof_id = 0

    for faculty_member in user_preferences.faculty_to_view.filter(department=department).order_by('last_name'):
        prof_id = prof_id + 1
        data_this_professor = []
        for semester_name in semester_list:
            idnum = idnum + 1
            course_offering_list_all_years = faculty_member.course_offerings.filter(semester__name__name=semester_name)
            course_offering_list = []
            for co in course_offering_list_all_years:
                if co.semester.year.begin_on.year == academic_year:
                    course_offering_list.append(co)

            if semester_name == semester_list[0]:
                table_title = faculty_member.first_name[0]+'. '+faculty_member.last_name+' ('+semester_name+', '+str(academic_year)+')'
            else:
                table_title = faculty_member.first_name[0]+'. '+faculty_member.last_name+' ('+semester_name+', '+str(academic_year+1)+')'

            courses_after_five = False
            for course_offering in course_offering_list:
                for scheduled_class in course_offering.scheduled_classes.all():
                    if scheduled_class.end_at.hour > 16:
                        courses_after_five = True

            schedule = initialize_canvas_data(courses_after_five, num_data_columns)

            grid_list, filled_row_list, table_text_list = create_schedule_grid(schedule, weekdays, 'MWF')
            table_text_list.append([schedule['width']/2,schedule['border']/2,
                                    table_title,
                                    schedule['table_title_font'],
                                    schedule['table_header_text_colour']])

            box_list = []
            box_label_list = []

            conflict_check_dict = {0:[],1:[],2:[],3:[],4:[]}
            for course_offering in course_offering_list:
                for scheduled_class in course_offering.scheduled_classes.all():
                    box_data, course_data, room_data = rectangle_coordinates_schedule(schedule, scheduled_class,
                                                                                      scheduled_class.day)
                    box_list.append(box_data)
                    box_label_list.append(course_data)
                    box_label_list.append(room_data)
                    conflict_check_dict[scheduled_class.day].append([scheduled_class.begin_at.hour*100+scheduled_class.begin_at.minute,
                                                                     scheduled_class.end_at.hour*100+scheduled_class.end_at.minute,
                                                                     course_offering.course.subject.abbrev+' '+course_offering.course.number])
                                                 


        # format for filled rectangles is: [xleft, ytop, width, height, fillcolour, linewidth, bordercolour]
        # format for text is: [xcenter, ycenter, text_string, font, text_colour]

            json_box_list = simplejson.dumps(box_list)
            json_box_label_list = simplejson.dumps(box_label_list)
            json_grid_list = simplejson.dumps(grid_list)
            json_filled_row_list = simplejson.dumps(filled_row_list)
            json_table_text_list = simplejson.dumps(table_text_list)

            overlap_dict = check_for_conflicts(conflict_check_dict)
            error_messages=[]
            for key in overlap_dict:
                for row in overlap_dict[key]:
                    error_messages.append([weekdays[key],row[0]+' conflicts with '+row[1]])
            
            id = 'id'+str(idnum)
            data_this_professor.append({'prof_id': prof_id,
                                        'faculty_name': faculty_member.first_name[0]+'. '+faculty_member.last_name,
                                        'json_box_list': json_box_list,
                                        'json_box_label_list':json_box_label_list,
                                        'json_grid_list': json_grid_list,
                                        'json_filled_row_list': json_filled_row_list,
                                        'json_table_text_list': json_table_text_list,
                                        'id':id,
                                        'schedule':schedule,
                                        'conflict':error_messages})
        data_list.append(data_this_professor)

    context={'data_list':data_list, 'year':academic_year_string, 'id': user_preferences.id, 'department': user_preferences.department_to_view}
    return render(request, 'weekly_schedule.html', context)

@login_required
def daily_schedule(request):
    """Display daily schedules for the department"""
    close_all_divs(request)
    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view.begin_on.year
    academic_year_string = str(academic_year)+'-'+str(academic_year+1)

# things that are currently hard-coded and could/should be fixed:
# - earliest course is 7 a.m.
# - hard-coded the semester "exclusion" list...could pass it instead
#
# NEED TO CHECK FOR COURSE TIME CONFLICTS!!!!!!!
#

    semester_names_to_exclude = [u'Summer']

    semester_list = []
    for semester in SemesterName.objects.all():
        if semester.name not in semester_names_to_exclude:
            semester_list.append(semester.name)

    instructor_dict = {}
    ii = 0
    professor_list = []
    for faculty_member in user_preferences.faculty_to_view.filter(department=department):
        instructor_dict[faculty_member.id] = ii
        professor_list.append(faculty_member.first_name[0]+'. '+faculty_member.last_name)
        ii=ii+1
    num_data_columns = ii

    data_list =[]
    idnum = 0

    day_list = ['Monday','Tuesday','Wednesday','Thursday','Friday']
    day_dict = {'Monday':0, 'Tuesday':1, 'Wednesday':2, 'Thursday':3, 'Friday':4}

    chapel_dict = {'Monday':'every', 'Tuesday':'none', 'Wednesday':'every', 'Thursday':'none', 'Friday':'every'}

    for day in day_list:
        data_this_day = []
        for semester_name in semester_list:
            instructor_conflict_check_dict = {}
            room_conflict_check_dict = {}
            for faculty_member in user_preferences.faculty_to_view.filter(department=department):
                instructor_conflict_check_dict[faculty_member.id] = {'today':[]}
#        for room in user_preferences.rooms_to_view.all().order_by('building','number'):
#            room_conflict_check_dict[room.id] = {'Monday':[], 'Tuesday':[], 'Wednesday':[], 'Thursday':[], 'Friday':[]}

            if semester_name == semester_list[0]:
                current_semester_string = semester_name+', '+str(academic_year)
                table_title = department.name +' ('+semester_name+', '+str(academic_year)+')'
            else:
                current_semester_string = semester_name+', '+str(academic_year+1)
                table_title = department.name +' ('+semester_name+', '+str(academic_year+1)+')'

            courses_after_five = False
            idnum = idnum + 1

            if semester_name == semester_list[0]:
                table_title = day+'s'+' ('+semester_name+', '+str(academic_year)+')'
            else:
                table_title = day+'s'+' ('+semester_name+', '+str(academic_year+1)+')'

            for sc in ScheduledClass.objects.filter(Q(day=day_dict[day])&
                                                    Q(course_offering__semester__name__name=semester_name)&
                                                    Q(course_offering__semester__year__begin_on__year = academic_year)&
                                                    Q(course_offering__course__subject__department = department)):
                if sc.end_at.hour > 16:
                    courses_after_five = True

                for instructor in sc.course_offering.instructor.all():
                    if instructor.id not in instructor_conflict_check_dict.keys():
                        instructor_conflict_check_dict[instructor.id] = {'today':[]}
                    instructor_conflict_check_dict[instructor.id]['today'].append([sc.begin_at.hour*100+sc.begin_at.minute,
                                                                                   sc.end_at.hour*100+sc.end_at.minute,
                                                                                   sc.course_offering.course.subject.abbrev+sc.course_offering.course.number+
                                                                                   ' ('+start_end_time_string(sc.begin_at.hour,
                                                                                                              sc.begin_at.minute,sc.end_at.hour,sc.end_at.minute)+')'])

                if sc.room.id not in room_conflict_check_dict.keys():
                    room_conflict_check_dict[sc.room.id] = {'today':[]}
                room_conflict_check_dict[sc.room.id]['today'].append([sc.begin_at.hour*100+sc.begin_at.minute,
                                                                      sc.end_at.hour*100+sc.end_at.minute,
                                                                      sc.course_offering.course.subject.abbrev+sc.course_offering.course.number+
                                                                      ' ('+start_end_time_string(sc.begin_at.hour,
                                                                                                 sc.begin_at.minute,sc.end_at.hour,sc.end_at.minute)+')'])

            schedule = initialize_canvas_data(courses_after_five, num_data_columns)

            grid_list, filled_row_list, table_text_list = create_schedule_grid(schedule, professor_list, chapel_dict[day])
            table_text_list.append([schedule['width']/2,schedule['border']/2,
                                    table_title,
                                    schedule['table_title_font'],
                                    schedule['table_header_text_colour']])

            box_list = []
            box_label_list = []
            for sc in ScheduledClass.objects.filter(Q(day=day_dict[day])&
                                                    Q(course_offering__semester__name__name=semester_name)&
                                                    Q(course_offering__semester__year__begin_on__year = academic_year)&
                                                    Q(course_offering__course__subject__department = department)):
#                for instructor in sc.course_offering.offeringinstructor_set.all():
                for instructor in sc.course_offering.offering_instructors.all():
                    if instructor.instructor in user_preferences.faculty_to_view.filter(department=department):
                        box_data, course_data, room_data = rectangle_coordinates_schedule(schedule, sc,
                                                                                          instructor_dict[instructor.instructor.id])
                        box_list.append(box_data)
                        box_label_list.append(course_data)
                        box_label_list.append(room_data)


        # format for filled rectangles is: [xleft, ytop, width, height, fillcolour, linewidth, bordercolour]
        # format for text is: [xcenter, ycenter, text_string, font, text_colour]

            json_box_list = simplejson.dumps(box_list)
            json_box_label_list = simplejson.dumps(box_label_list)
            json_grid_list = simplejson.dumps(grid_list)
            json_filled_row_list = simplejson.dumps(filled_row_list)
            json_table_text_list = simplejson.dumps(table_text_list)

            error_messages=[]
            for faculty_member_id in instructor_conflict_check_dict.keys():
                overlap_dict = check_for_conflicts(instructor_conflict_check_dict[faculty_member_id])
                faculty_member = FacultyMember.objects.get(pk = faculty_member_id)
                for key in overlap_dict:
                    for row in overlap_dict[key]:
                        error_messages.append([faculty_member.first_name[:1]+' '+
                                               faculty_member.last_name+' has a conflict:',
                                               row[0]+' conflicts with '+row[1]])

            for room_id in room_conflict_check_dict.keys():
                overlap_dict = check_for_conflicts(room_conflict_check_dict[room_id])
                room = Room.objects.get(pk = room_id)
                for key in overlap_dict:
                    for row in overlap_dict[key]:
                        error_messages.append([room.building.abbrev+room.number+' has a conflict:',
                                               row[0]+' conflicts with '+row[1]])

            id = 'id'+str(idnum)
            data_this_day.append({'day_name': day,
                                  'json_box_list': json_box_list,
                                  'json_box_label_list':json_box_label_list,
                                  'json_grid_list': json_grid_list,
                                  'json_filled_row_list': json_filled_row_list,
                                  'json_table_text_list': json_table_text_list,
                                  'id':id,
                                  'schedule':schedule,
                                  'error_messages':error_messages,
                                  'semester':current_semester_string})
        data_list.append(data_this_day)

    context={'data_list':data_list, 'year':academic_year_string, 'id': user_preferences.id, 'department': user_preferences.department_to_view}
    return render(request, 'daily_schedule.html', context)


@login_required
def room_schedule(request):
    """Display daily schedules for the department"""
    close_all_divs(request)
    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view.begin_on.year
    academic_year_string = str(academic_year)+'-'+str(academic_year+1)

# things that are currently hard-coded and could/should be fixed:
# - earliest course is 7 a.m.
# - hard-coded the semester "exclusion" list...could pass it instead
#
# NEED TO CHECK FOR COURSE TIME CONFLICTS!!!!!!!
#

    semester_names_to_exclude = [u'Summer']

    semester_list = []
    for semester in SemesterName.objects.all():
        if semester.name not in semester_names_to_exclude:
            semester_list.append(semester.name)

    num_data_columns = 5
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    data_list =[]
    idnum = 0
    roomid = 0

    for room in user_preferences.rooms_to_view.all().order_by('building__name','number'):
        data_this_room = []
        roomid=roomid+1
        for semester_name in semester_list:
            courses_after_five = False
            idnum = idnum + 1

            if semester_name == semester_list[0]:
                table_title = room.building.name+' '+room.number+' ('+semester_name+', '+str(academic_year)+')'
            else:
                table_title = room.building.abbrev+' '+room.number+' ('+semester_name+', '+str(academic_year+1)+')'

            for sc in ScheduledClass.objects.filter(Q(room = room)&
                                                    Q(course_offering__semester__name__name=semester_name)&
                                                    Q(course_offering__semester__year__begin_on__year = academic_year)):
                if sc.end_at.hour > 16:
                    courses_after_five = True

            schedule = initialize_canvas_data(courses_after_five, num_data_columns)

            grid_list, filled_row_list, table_text_list = create_schedule_grid(schedule, weekdays, 'MWF')
            table_text_list.append([schedule['width']/2,schedule['border']/2,
                                    table_title,
                                    schedule['table_title_font'],
                                    schedule['table_header_text_colour']])


            conflict_check_dict = {0:[],1:[],2:[],3:[],4:[]}
            box_list = []
            box_label_list = []
            for sc in ScheduledClass.objects.filter(Q(room = room)&
                                                    Q(course_offering__semester__name__name=semester_name)&
                                                    Q(course_offering__semester__year__begin_on__year = academic_year)):
                box_data, course_data, room_data = rectangle_coordinates_schedule(schedule, sc, sc.day)
                box_list.append(box_data)
                box_label_list.append(course_data)
                box_label_list.append(room_data)
                conflict_check_dict[sc.day].append([sc.begin_at.hour*100+sc.begin_at.minute,
                                                    sc.end_at.hour*100+sc.end_at.minute,
                                                    sc.course_offering.course.subject.abbrev+' '+sc.course_offering.course.number])


        # format for filled rectangles is: [xleft, ytop, width, height, fillcolour, linewidth, bordercolour]
        # format for text is: [xcenter, ycenter, text_string, font, text_colour]

            json_box_list = simplejson.dumps(box_list)
            json_box_label_list = simplejson.dumps(box_label_list)
            json_grid_list = simplejson.dumps(grid_list)
            json_filled_row_list = simplejson.dumps(filled_row_list)
            json_table_text_list = simplejson.dumps(table_text_list)

            overlap_dict = check_for_conflicts(conflict_check_dict)
            error_messages=[]
            for key in overlap_dict:
                for row in overlap_dict[key]:
                    error_messages.append([weekdays[key],row[0]+' conflicts with '+row[1]])

            id = 'id'+str(idnum)
            data_this_room.append({'room_id':roomid,
                                   'room_name': room.building.abbrev+' '+room.number,
                                   'json_box_list': json_box_list,
                                   'json_box_label_list':json_box_label_list,
                                   'json_grid_list': json_grid_list,
                                   'json_filled_row_list': json_filled_row_list,
                                   'json_table_text_list': json_table_text_list,
                                   'id':id,
                                   'schedule':schedule,
                                   'conflict':error_messages})
        data_list.append(data_this_room)

    context={'data_list':data_list, 'year':academic_year_string, 'id': user_preferences.id, 'department': user_preferences.department_to_view}
    return render(request, 'room_schedule.html', context)

@login_required
def course_schedule(request):
    """Display daily schedules for the department"""
    close_all_divs(request)
    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view.begin_on.year
    academic_year_string = str(academic_year)+'-'+str(academic_year+1)

# things that are currently hard-coded and could/should be fixed:
# - earliest course is 7 a.m.
# - hard-coded the semester "exclusion" list...could pass it instead
#
# NEED TO CHECK FOR COURSE TIME CONFLICTS!!!!!!!
#

    semester_names_to_exclude = [u'Summer']

    semester_list = []
    for semester in SemesterName.objects.all():
        if semester.name not in semester_names_to_exclude:
            semester_list.append(semester.name)

    num_data_columns = 5
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    data_list =[]
    idnum = 0
    courseid = 0

    for subject in department.subjects.all():
        for course in subject.courses.all(): #filter(offerings__semester__year__begin_on__year = academic_year):
            co = course.offerings.filter(semester__year__begin_on__year = academic_year)
            if len(co) > 0:
                co_semester_list=[]
                for co_item in co:
                    co_semester_list.append(co_item.semester.name.name)
                data_this_course = []
                courseid=courseid+1
                for semester_name in semester_list:
                    if semester_name in co_semester_list:
                        courses_after_five = False
                        idnum = idnum + 1

                        if semester_name == semester_list[0]:
                            table_title = course.title+' ('+semester_name+', '+str(academic_year)+')'
                        else:
                            table_title = course.title+' ('+semester_name+', '+str(academic_year+1)+')'

                        for sc in ScheduledClass.objects.filter(Q(course_offering__course = course)&
                                                                Q(course_offering__semester__name__name=semester_name)&
                                                                Q(course_offering__semester__year__begin_on__year = academic_year)):
                            if sc.end_at.hour > 16:
                                courses_after_five = True

                        schedule = initialize_canvas_data(courses_after_five, num_data_columns)

                        grid_list, filled_row_list, table_text_list = create_schedule_grid(schedule, weekdays, 'MWF')
                        table_text_list.append([schedule['width']/2,schedule['border']/2,
                                                table_title,
                                                schedule['table_title_font'],
                                                schedule['table_header_text_colour']])

                        box_list = []
                        box_label_list = []
                        for sc in ScheduledClass.objects.filter(Q(course_offering__course = course)&
                                                                Q(course_offering__semester__name__name=semester_name)&
                                                                Q(course_offering__semester__year__begin_on__year = academic_year)):
                            box_data, course_data, room_data = rectangle_coordinates_schedule(schedule, sc, sc.day)
                            box_list.append(box_data)
                            box_label_list.append(course_data)
                            box_label_list.append(room_data)


                            # format for filled rectangles is: [xleft, ytop, width, height, fillcolour, linewidth, bordercolour]
                            # format for text is: [xcenter, ycenter, text_string, font, text_colour]

                        json_box_list = simplejson.dumps(box_list)
                        json_box_label_list = simplejson.dumps(box_label_list)
                        json_grid_list = simplejson.dumps(grid_list)
                        json_filled_row_list = simplejson.dumps(filled_row_list)
                        json_table_text_list = simplejson.dumps(table_text_list)

                        id = 'id'+str(idnum)
                        data_this_course.append({'course_id':courseid,
                                                 'course_name': course.subject.abbrev+' '+course.number+': '+course.title,
                                                 'json_box_list': json_box_list,
                                                 'json_box_label_list':json_box_label_list,
                                                 'json_grid_list': json_grid_list,
                                                 'json_filled_row_list': json_filled_row_list,
                                                 'json_table_text_list': json_table_text_list,
                                                 'id':id,
                                                 'schedule':schedule})
                data_list.append(data_this_course)

    context={'data_list':data_list, 'year':academic_year_string, 'id': user_preferences.id, 'department': user_preferences.department_to_view}
    return render(request, 'course_schedule.html', context)

def check_for_conflicts(conflict_dict):
    """
    Checks for time conflicts in a dictionary of lists.
    The lists are assumed to have the form:
    {key1:[[begin,end,string],[begin,end,string]],key2:....}.
    """
    time_blocks = [[0,0],[0,0]]
    return_dict={}
    for key in conflict_dict:
        return_dict[key]=[]
        n = len(conflict_dict[key])
        for i in range(0,n-1):
            for j in range(i+1,n):
                time_blocks[0][0] = conflict_dict[key][i][0]
                time_blocks[0][1] = conflict_dict[key][i][1]
                time_blocks[1][0] = conflict_dict[key][j][0]
                time_blocks[1][1] = conflict_dict[key][j][1]
                if time_blocks_overlap(time_blocks):
                    return_dict[key].append([conflict_dict[key][i][2],conflict_dict[key][j][2]])

    return return_dict
    
def time_blocks_overlap(time_blocks):
    """
    Compares two time blocks to see if they overlap.  If so, returns True; otherwise, False.
    Blocks are of the form [[begin1,end1],[begin2,end2]].
    """
    begin1 = time_blocks[0][0]
    end1 = time_blocks[0][1]
    begin2 = time_blocks[1][0]
    end2 = time_blocks[1][1]

    if ((begin1 < end2) & (begin1 >= begin2)) or ((end1 <= end2) & (end1 > begin2)) or ((end1 > end2) & (begin1 < begin2)):
        return True
    else:
        return False

def initialize_canvas_data(courses_after_five, num_data_columns):
    """
    Creates a dictionary of data for the canvas for various schedules.
    """

    width_day = 120
    width_hour_names = 100
    height_day_names = 40
    height_hour_block = 60
    border = 50
    start_time = 7

    canvas_width = 2*border+num_data_columns*width_day+width_hour_names

    # 10 hour blocks (7 a.m.,..., 4 p.m.) or 15 (...9 p.m.)
    if courses_after_five:
        number_hour_blocks = 15
    else:
        number_hour_blocks = 10

    canvas_height = 2*border+height_day_names+height_hour_block*number_hour_blocks

    schedule = {'width':canvas_width,
                'height':canvas_height,
                'width_day':width_day,
                'width_hour_names':width_hour_names,
                'height_day_names':height_day_names,
                'height_hour_block':height_hour_block,
                'border':border,
                'number_hour_blocks':number_hour_blocks,
                'start_time':start_time,
                'row_background_fill_colour':'#f0f0f0',
                'box_fill_colour':'#d8d8d8',
                'box_line_width': 1,
                'box_border_colour':'#2f2f2f',
                'box_text_line_sep_pixels': 16,
                'box_font':'12pt Arial',
                'box_bold_font':'bold 12pt Arial',
                'grid_line_colour':'#b8b8b8',
                'grid_line_width':1,
                'table_header_font':'12pt Arial',
                'table_header_text_colour':'#2f2f2f',
                'table_title_font':'bold 14pt Arial',
                }

    return schedule

def create_schedule_grid(schedule,column_titles,chapel):
    """
    returns the coordinates for the lines that form the schedule grid in the
    form [[xbegin, ybegin, xend, yend],[...],[...]]
    """

# chapel can be "every" (every column), "none" (no columns) or "MWF" (1st, 3rd and 5th columns)

    line_coordinates_array = []
    filled_row_array = []
    text_array = []

    b = schedule['border']
    c_h = schedule['height']
    c_w = schedule['width']
    w_h_n = schedule['width_hour_names']
    w_d = schedule['width_day']
    n_h_b = schedule['number_hour_blocks']
    h_h_b = schedule['height_hour_block']
    h_d_n = schedule['height_day_names']

    for ii in range(len(column_titles)):
        text_array.append([b+w_h_n+ii*w_d+w_d/2,b+h_d_n/2,
                           column_titles[ii],
                           schedule['table_header_font'],
                           schedule['table_header_text_colour']])

    if chapel == 'MWF':
        for ii in range(3):
            text_array.append([b+w_h_n+2*ii*w_d+w_d/2,b+h_d_n+3*h_h_b+h_h_b/2,
                               'chapel',
                               schedule['table_header_font'],
                               schedule['table_header_text_colour']])
    elif chapel == 'every':
        for ii in range(len(column_titles)):
            text_array.append([b+w_h_n+ii*w_d+w_d/2,b+h_d_n+3*h_h_b+h_h_b/2,
                               'chapel',
                               schedule['table_header_font'],
                               schedule['table_header_text_colour']])

    start_time = schedule['start_time']
    for ii in range(n_h_b):
        time_int = start_time+ii
        time = str(time_int)+':00'
        text_array.append([b+w_h_n/2,b+h_d_n+ii*h_h_b+h_h_b/2,
                           time,
                           schedule['table_header_font'],
                           schedule['table_header_text_colour']])


    # coordinates for the vertical lines in the grid
    line_coordinates_array.append([b,b,b,c_h-b])
    for ii in range(len(column_titles)+1):
        line_coordinates_array.append([b+w_h_n+ii*w_d,b,b+w_h_n+ii*w_d,c_h-b])
    # coordinates for the horizontal lines in the grid
    line_coordinates_array.append([b,b,c_w-b,b])
    colour_on = False
    for ii in range(n_h_b+1):
        line_coordinates_array.append([b,b+h_d_n+ii*h_h_b,c_w-b,b+h_d_n+ii*h_h_b])
        if colour_on:
            filled_row_array.append([b,b+h_d_n+(ii-1)*h_h_b,c_w-2*b,h_h_b,
                                     schedule['row_background_fill_colour'],
                                     schedule['grid_line_width'],
                                     schedule['row_background_fill_colour']])
            colour_on = False
        else:
            colour_on = True

    return line_coordinates_array, filled_row_array, text_array



def rectangle_coordinates_schedule(schedule, scheduled_class_object, data_column):
    """
    returns the coordinates required (by the javascript in the template)
    to display a rectangular box for a single class meeting
    """

    b = schedule['border']
    w_h_n = schedule['width_hour_names']
    w_d = schedule['width_day']
    h_h_b = schedule['height_hour_block']
    h_d_n = schedule['height_day_names']

    # base_hour is the earliest hour on the schedule

    base_hour = schedule['start_time']
    begin_height_pixels = b+h_d_n+convert_time_to_pixels(h_h_b,base_hour,
                                                         scheduled_class_object.begin_at.hour,
                                                         scheduled_class_object.begin_at.minute)
    end_height_pixels = b+h_d_n+convert_time_to_pixels(h_h_b,base_hour,
                                                         scheduled_class_object.end_at.hour,
                                                         scheduled_class_object.end_at.minute)

    decimal_time = scheduled_class_object.begin_at.hour+scheduled_class_object.begin_at.minute/60.0

# format for filled rectangles is: [xleft, ytop, width, height, fillcolour, linewidth, bordercolour]

    xleft = b+w_h_n+data_column*w_d
    height = end_height_pixels-begin_height_pixels

    subject = scheduled_class_object.course_offering.course.subject.abbrev
    course_number = scheduled_class_object.course_offering.course.number
    course_label = subject+course_number
    room_label = scheduled_class_object.room.building.abbrev+scheduled_class_object.room.number

    line_sep = schedule['box_text_line_sep_pixels']

    box_data = [xleft, begin_height_pixels, w_d, height, schedule['box_fill_colour'],
                schedule['box_line_width'], schedule['box_border_colour']]

    course_data = [xleft+w_d/2, begin_height_pixels+height/2-line_sep/2, course_label,
                 schedule['box_font'],
                 schedule['table_header_text_colour']]

    room_data = [xleft+w_d/2, begin_height_pixels+height/2+line_sep/2, room_label,
                 schedule['box_font'],
                 schedule['table_header_text_colour']]

    return box_data, course_data, room_data

def convert_time_to_pixels(height_hour_block, base_hour, time_hour, time_minute):
    """
    converts a time in hours and minutes to a height in pixels, relative to a
    base hour; height_hour_block is in pixes; other quantities are ints
    """
# note: in at least some versions of python, "/" does integer division, so need to be careful
    return (time_hour-base_hour)*height_hour_block+time_minute*height_hour_block/60


@login_required
def course_summary(request, allow_delete):
    """Display courses for the department and semesters in which they are taught"""
# allow_delete == 0 => cannot delete courses
# allow_delete == 1 => can delete courses
    request.session["return_to_page"] = "/planner/coursesummary/0/"
    close_all_divs(request)
    user = request.user
    user_preferences = user.user_preferences.all()[0]
    academic_year = user_preferences.academic_year_to_view.begin_on.year
    academic_year_string = str(academic_year)+'-'+str(academic_year+1)

    department = user_preferences.department_to_view
    can_edit = False
    if user_preferences.permission_level == 1:
        can_edit = True

    ii = 0
    semesterdict=dict()
    for semester in SemesterName.objects.all():
        semesterdict[semester.name] = ii
        ii=ii+1
    number_semesters = ii

    year_list = []
    academic_year_dict=dict()
    ii = 0
    for year in AcademicYear.objects.all():
        year_list.append(str(year.begin_on.year)+'-'+str(year.begin_on.year + 1))
        academic_year_dict[year.begin_on.year] = ii
        ii=ii+1

    data_list = []
    for subject in department.subjects.all():
        for course in subject.courses.all():
            number = u"{0} {1}".format(course.subject,
                                       course.number)
            course_name = course.title
            offering_list = []
            for year in year_list:
                offering_list.append([0]*number_semesters)

            for course_offering in course.offerings.all():
                semester_name = course_offering.semester.name.name
                academic_year = course_offering.semester.year.begin_on.year
                try:
                    current_number_offerings = offering_list[academic_year_dict[academic_year]][semesterdict[semester_name]]
                    offering_list[academic_year_dict[academic_year]][semesterdict[semester_name]] = current_number_offerings+1
                except KeyError:
                    pass

            data_list.append({'number':number,
                              'name':course_name,
                              'offering_list': offering_list,
                              'id':course.id,
                              'credit_hrs':course.credit_hours
                              })


    context={'course_data_list':data_list, 'year_list':year_list, 
             'number_semesters': number_semesters,
             'can_edit': can_edit,
             'year':academic_year_string, 
             'id': user_preferences.id, 
             'department': user_preferences.department_to_view,
             'allow_delete': int(allow_delete)}
    return render(request, 'course_summary.html', context)



@login_required
def manage_course_offerings(request,id):
    """ 
    this function was previously used to manage the semester, etc., for course offerings (from the Course Summary page);
    that functionality has been moved to the Faculty Load Summary page.
    """
    user = request.user
    user_preferences = user.user_preferences.all()[0]
    year_id = user_preferences.academic_year_to_view.id

    instance = Course.objects.get(pk = id)
# create the formset class
    CourseOfferingFormset = inlineformset_factory(Course, CourseOffering, formset = BaseCourseOfferingFormset, extra=2, exclude='instructor')
# create the formset
#------new

#    CourseOfferingFormset.form = staticmethod(curry(ManageCourseOfferingForm, year_id=year_id))

#------new

    formset = CourseOfferingFormset(instance=instance)

    errordict={}
    dict = {"formset": formset
        , "instance": instance
        , "course": instance
        , "errordict": errordict
    }

    if request.method == 'POST':
#        form = CourseOfferingForm(request.POST, instance=instance)
        formset = CourseOfferingFormset(request.POST, instance = instance)

        formset.is_valid()
        formset_error=formset.non_form_errors()

        if formset.is_valid() and not formset_error:
#            form.save()
            formset.save()
            url_string="/planner/coursesummary/0/"
            return redirect(url_string)
        else:
            dict["formset"]=formset
            if formset_error:
                errordict.update({'formset_error':formset_error})
            for subform in formset:
                if subform.errors:
                    errordict.update(subform.errors)

            return render(request, 'manage_course_offerings.html', dict)
    else:
        # User is not submitting the form; show them the blank add create your own course form
        return render(request, 'manage_course_offerings.html', dict)

#
# Next:
# - add class rooms to form
# - use data from form to write to the database, which will involve writing a function to parse MWF, etc.
# - allow user to do a "quickie" version of the class schedule, even if it already exists in the database,
#   by first deleting everything and then hitting the new_class_schedule form (?) -> just check first thing
#   and delete existing data....

def new_class_schedule(request,id, daisy_chain):
# daisy_chain is "0" (False) or "1" (True) and says whether the page should advance to set up class schedules next, or just
# return to the "return_to_page".

# start is the start time in hours (7 for 7:00, etc.)
# duration is the class duration in minutes

    if int(daisy_chain):
        daisy_chaining = True
    else:
        daisy_chaining = False

    course_offering = CourseOffering.objects.get(pk=id)

    if request.method == 'POST':
        form = EasyDaySchedulerForm(request.POST)
        if form.is_valid():
            day_dict = {'M':0, 'T':1, 'W':2, 'R':3, 'F':4}

            # Note: days will be something like u'MWF', start will be something like u'700' or u'730' and duration will be something like u'50'
            days = form.cleaned_data.get('days')
            start = int(form.cleaned_data.get('start'))
            duration = int(form.cleaned_data.get('duration'))
            room = form.cleaned_data.get('room')

            for day in days:
                new_class = ScheduledClass(course_offering = course_offering)
                new_class.day = day_dict[day]

                start_hour=(start-start%100)/100
                start_minute=start%100
                end_hour = start_hour + (start_minute+duration)/60
                end_minute = (start_minute+duration)%60 
                
                if start_minute<10:
                    start_minute_string = '0'+str(start_minute)
                else:
                    start_minute_string = str(start_minute)
                if end_minute<10:
                    end_minute_string = '0'+str(end_minute)
                else:
                    end_minute_string = str(end_minute)
                new_class.begin_at = str(start_hour)+':'+start_minute_string
                new_class.end_at = str(end_hour)+':'+end_minute_string
                
                new_class.room = room
                # if the db hangs, try new_class.room_id = room.id
                new_class.save()

            if not int(daisy_chain):
                if "return_to_page" in request.session:
                    next = request.session["return_to_page"]
                else:
                    next = "home"
                return redirect(next)
            else:
                url_string = '/planner/updatecourseoffering/'+str(course_offering.id)+'/1/'
                print url_string
                return redirect(url_string)
        else:
            return render(request, 'new_class_schedule.html', {'form':form, 'id':id, 'daisy_chaining': daisy_chaining, 'course':course_offering})

    else:
        form = EasyDaySchedulerForm()
        return render(request, 'new_class_schedule.html', {'form':form, 'id':id, 'daisy_chaining': daisy_chaining, 'course':course_offering })

def add_course(request, daisy_chain):
# start is the start time in hours (7 for 7:00, etc.)
# duration is the class duration in minutes
#
# daisy_chain is "0" (False) or "1" (True) and says whether the page should advance to set up course offerings next, or just
# return to the "return_to_page".

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department_id = user_preferences.department_to_view.id

    course_list=[]
    if int(daisy_chain):
        warning = False
    else:
        warning = True
        for subject in Subject.objects.filter(Q(department__id = department_id)):
            for course in Course.objects.filter(subject=subject):
                course_list.append(course)

    if request.method == 'POST':
        form = AddCourseForm(department_id,request.POST)
        if form.is_valid():
            course = form.save()
            if not int(daisy_chain):
                if "return_to_page" in request.session:
                    next = request.session["return_to_page"]
                else:
                    next = "home"
                return redirect(next)
            else:
                url_string = '/planner/addcourseoffering/'+str(course.id)+'/1/'
                print url_string
                return redirect(url_string)
        else:
            context = {'form': form, 'title': 'Add New Course', 'course_list':course_list}
            return render(request, 'add_course.html', context)

    else:
        form = AddCourseForm(department_id)
        context = {'form': form, 'title': 'Add New Course', 'course_list':course_list}
        return render(request, 'add_course.html', context)

def add_course_offering(request, course_id, daisy_chain):
# daisy_chain is "0" (False) or "1" (True) and says whether the page should advance to set up class schedules next, or just
# return to the "return_to_page".
    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
#    department_id = user_preferences.department_to_view.id
    academic_year_id = user_preferences.academic_year_to_view.id
    course = Course.objects.get(pk = course_id)

    if request.method == 'POST':
        form = CourseOfferingRestrictedByYearForm(academic_year_id, request.POST)
        if form.is_valid():

            semester = form.cleaned_data.get('semester')
            load_available = form.cleaned_data.get('load_available')
            max_enrollment = form.cleaned_data.get('max_enrollment')
            comment = form.cleaned_data.get('comment')
            new_course_offering = CourseOffering(course = course,
                                                 semester = semester,
                                                 load_available = load_available,
                                                 max_enrollment = max_enrollment,
                                                 comment = comment)
            new_course_offering.save()
            if not int(daisy_chain):
                if "return_to_page" in request.session:
                    next = request.session["return_to_page"]
                else:
                    next = "home"
                return redirect(next)
            else:
                url_string = '/planner/newclassschedule/'+str(new_course_offering.id)+'/1/'
                print url_string
                return redirect(url_string)
        else:
            context = {'form': form, 'course': course}
            return render(request, 'add_course_offering.html', context)

    else:
        form = CourseOfferingRestrictedByYearForm(academic_year_id)
        context = {'form': form, 'course': course}
        return render(request, 'add_course_offering.html', context)



@login_required
def update_course(request, id):

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department_id = user_preferences.department_to_view.id

    instance = Course.objects.get(pk = id)
    course_list=[]
    if request.method == 'POST':
        form = AddCourseForm(department_id, request.POST, instance=instance)
        if form.is_valid():
            form.save()
            next = request.GET.get('next', 'home')
            return redirect(next)
#            return redirect('course_summary')
        else:
            context = {'form': form, 'title': 'Edit Course', 'course_list':course_list}
            return render(request, 'add_course.html', context)
    else:
        form = AddCourseForm(department_id, instance=instance)
        context = {'form': form, 'title': 'Edit Course', 'course_list':course_list}
        return render(request, 'add_course.html', context)

@login_required
def delete_course_offering(request, id):

    if "return_to_page" in request.session:
        sending_page = request.session["return_to_page"]
    else:
        sending_page = "home"

    instance = CourseOffering.objects.get(pk = id)
    if request.method == 'POST':
        instance.delete()
        next = request.GET.get('next', 'department_load_summary')
        return redirect(next)
    else:
        scheduled_classes = instance.scheduled_classes.all()
        if len(scheduled_classes)==0:
            meetings_scheduled = False
            meeting_times_list = ["---"]
            room_list = ["---"]
        else:
            meetings_scheduled = True
            meeting_times_list, room_list = class_time_and_room_summary(scheduled_classes)
        counter = 0
        meeting_info = []
        for meeting_time in meeting_times_list:
            meeting_info.append({'times': meeting_times_list[counter], 'room': room_list[counter]})
            counter = counter+1

        context = {'title': 'Delete Course Offering', 'course_offering': instance, 
                   'meeting_info': meeting_info,'sending_page': sending_page}
        return render(request, 'delete_course_offering_confirmation.html', context)

#    return redirect('dept_load_summary')

@login_required
def delete_course_confirmation(request, id):
    course = Course.objects.get(pk = id)

    offering_list=[]
    for offering in course.offerings.all():
        offering_list.append(offering)

    context ={'course': course,'offering_list':offering_list}
    return render(request, 'delete_course_confirmation.html', context)

@login_required
def delete_course(request, id):
    instance = Course.objects.get(pk = id)
    instance.delete()
    url_string = '/planner/coursesummary/0/'
    return redirect(url_string)
#    return redirect('course_summary')

@login_required
def allow_delete_course_confirmation(request):
    context ={}
    return render(request, 'allow_delete_course_confirmation.html', context)

@login_required
def registrar_schedule(request, printer_friendly_flag):
    """Display courses in roughly the format used by the registrar"""
    # printer_friendly_flag == 0 => display the usual page
    # printer_friendly_flag == 1 => display the printer-friendly version in a new tab with small font
    # printer_friendly_flag == 2 => display the printer-friendly version in a new tab with larger font

    if int(printer_friendly_flag)==0:
        printer_friendly = False
        font_size_large = False
    else:
        printer_friendly = True
        if int(printer_friendly_flag)==2:
            font_size_large = True
        else:
            font_size_large = False

    request.session["return_to_page"] = "/planner/registrarschedule/0/"
    close_all_divs(request) # next time the dept load summary page is opened, all divs will be closed

    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view
    year_to_view = user_preferences.academic_year_to_view.begin_on.year

    academic_year_string = str(year_to_view)+'-'+str(year_to_view + 1)

    can_edit = False
    if user_preferences.permission_level == 1:
        can_edit = True

    registrar_data_list = []
    for semester in SemesterName.objects.all():
        for subject in department.subjects.all():
            for course in subject.courses.all():
                number = u"{0} {1}".format(course.subject, course.number)
                course_name = course.title

                for co in course.offerings.filter(Q(semester__name__name=semester.name)&Q(semester__year__begin_on__year=year_to_view)):
                    scheduled_classes=[]
                    instructor_list=[]
                    for instructor in co.offering_instructors.all():
                        instructor_list.append(instructor.instructor.first_name[:1]+' '+instructor.instructor.last_name+
                                               ' ['+str(load_hour_rounder(instructor.load_credit))+'/'
                                               +str(load_hour_rounder(co.load_available))+']'
                                               )
                    if len(instructor_list)==0:
                        instructor_list = ['TBA']

                    for sc in co.scheduled_classes.all():
                        scheduled_classes.append(sc)

                    if len(scheduled_classes)==0:
                        meetings_scheduled = False
                        meeting_times_list = ["---"]
                        room_list = ["---"]
                    else:
                        meetings_scheduled = True
                        meeting_times_list, room_list = class_time_and_room_summary(scheduled_classes)

                    registrar_data_list.append({'number':number,
                                                'name':course_name,
                                                'room_list': room_list,
                                                'meeting_times_list': meeting_times_list,
                                                'instructor_list': instructor_list,
                                                'cap': co.max_enrollment,
                                                'credit_hours': course.credit_hours,
                                                'course_id':course.id,
                                                'course_offering_id':co.id,
                                                'meetings_scheduled':meetings_scheduled,
                                                'semester':semester.name                                                
                                                })

    context={'registrar_data_list':registrar_data_list, 'department': department, 
             'academic_year': academic_year_string, 'can_edit': can_edit, 'id': user_preferences.id,
             'pagesize':'letter', 'printer_friendly': printer_friendly, 'font_size_large': font_size_large
    }

    if printer_friendly:
        context['base_html']='emptybase.html'
        return render_to_pdf(
            'registrar_schedule.html',
            context
        )
    else:
        context['base_html']='base.html'
        return render(request, 'registrar_schedule.html', context)

@login_required
def update_other_load(request, id):
    """Update amounts of load and/or professor for 'other' (administrative-type) loads."""

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    instance = OtherLoadType.objects.get(pk = id)
#    print instance

    dept_id = user_preferences.department_to_view.id
    year_to_view = user_preferences.academic_year_to_view.begin_on.year

    OtherLoadFormset = inlineformset_factory(OtherLoadType, OtherLoad, 
                                             formset = BaseOtherLoadFormset,
                                             extra = 2,
                                             exclude = 'load_type')
    OtherLoadFormset.form = staticmethod(curry(OtherLoadForm, department_id=dept_id, year_to_view=year_to_view))
    formset = OtherLoadFormset(instance=instance,queryset=OtherLoad.objects.filter(Q(instructor__department__id=dept_id)
                                                                                   & Q(semester__year__begin_on__year=year_to_view)))
    
    errordict={}
    dict = {"formset": formset,
            "instance": instance,
            "other_load_type": instance,
            "errordict": errordict
            }

    if request.method == 'POST':
        formset = OtherLoadFormset(request.POST, instance=instance)
        formset.is_valid()
        formset_error=formset.non_form_errors()

        if formset.is_valid() and not formset_error:
            formset.save()
            next = request.GET.get('next', 'home')
            return redirect(next)
        else:
            dict["formset"]=formset
            if formset_error:
                errordict.update({'formset_error':formset_error})
            for subform in formset:
                if subform.errors:
                    errordict.update(subform.errors)

            return render(request, 'update_other_load.html', dict)

    else:
        return render(request, 'update_other_load.html', dict)

@login_required
def update_rooms_to_view_old(request, id):

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department_id = user_preferences.department_to_view.id

    instance = UserPreferences.objects.get(pk = id)

    if request.method == 'POST':
        form = UpdateRoomsToViewForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            next = request.GET.get('next', 'home')
            return redirect(next)
        else:
            return render(request, 'update_rooms_to_view_old.html', {'form': form})
    else:
        form = UpdateRoomsToViewForm(instance=instance)
        context = {'form': form}
        return render(request, 'update_rooms_to_view_old.html', context)


@login_required
def update_rooms_to_view(request, id):

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department = user_preferences.department_to_view
    year = user_preferences.academic_year_to_view
    rooms_to_view = user_preferences.rooms_to_view.all()

    if request.method == 'POST':
        rooms_to_display_id_list = request.POST.getlist('rooms_to_display')
        user_preferences.rooms_to_view.clear()
        for room_id in rooms_to_display_id_list:
            room = Room.objects.get(pk=room_id)
            user_preferences.rooms_to_view.add(room)
        next = request.GET.get('next', 'home')
        return redirect(next)
    else:
        buildings=Building.objects.all()
        room_info = []
        rooms_in_use = []
        rooms_not_in_use = []
        for building in buildings:
            room_list = []
            for room in building.rooms.all():
                in_use = room.classes_scheduled(year, department)
                if in_use:
                    rooms_in_use.append(room.id)
                else:
                    rooms_not_in_use.append(room.id)
                if room in rooms_to_view:
                    view_this_room = True
                else:
                    view_this_room = False
                room_list.append({'room': room, 'in_use': in_use, 'view_this_room': view_this_room})
            room_info.append({
                'building': building,
                'rooms': room_list,
            })

        json_rooms_in_use = json.dumps(rooms_in_use)
        json_rooms_not_in_use = json.dumps(rooms_not_in_use)
        context = {'room_info': room_info,
                   'json_rooms_in_use': json_rooms_in_use,
                   'json_rooms_not_in_use': json_rooms_not_in_use}
        
        return render(request, 'update_rooms_to_view.html', context)

    
@login_required
def update_faculty_to_view_old(request, id):

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department_id = user_preferences.department_to_view.id

    instance = UserPreferences.objects.get(pk = id)

    if request.method == 'POST':
        form = UpdateFacultyToViewForm(department_id, request.POST, instance=instance)
        if form.is_valid():
            form.save()
            next = request.GET.get('next', 'home')
            return redirect(next)
        else:
            return render(request, 'update_faculty_to_view.html', {'form': form})
    else:
        form = UpdateFacultyToViewForm(department_id, instance=instance)
        print form
        context = {'form': form}
        return render(request, 'update_faculty_to_view_old.html', context)

@login_required
def update_faculty_to_view(request, id):

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department = user_preferences.department_to_view
    year = user_preferences.academic_year_to_view
    faculty_to_view = user_preferences.faculty_to_view.all()

    if request.method == 'POST':
        faculty_to_display_id_list = request.POST.getlist('faculty_to_display')
        user_preferences.faculty_to_view.clear()
        for faculty_id in faculty_to_display_id_list:
            faculty = FacultyMember.objects.get(pk=faculty_id)
            user_preferences.faculty_to_view.add(faculty)
        next = request.GET.get('next', 'home')
        return redirect(next)
    else:
        all_faculty=FacultyMember.objects.filter(department=department)
        
        faculty_info = []
        faculty_with_loads = []
        faculty_without_loads = []
        for faculty in all_faculty:
            total_load = load_hour_rounder(faculty.load(year))
            if total_load > 0:
                has_load = True
                faculty_with_loads.append(faculty.id)
            else:
                has_load = False
                faculty_without_loads.append(faculty.id)
#            json_bls = json.dumps(budget_lines_with_subaccounts)
            if faculty in faculty_to_view:
                view_this_faculty = True
            else:
                view_this_faculty = False
            faculty_info.append({
                'faculty': faculty,
                'view_this_faculty': view_this_faculty,
                'load': total_load,
                'has_load': has_load
            })

        json_faculty_with_loads = json.dumps(faculty_with_loads)
        json_faculty_without_loads = json.dumps(faculty_without_loads)
        context = {'faculty_info': faculty_info,
                   'json_faculty_with_loads': json_faculty_with_loads,
                   'json_faculty_without_loads': json_faculty_without_loads}
        return render(request, 'update_faculty_to_view.html', context)

    
@login_required
def update_department_to_view(request):
    """
    Allows a super-user (only) to change which department they are looking at.
    """
    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department_id = user_preferences.department_to_view.id

    instance = user_preferences

# only a superuser can change his/her department to view.
    if user_preferences.permission_level != 2:
        return redirect('home')

    if request.method == 'POST':
        form = UpdateDepartmentToViewForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            user_preferences = user.user_preferences.all()[0]
# update preferences to remove faculty members from old department and add in all faculty members from new dept
            faculty_list = user_preferences.faculty_to_view.all()
            for faculty in faculty_list:
                user_preferences.faculty_to_view.remove(faculty)
            new_dept = user_preferences.department_to_view
            faculty_list = new_dept.faculty.all()
            for faculty in faculty_list:
                user_preferences.faculty_to_view.add(faculty)
            next = request.GET.get('next', 'home')
            return redirect(next)
        else:
            return render(request, 'update_faculty_to_view.html', {'form': form})
    else:
        form = UpdateDepartmentToViewForm(instance=instance)
        context = {'form': form}
        return render(request, 'update_department_to_view.html', context)

@login_required
def update_year_to_view(request, id):

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department_id = user_preferences.department_to_view.id

    instance = UserPreferences.objects.get(pk = id)

    if request.method == 'POST':
        form = UpdateYearToViewForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            next = request.GET.get('next', 'home')
            return redirect(next)
        else:
            return render(request, 'update_year_to_view.html', {'form': form})
    else:
        form = UpdateYearToViewForm(instance=instance)
        context = {'form': form}
        return render(request, 'update_year_to_view.html', context)

@login_required
def update_loads_to_view(request, id):

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department_id = user_preferences.department_to_view.id

    instance = UserPreferences.objects.get(pk = id)

    if request.method == 'POST':
        form = UpdateLoadsToViewForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            next = request.GET.get('next', 'home')
            return redirect(next)
        else:
            return render(request, 'update_loads_to_view.html', {'form': form})
    else:
        form = UpdateLoadsToViewForm(instance=instance)
        context = {'form': form}
        return render(request, 'update_loads_to_view.html', context)


@login_required
def copy_courses(request, id, check_all_flag):

    if "return_to_page" in request.session:
        next = request.session["return_to_page"]
    else:
        next = "home"

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department = user_preferences.department_to_view

    academic_year_copy_from = AcademicYear.objects.get(pk = id)
    academic_year_copy_to = user_preferences.academic_year_to_view
    faculty_to_view = user_preferences.faculty_to_view.all()

#    print academic_year_copy_from
#    print academic_year_copy_to
    if check_all_flag == '0':
        check_all = False
        check_all_flag_table = 1
    else:
        check_all = True
        check_all_flag_table = 0
    
    if request.method == 'POST':
        course_offerings_to_copy_id_list = request.POST.getlist('courses_to_copy')
        for co_id in course_offerings_to_copy_id_list:
            co = CourseOffering.objects.get(pk = co_id)

            semester_name = co.semester.name
            semester_object_copy_to = Semester.objects.get(Q(name=semester_name)&Q(year=academic_year_copy_to))

            new_co = CourseOffering.objects.create(course = co.course,
                                                   semester = semester_object_copy_to,
                                                   load_available = co.load_available,
                                                   max_enrollment = co.max_enrollment,
                                                   comment = co.comment
                                                   )
            new_co.save()

            for instructor in co.offering_instructors.all():
                # NOTE: instructors are only assigned to courses if they are currently listed as being "viewable"
                if instructor.instructor in faculty_to_view:
                    new_offering_instructor = OfferingInstructor.objects.create(course_offering = new_co,
                                                                                instructor = instructor.instructor,
                                                                                load_credit = instructor.load_credit
                                                                                )
                    new_offering_instructor.save()

            for sc in co.scheduled_classes.all():
                schedule_addition = ScheduledClass.objects.create(course_offering = new_co,
                                                                  day = sc.day,
                                                                  begin_at = sc.begin_at,
                                                                  end_at = sc.end_at,
                                                                  room = sc.room,
                                                                  comment = sc.comment
                                                                  )
                schedule_addition.save()

#        next = request.GET.get('next', 'profile')
        return redirect(next)
    else:
        missing_instructor = False
        data_list = []
        comment_list = []
        for subject in department.subjects.all():
            for course in subject.courses.all():
                for course_offering in course.offerings.filter(semester__year = academic_year_copy_from):
                    course_offerings_current_year = course.offerings.filter(Q(semester__year = academic_year_copy_to)&
                                                                            Q(semester__name = course_offering.semester.name))
                    instructor_list=[]
                    note_list=[]
                    missing_instructor_this_course = False
                    for faculty in course_offering.offering_instructors.all():
                        if faculty.instructor in faculty_to_view:
                            instructor_list.append(faculty.instructor.last_name)
                        else:
                            instructor_list.append("("+faculty.instructor.last_name+")")
                            missing_instructor = True
                            missing_instructor_this_course = True
                    if missing_instructor_this_course:
                        note_list.append("missing instructor")

                    scheduled_classes = course_offering.scheduled_classes.all()
                    if len(scheduled_classes)==0:
                        meetings_scheduled = False
                        meeting_times_list = ["---"]
                        room_list = ["---"]
                    else:
                        meetings_scheduled = True
                        meeting_times_list, room_list = class_time_and_room_summary(scheduled_classes)
# now try to find "collisions" between current course offerings (in the "copy to" year) and
# the course offerings in the year being copied from
                    scheduled_classes_current_year=[]
                    for cocy in course_offerings_current_year:
                        for sc in cocy.scheduled_classes.all():
                            scheduled_classes_current_year.append(sc)
# at this point, scheduled_classes and scheduled_classes_current_year are both arrays of "ScheduledClass"
# objects; one has the classes from the "copy from" year and one from the "copy to" year; now those need
# to be compared to see if there is any overlap
                    course_offering_already_exists = scheduled_classes_overlap(scheduled_classes, scheduled_classes_current_year)
#                    if course_offering_already_exists:
#                        note_list.append("similar schedule exists")

                    data_list.append({'instructors':instructor_list,
                                      'room_list': room_list,
                                      'meeting_times': meeting_times_list,
                                      'meetings_scheduled': meetings_scheduled,
                                      'id':course_offering.id,
                                      'note_list': note_list,
                                      'exists':course_offering_already_exists,
                                      'number':course_offering.course.subject.abbrev+' '+course_offering.course.number,
                                      'name':course_offering.course.title,
                                      'semester':course_offering.semester.name
                                      })
        if missing_instructor:
            comment_list.append("One or more instructors is missing from the current academic year and will not be included in a course copy.  If this is unintentional, you can add instructors back in under Profile.")
            
#        form = CoursesToCopyForm(['heythere'])
#        print 'got here'
#        print(form.as_table())
        context = {'data_list': data_list, 'comment_list': comment_list, 
                   'academic_year_copy_from':academic_year_copy_from,
                   'academic_year_copy_to':academic_year_copy_to, 
                   'check_all': check_all, 'check_all_flag_table':check_all_flag_table, 'year_id': id}
        return render(request, 'copy_courses.html', context)

def scheduled_classes_overlap(sclist1, sclist2):
    """
    Compares sclist1 and sclist2, which are lists of ScheduledClass objects, 
    to see if there is any overlap in the schedules.  If there is no overlap
    or if one of the lists is empty, returns False; if there is an overlap,
    returns True.
    """
    if len(sclist1) == 0 or len(sclist2) == 0:
        return False

    day_schedules1 = {0:[], 1:[], 2:[], 3:[], 4:[]}
    for sc1 in sclist1:
        day_schedules1[sc1.day].append([convert_military_time(sc1.begin_at),convert_military_time(sc1.end_at)])

    for sc2 in sclist2:
        begin2 = convert_military_time(sc2.begin_at)
        end2 = convert_military_time(sc2.end_at)
        for time_block in day_schedules1[sc2.day]:
            begin1 = time_block[0]
            end1 = time_block[1]
            if ((begin1 < end2) and (begin1 > begin2)) or ((end1 < end2) and (end1 > begin2)) or ((begin1 <= begin2) and (end1 >= end2)):
                return True
    return False


def convert_military_time(time_object):
    return time_object.hour*100+time_object.minute


@login_required
def choose_year_course_copy(request):

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department = user_preferences.department_to_view

    academic_year_copy_to = user_preferences.academic_year_to_view
    academic_years = AcademicYear.objects.all()
    
    year_list =[]
    for year in academic_years:
        if year.begin_on.year < academic_year_copy_to.begin_on.year:
            year_list.append({
                    'year_name':year,
                    'year_id':year.id
                    })

    context = {'year_list': year_list}
    return render(request, 'choose_year_course_copy.html', context)

@login_required
def search_form(request):
    """
    Allows the user to search for offerings of one or more courses.
    """
    close_all_divs(request)
    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view
    faculty_to_view = user_preferences.faculty_to_view.all()
    
    request.session["return_to_page"] = "/planner/search-form/"

    current_year = academic_year.begin_on.year
    academic_year_list = []
    for ii in range(4):
        ay = current_year-2+ii
        year_name = str(ay)+'-'+str(ay+1)
        academic_year_list.append({'year_name':year_name,
                                   'id': ii,
                                   'begin_on':ay})
    
    if request.method == 'POST':
        search_term = request.POST.getlist('course_search')[0]
        year_begin_on_list= request.POST.getlist('years_for_search')
        academic_year_short_list = []
        for year in year_begin_on_list:
            academic_year_short_list.append(int(year))

        # first, assume that the text is part of the course title....
        if len(search_term)>0:
            course_list_1 = Course.objects.filter(title__icontains =search_term)
        else:
            course_list_1 = []
        # now assume that it might be of the form 'PHY 493'....
        split_array = search_term.split()
        if len(split_array) == 0:
            course_list_2 = []
        elif len(split_array) == 1:
            # assume it is the subject....
            subj = split_array[0]
            course_list_2 = Course.objects.filter(subject__abbrev__icontains = subj)
        else:
            subj = split_array[0]
            number = split_array[1]
            course_list_2 = Course.objects.filter(Q(subject__abbrev__icontains = subj)&
                                                  Q(number__icontains = number))
        
        # WORKING HERE -------- now, find all offerings for the courses for the given year, and list those

        # create complete list of course objects
        course_list = []
        for course in course_list_1:
            course_list.append(course)

        for course in course_list_2:
            course_list.append(course)

        course_offering_list = []
        for year in academic_year_short_list:
            for course in course_list:
                for course_offering in course.offerings.all():
                    if course_offering.semester.year.begin_on.year == year:
                        can_edit = False
                        if user_preferences.permission_level == 1 and year == current_year and course.subject.department==department:
                            can_edit = True
                        elif user_preferences.permission_level == 2 and year == current_year:
                            can_edit = True

                        scheduled_classes = course_offering.scheduled_classes.all()
                        if len(scheduled_classes)==0:
                            meetings_scheduled = False
                            meeting_times_list = ["---"]
                            room_list = ["---"]
                        else:
                            meetings_scheduled = True
                            meeting_times_list, room_list = class_time_and_room_summary(scheduled_classes)

                        course_offering_list.append({'name':course.title, 
                                                     'number': course.subject.abbrev+' '+course.number,
                                                     'course_id':course.id,
                                                     'offering_id':course_offering.id,
                                                     'semester':course_offering.semester,
                                                     'rooms':room_list,
                                                     'meeting_times':meeting_times_list,
                                                     'meetings_scheduled':meetings_scheduled,
                                                     'can_edit':can_edit
                                                     })

        context = {'search_term': search_term, 'course_offering_list':course_offering_list,
                   'next':'search-form'}
        return render(request, 'search_results.html', context)
    else:
        context = {'academic_year': academic_year, 
                   'academic_year_list':academic_year_list}
        return render(request, 'search_form.html', context)

@login_required
def search_form_time(request):
    """
    Allows the user to search for offerings of one or more courses.
    """
    close_all_divs(request)
    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view
    faculty_to_view = user_preferences.faculty_to_view.all()

    request.session["return_to_page"] = "/planner/search-form-time/"

    all_depts_list = []
    for dept in Department.objects.all().order_by('name'):
        all_depts_list.append({'name':dept.name,'id':dept.id})

    current_year = academic_year.begin_on.year

    semesters_all = Semester.objects.all()
    semester_list = []
    ii = 0
    for semester in semesters_all:
        if (semester.year.begin_on.year >= current_year-2) and (semester.year.begin_on.year <= current_year+1):
            ii = ii+1
            semester_list.append({'name':semester.name.name+' '+str(semester.year.begin_on.year)+'-'+str(semester.year.end_on.year),
                                  'id':semester.id})
    
    if request.method == 'POST':
        depts_for_search= request.POST.getlist('depts_for_search')
        start_hour_string= request.POST.getlist('start_time')[0]
        time_interval= request.POST.getlist('time_interval')[0]
        days_for_search = request.POST.getlist('days_for_search')
        semester_id = int(request.POST.getlist('semester')[0])
        semester = Semester.objects.get(pk = semester_id)
        year_for_search = semester.year.begin_on.year
        
        day_dict={0:'M',1:'T',2:'W',3:'R',4:'F'}
        day_string = ''
        day_list=[]
        for day in days_for_search:
            day_list.append(int(day))
            day_string=day_string+day_dict[int(day)]

        start_time = int(start_hour_string)*100+0
        num_hours=int(time_interval)/60
        num_minutes=int(time_interval)-num_hours*60
        end_time = start_time + num_hours*100+num_minutes

        start_string = start_hour_string+':00'
        end_string = str(int(start_hour_string)+num_hours)+':'+str(num_minutes)

        course_offering_list=[]
        for dept_id in depts_for_search:
            course_list = Course.objects.filter(subject__department__id = int(dept_id))
            for course in course_list:
                for course_offering in course.offerings.filter(semester__id = semester_id):
                    can_edit = False
                    if user_preferences.permission_level == 1 and year_for_search == current_year and course.subject.department==department:
                        can_edit = True
                    elif user_preferences.permission_level == 2 and year_for_search == current_year:
                        can_edit = True

                    scheduled_classes = course_offering.scheduled_classes.all()
                    meeting_in_interval_and_day_in_list = False
                    for meeting in scheduled_classes:
                        meeting_start = meeting.begin_at.hour*100+meeting.begin_at.minute
                        meeting_end = meeting.end_at.hour*100+meeting.end_at.minute
                        if (meeting.day in day_list) and (time_blocks_overlap([[meeting_start,meeting_end],[start_time,end_time]])):
                            meeting_in_interval_and_day_in_list = True

                    if meeting_in_interval_and_day_in_list:
                        if len(scheduled_classes)==0:
                            meetings_scheduled = False
                            meeting_times_list = ["---"]
                            room_list = ["---"]
                        else:
                            meetings_scheduled = True
                            meeting_times_list, room_list = class_time_and_room_summary(scheduled_classes)

                        course_offering_list.append({'name':course.title, 
                                                     'number': course.subject.abbrev+' '+course.number,
                                                     'course_id':course.id,
                                                     'offering_id':course_offering.id,
                                                     'semester':course_offering.semester,
                                                     'rooms':room_list,
                                                     'meeting_times':meeting_times_list,
                                                     'meetings_scheduled':meetings_scheduled,
                                                     'can_edit':can_edit
                                                     })
        
        search_details = 'courses in '+semester.name.name+' '+str(semester.year.begin_on.year)+'-'+str(extract_two_digits(semester.year.begin_on.year+1))+' that occur between '+start_string+' and '+end_string+' on the following day(s): '+day_string
        context = {'search_term': search_details, 'course_offering_list':course_offering_list,
                   'next':'search-form-time'}
        return render(request, 'search_results.html', context)
    else:
        start_time_list=[]
        for time in range(7,20):
            start_time_list.append(time)

        context = {'academic_year': academic_year, 
                   'semester_list':semester_list,
                   'start_time_list':start_time_list,
                   'dept_list':all_depts_list}
        return render(request, 'search_form_time.html', context)

@login_required
def export_summary_data(request):
    """Exports a summary of teaching load data to an Excel file."""
    close_all_divs(request)
    context = collect_data_for_summary(request)

    file_name = 'DepartmentLoadSummary.xls'

    book = prepare_excel_summary(context)
    response = HttpResponse(mimetype="application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    book.save(response)
    return response

def prepare_excel_summary(context):
    """
    Prepares an Excel file containing a summary of department loads
    """

############ NEXT:  make grey a bit lighter somehow; add some boxes and lines

    one_inch = 3333
    styles = dict(
        bold = 'font: bold 1',
        italic = 'font: italic 1',
        # Wrap text in the cell
        wrap_bold = 'font: bold 1; align: wrap 1;',
        # White text on a blue background
        reversed = 'pattern: pattern solid, fore_color blue; font: color white;',
        # Light orange checkered background
        light_orange_bg = 'pattern: pattern fine_dots, fore_color white, back_color orange;',
        # Heavy borders
        bordered = 'border: top thick, right thick, bottom thick, left thick;',
        # 16 pt red text
        big_red = 'font: height 320, color red;',
        calibri_font = 'font: height 220, color black, name Calibri;',
        calibri_bold_bordered = 'font: height 220, color black, name Calibri, bold 1;border: top thin, right thin, bottom thin, left thin;',
        calibri_bordered = 'font: height 220, color black, name Calibri;border: top thin, right thin, bottom thin, left thin;',
        calibri_bold_bordered_centered = 'alignment: horizontal center; font: height 220, color black, name Calibri, bold 1;border: top thin, right thin, bottom thin, left thin;',
        calibri_bold_bordered_right = 'alignment: horizontal right; font: height 220, color black, name Calibri, bold 1;border: top thin, right thin, bottom thin, left thin;',
        calibri_centered_left_line = 'font: height 220, color black, name Calibri; alignment:horizontal center, vertical top; border: left thin;',
        calibri_centered_grey_left_line = 'font: height 220, color black, name Calibri; alignment:horizontal center, vertical top; pattern: pattern solid, fore_color 22; border: left thin;',
        calibri_centered_right_line = 'font: height 220, color black, name Calibri; alignment:horizontal center, vertical top; border: right thin;',
        calibri_centered_grey_right_line = 'font: height 220, color black, name Calibri; alignment:horizontal center, vertical top; pattern: pattern solid, fore_color 22; border: right thin;',
        calibri_centered = 'font: height 220, color black, name Calibri; alignment:horizontal center, vertical top;',
        calibri_centered_grey = 'font: height 220, color black, name Calibri; alignment:horizontal center, vertical top; pattern: pattern solid, fore_color 22;',
        calibri_left = 'font: height 220, color black, name Calibri; alignment:horizontal left, vertical top; border: left thin;',
        calibri_left_grey = 'font: height 220, color black, name Calibri; alignment:horizontal left, vertical top; border: left thin; pattern: pattern solid, fore_color 22;',
        calibri_right = 'font: height 220, color black, name Calibri; alignment:horizontal right;',
        bold_title = 'alignment:horizontal left; font: height 240, color black, name Calibri, bold 1;',
        bold_title_centered = 'alignment:horizontal center; font: height 240, color black, name Calibri, bold 1;',
        bold_title_right = 'alignment:horizontal right; font: height 240, name Calibri, bold 1;',
        calibri_centered_top_line = 'font: height 220, color black, name Calibri; alignment:horizontal center, vertical top; border: top thin;',
        )


    row_data_start = 3
    col_data_start = 7

    first_char_dict = {0:'',1:'A',2:'B',3:'C',4:'D',5:'E',6:'F'}
    second_char_dict = dict()
    for num in range(26):
        second_char_dict[num]=chr(ord('A')+num)

    num_profs = len(context['instructor_list'])
    counter = 0
    first_char_counter = 0
    col_dict = dict()
    for num in range(num_profs*3+col_data_start):
        if counter == 26:
            counter = 0
            first_char_counter = first_char_counter+1
            
        col_dict[num]=first_char_dict[first_char_counter]+second_char_dict[counter]
        counter = counter + 1

    column_widths = [int(0.7*one_inch),
                     int(2.3*one_inch),
                     int(0.7*one_inch),
                     int(1.3*one_inch),
                     int(0.8*one_inch),
                     int(0.4*one_inch),
                     int(0.4*one_inch)]

    # note: row heights are set automatically by the font size
    
    book = xlwt.Workbook()
    style_calibri_bordered = xlwt.easyxf(styles['calibri_bordered'])
    style_calibri_bordered_grey = xlwt.easyxf(styles['calibri_bordered']+'pattern: pattern solid, fore_color 22')
    style_calibri_centered = xlwt.easyxf(styles['calibri_centered'])
    style_calibri_centered_grey = xlwt.easyxf(styles['calibri_centered_grey'])
    style_calibri_centered_left_line = xlwt.easyxf(styles['calibri_centered_left_line'])
    style_calibri_centered_grey_left_line = xlwt.easyxf(styles['calibri_centered_grey_left_line'])
    style_calibri_centered_right_line = xlwt.easyxf(styles['calibri_centered_right_line'])
    style_calibri_centered_grey_right_line = xlwt.easyxf(styles['calibri_centered_grey_right_line'])
    style_calibri_bold_bordered = xlwt.easyxf(styles['calibri_bold_bordered_centered'])
    style_calibri_bold_bordered_right = xlwt.easyxf(styles['calibri_bold_bordered_right'])
    style_calibri_left=xlwt.easyxf(styles['calibri_left'])
    style_calibri_left_grey=xlwt.easyxf(styles['calibri_left_grey'])
    style_calibri_right=xlwt.easyxf(styles['calibri_right'])
    style_bold_right=xlwt.easyxf(styles['bold_title_right'])
    style_top_line=xlwt.easyxf(styles['calibri_centered_top_line'])
    
    style_wrap=style_calibri_centered_left_line
    style_wrap.alignment.wrap = 1

    style_wrap_grey=style_calibri_centered_grey_left_line
    style_wrap_grey.alignment.wrap = 1

    sheet = book.add_sheet('dept load summary')

    col = 0
    for width in column_widths:
        sheet.col(col).width = width
        col = col+1
        
    sheet.write_merge(0,0,0,6,'Load Summary -- Department of '+context['department'].name+' ('+context['academic_year']+')',xlwt.easyxf(styles['bold_title']))
    sheet.write(2,0,'Number',style_calibri_bold_bordered)
    sheet.write(2,1,'Name',style_calibri_bold_bordered)
    sheet.write(2,2,'Semester',style_calibri_bold_bordered)
    sheet.write(2,3,'Time',style_calibri_bold_bordered)
    sheet.write(2,4,'Room',style_calibri_bold_bordered)
    sheet.write(2,5,'Load',style_calibri_bold_bordered)
    sheet.write(2,6,'Diff',style_calibri_bold_bordered)

    style_center_list=[style_calibri_centered,style_calibri_centered_grey]
    style_center_left_line_list=[style_calibri_centered_left_line,style_calibri_centered_grey_left_line]
    style_center_right_line_list=[style_calibri_centered_right_line,style_calibri_centered_grey_right_line]
    style_left_list=[style_calibri_left,style_calibri_left_grey]
    style_center_wrap_list=[style_wrap,style_wrap_grey]

    j = 0
    for instructor in context['instructor_list']:
        sheet.col(col_data_start+3*j).width = int(0.4*one_inch)
        sheet.col(col_data_start+3*j+1).width = int(0.4*one_inch)
        sheet.col(col_data_start+3*j+2).width = int(0.4*one_inch)
        sheet.write_merge(2,2,col_data_start+3*j,col_data_start+3*j+2,instructor,style_calibri_bold_bordered)
        j = j+1

    sheet.col(col_data_start+3*j).width = int(1.5*one_inch)
    sheet.write(2,col_data_start+3*j,'Comments',style_calibri_bold_bordered)

    i = 0
    data_list = context['course_data_list']
    for entry in data_list:
        row=row_data_start+i
        style_center = style_center_list[(i+1)%2]
        style_center_left_line = style_center_left_line_list[(i+1)%2]
        style_center_right_line = style_center_right_line_list[(i+1)%2]
        style_center_wrap = style_center_wrap_list[(i+1)%2]
        style_left = style_left_list[(i+1)%2]

        sheet.write(row,0,entry['number'],style_left)
        sheet.write(row,1,entry['name'],style_left)
        sheet.write(row,2,entry['semester'],style_center_left_line)
        sheet.write(row,5,entry['load_hours'],style_center_left_line)
#        if entry['load_difference']<0:
#            sheet.write(row,6,entry['load_difference'],style_bold_centered_red)
#        elif entry['load_difference']>0:
#            sheet.write(row,6,entry['load_difference'],style_calibri_centered)

        time_list = ''
        for time in entry['meeting_times']:
            if time_list=='':
                time_list = time
            else:
                time_list = time_list+'\n'+time
        sheet.write(row,3,time_list,style_center_wrap)

        room_list = ''
        for room in entry['rooms']:
            if room_list=='':
                room_list = room
            else:
                room_list = room_list+'\n'+room
        sheet.write(row,4,room_list,style_center_wrap)

        j = 0
        temp_list = entry['load_hour_list'][:]

        for load in temp_list:
            loads_to_write=['','','']
            if load[0]>=0:
                loads_to_write[load[1]] = load[0]
            for kk in range(3):
                if kk == 0:
                    sheet.write(row,col_data_start+3*j+kk,loads_to_write[kk],style_center_left_line)
                elif kk == 1:
                    sheet.write(row,col_data_start+3*j+kk,loads_to_write[kk],style_center)
                else:
                    sheet.write(row,col_data_start+3*j+kk,loads_to_write[kk],style_center_right_line)
            j=j+1

        sheet.write(row,col_data_start+3*j,entry['comment'],style_center_right_line)

        sum_string = 'F'+str(row+1)+'-SUM('+col_dict[col_data_start]+str(row+1)+':'+col_dict[col_data_start+3*num_profs-1]+str(row+1)+')'
        sheet.write(row_data_start+i,6,xlwt.Formula(sum_string),style_center_left_line)

        i=i+1

    data_list = context['admin_data_list']
    for entry in data_list:
        style_center = style_center_list[(i+1)%2]
        style_center_left_line = style_center_left_line_list[(i+1)%2]
        style_center_right_line = style_center_right_line_list[(i+1)%2]
        style_center_wrap = style_center_wrap_list[(i+1)%2]
        style_left = style_left_list[(i+1)%2]

        row=row_data_start+i
        sheet.write(row,0,'',style_left)
        sheet.write(row,1,entry['load_type'],style_left)
        sheet.write(row,2,'',style_left)
        sheet.write(row,3,'',style_left)
        sheet.write(row,4,'',style_left)
        sheet.write(row,5,'',style_left)
        sheet.write(row,6,'',style_left)
        j = 0
        temp_list = entry['load_hour_list'][:]
        for load in temp_list:
            kk = 0
            for load_entry in load:
                if load_entry > 0:
                    load_to_write = load_entry
                else:
                    load_to_write = ''
                if kk == 0:
                    sheet.write(row,col_data_start+3*j+kk,load_to_write,style_center_left_line)
                elif kk == 1:
                    sheet.write(row,col_data_start+3*j+kk,load_to_write,style_center)
                else:
                    sheet.write(row,col_data_start+3*j+kk,load_to_write,style_center_right_line)
                kk = kk+1
            j=j+1
        sheet.write(row,col_data_start+3*j,'',style_center_right_line)
        i=i+1

    for j in range(num_profs*3):
        sum_string = 'SUM('+col_dict[col_data_start+j]+str(row_data_start+1)+':'+col_dict[col_data_start+j]+str(row_data_start+i)+')'
        sheet.write(row_data_start+i,col_data_start+j,xlwt.Formula(sum_string),style_calibri_bold_bordered)

    sheet.write_merge(row_data_start+i,row_data_start+i,0,6,'Load Summary',style_calibri_bold_bordered_right)
    sheet.write(row_data_start+i,col_data_start+3*num_profs,'',style_top_line)

    i=i+1

    for j in range(num_profs):
        sum_string = 'SUM('+col_dict[col_data_start+3*j]+str(row_data_start+i)+':'+col_dict[col_data_start+3*j+2]+str(row_data_start+i)+')'
        sheet.write_merge(row_data_start+i,row_data_start+i,col_data_start+3*j,col_data_start+3*j+2,xlwt.Formula(sum_string),style_calibri_bold_bordered)

    sheet.write_merge(row_data_start+i,row_data_start+i,0,6,'Total',style_calibri_bold_bordered_right)
    i=i+1

    j = 0
    for instructor in context['instructor_list']:
        sheet.write_merge(row_data_start+i,row_data_start+i,col_data_start+3*j,col_data_start+3*j+2,instructor,style_calibri_bold_bordered)
        j = j+1

    return book







@login_required
def getting_started(request):
    """
    Sends user to the help page.
    """
    close_all_divs(request)
    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view
    faculty_to_view = user_preferences.faculty_to_view.all()

    return render(request, 'getting_started.html')

@login_required
def weekly_course_schedule_entire_dept(request):
    """Display weekly schedules for the entire department"""
    close_all_divs(request)
    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view.begin_on.year
    academic_year_string = str(academic_year)+'-'+str(academic_year+1)

# things that are currently hard-coded and could/should be fixed:
# - earliest course is 7 a.m.
# - hard-coded the semester "exclusion" list...could pass it instead
#
# NEED TO CHECK FOR COURSE TIME CONFLICTS!!!!!!!
#

    semester_names_to_exclude = [u'Summer']

    semester_list = []
    for semester in SemesterName.objects.all():
        if semester.name not in semester_names_to_exclude:
            semester_list.append(semester.name)

    num_data_columns = 5

    data_list =[]
    idnum = 0

    day_list = ['Monday','Tuesday','Wednesday','Thursday','Friday']
    day_dict = {'Monday':0, 'Tuesday':1, 'Wednesday':2, 'Thursday':3, 'Friday':4}

    chapel_dict = {'Monday':'every', 'Tuesday':'none', 'Wednesday':'every', 'Thursday':'none', 'Friday':'every'}
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

# ---working here--- NEXT: dump the results from the instructor conflict check out to the template; check for room conflicts, too


    for semester_name in semester_list:
        instructor_conflict_check_dict = {}
        room_conflict_check_dict = {}
        for faculty_member in user_preferences.faculty_to_view.filter(department=department):
            instructor_conflict_check_dict[faculty_member.id] = {'Monday':[], 'Tuesday':[], 'Wednesday':[], 'Thursday':[], 'Friday':[]}
#        for room in user_preferences.rooms_to_view.all().order_by('building','number'):
#            room_conflict_check_dict[room.id] = {'Monday':[], 'Tuesday':[], 'Wednesday':[], 'Thursday':[], 'Friday':[]}

        idnum = idnum+1
        courses_after_five = False
        if semester_name == semester_list[0]:
            current_semester_string = semester_name+', '+str(academic_year)
            table_title = department.name +' ('+semester_name+', '+str(academic_year)+')'
        else:
            current_semester_string = semester_name+', '+str(academic_year+1)
            table_title = department.name +' ('+semester_name+', '+str(academic_year+1)+')'

        master_dict={}
        num_lines_in_hour={7:0,8:0,9:0,10:0,11:0,12:0,13:0,14:0,15:0,16:0,17:0,18:0,19:0,20:0,21:0}
        num_lines_including_halves={7:0,8:0,9:0,10:0,11:0,12:0,13:0,14:0,15:0,16:0,17:0,18:0,19:0,20:0,21:0}
        for day in day_list:
            master_dict[day]={7:[],8:[],9:[],10:[],11:[],12:[],13:[],14:[],15:[],16:[],17:[],18:[],19:[],20:[],21:[]}

# master_dict contains the text that will be displayed in the various boxes
            for sc in ScheduledClass.objects.filter(Q(day=day_dict[day])&
                                                    Q(course_offering__semester__name__name=semester_name)&
                                                    Q(course_offering__semester__year__begin_on__year = academic_year)&
                                                    Q(course_offering__course__subject__department = department)):

                data_this_class=[sc.course_offering.course.subject.abbrev+sc.course_offering.course.number+' - '+
                                 sc.room.building.abbrev+sc.room.number]

                for instructor in sc.course_offering.instructor.all():
                    if instructor.id not in instructor_conflict_check_dict.keys():
                        instructor_conflict_check_dict[instructor.id] = {'Monday':[], 'Tuesday':[], 'Wednesday':[], 'Thursday':[], 'Friday':[]}
                    instructor_conflict_check_dict[instructor.id][day_list[sc.day]].append([sc.begin_at.hour*100+sc.begin_at.minute,
                                                                                  sc.end_at.hour*100+sc.end_at.minute,
                                                                                  sc.course_offering.course.subject.abbrev+sc.course_offering.course.number+
                                                                                            ' ('+start_end_time_string(sc.begin_at.hour,
                                                                                                                       sc.begin_at.minute,sc.end_at.hour,sc.end_at.minute)+')'])
                if sc.room.id not in room_conflict_check_dict.keys():
                    room_conflict_check_dict[sc.room.id] = {'Monday':[], 'Tuesday':[], 'Wednesday':[], 'Thursday':[], 'Friday':[]}

                room_conflict_check_dict[sc.room.id][day_list[sc.day]].append([sc.begin_at.hour*100+sc.begin_at.minute,
                                                                                  sc.end_at.hour*100+sc.end_at.minute,
                                                                                  sc.course_offering.course.subject.abbrev+sc.course_offering.course.number+
                                                                                            ' ('+start_end_time_string(sc.begin_at.hour,
                                                                                                                       sc.begin_at.minute,sc.end_at.hour,sc.end_at.minute)+')'])

                if sc.end_at.hour > 16:
                    courses_after_five = True
                profs_this_class = ''
                for instructor in sc.course_offering.instructor.all():
                    if len(profs_this_class)>0:
                        profs_this_class = profs_this_class+' / '+instructor.first_name[:1]+' '+instructor.last_name
                    else:
                        profs_this_class = instructor.first_name[:1]+' '+instructor.last_name
                if len(profs_this_class)>0:
                    data_this_class.append(profs_this_class)

                begin_hour = sc.begin_at.hour
                if(sc.end_at.minute==0):
                    end_hour = sc.end_at.hour - 1
                else:
                    end_hour = sc.end_at.hour

                hour_range=range(begin_hour,end_hour+1)
                for ii in range(len(hour_range)):
                    local_data=[]
                    for line in data_this_class:
                        local_data.append(line)
                    if ii == 0:
                        if sc.begin_at.minute != 0:
                            if sc.begin_at.minute<10:
                                local_data.append('(begins @ '+str(sc.begin_at.hour)+':0'+str(sc.begin_at.minute)+')')
                            else:
                                local_data.append('(begins @ '+str(sc.begin_at.hour)+':'+str(sc.begin_at.minute)+')')
                    if ii == len(hour_range)-1:
                        if sc.end_at.minute != 50:
                            if sc.end_at.minute<10:
                                local_data.append('(ends @ '+str(sc.end_at.hour)+':0'+str(sc.end_at.minute)+')')
                            else:
                                local_data.append('(ends @ '+str(sc.end_at.hour)+':'+str(sc.end_at.minute)+')')

                    if len(master_dict[day][hour_range[ii]])>0:
                        master_dict[day][hour_range[ii]].append('')
                    for new_line in local_data:
                        master_dict[day][hour_range[ii]].append(new_line)

#        print master_dict
        
        for hour in num_lines_in_hour:
            for day in master_dict:
                if len(master_dict[day][hour])>num_lines_in_hour[hour]:
                    num_lines_in_hour[hour]=len(master_dict[day][hour])
                    num_lines_including_halves[hour]=num_lines_in_hour[hour]-1.0*(master_dict[day][hour].count(''))/2.0
#                    print master_dict[day][hour],num_lines_including_halves[hour]

#        print num_lines_in_hour

        schedule = initialize_canvas_data(courses_after_five, num_data_columns)
#        print schedule['height']
        
        height_hour_blocks_dict={7:0,8:0,9:0,10:0,11:0,12:0,13:0,14:0,15:0,16:0,17:0,18:0,19:0,20:0,21:0}
        min_height_hour_block = 3*schedule['box_text_line_sep_pixels']

        canvas_height=2*schedule['border']+schedule['height_day_names']
        for hour in num_lines_in_hour:
            height_this_block=(1+num_lines_including_halves[hour])*schedule['box_text_line_sep_pixels']
            if height_this_block<min_height_hour_block:
                height_hour_blocks_dict[hour]=min_height_hour_block
            else:
                height_hour_blocks_dict[hour]=height_this_block
            if hour<17:
                canvas_height=canvas_height+height_hour_blocks_dict[hour]
            else:
                if courses_after_five:
                    canvas_height=canvas_height+height_hour_blocks_dict[hour]
                    
#        print height_hour_blocks_dict
        # replace 'height_hour_block' by a dictionary of heights and 'height' by the recalculated canvas_height and width
        # by a greater width than normal            
        schedule['height_hour_block']=height_hour_blocks_dict
        schedule['height']=canvas_height
        schedule['width_day']=2*schedule['width_day']

#        print schedule

        canvas_width = 2*schedule['border']+5*schedule['width_day']+schedule['width_hour_names']
        schedule['width']=canvas_width
        grid_list, filled_row_list, table_text_list = create_flexible_schedule_grid(schedule, weekdays, 'MWF')

        table_text_list.append([schedule['width']/2,schedule['border']/2,
                                table_title,
                                schedule['table_title_font'],
                                schedule['table_header_text_colour']])
        
        b = schedule['border']
        h_h_b = schedule['height_hour_block']
        h_d_n = schedule['height_day_names']
        n_h_b = schedule['number_hour_blocks']
        start_time = schedule['start_time'] 
        vertical_edges = [b,b+h_d_n]
        current_edge = b+h_d_n
        for ii in range(n_h_b):
            hour = start_time+ii
            current_edge = current_edge+h_h_b[hour]
            vertical_edges.append(current_edge)

        box_list = []
        box_label_list = []
        # now loop over the text in the master_dict, etc.
        for day in master_dict:
            for ii in range(n_h_b):
                hour = start_time+ii
                text_list = master_dict[day][hour]
                
                if len(text_list)>0:
                    box_data, text_data = rectangle_coordinates_flexible_schedule(schedule, vertical_edges,
                                                                                       text_list, day_dict[day], hour)
#                print box_data, text_data

#        box_data = [xleft, begin_height_pixels, w_d, height, schedule['box_fill_colour'],
#                schedule['box_line_width'], schedule['box_border_colour']]

#        text_data = [
#                     [xleft+w_d/2, row_height, line_of_text,
#                      schedule['box_font'],
#                      schedule['table_header_text_colour']],[...],...]

                    box_list.append(box_data)
                    for text_row in text_data:
                        box_label_list.append(text_row)

        # format for filled rectangles is: [xleft, ytop, width, height, fillcolour, linewidth, bordercolour]
        # format for text is: [xcenter, ycenter, text_string, font, text_colour]

        json_box_list = simplejson.dumps(box_list)
        json_box_label_list = simplejson.dumps(box_label_list)
        json_grid_list = simplejson.dumps(grid_list)
        json_filled_row_list = simplejson.dumps(filled_row_list)
        json_table_text_list = simplejson.dumps(table_text_list)

        error_messages=[]
        for faculty_member_id in instructor_conflict_check_dict.keys():
            overlap_dict = check_for_conflicts(instructor_conflict_check_dict[faculty_member_id])
            faculty_member = FacultyMember.objects.get(pk = faculty_member_id)
            for key in overlap_dict:
                for row in overlap_dict[key]:
                    error_messages.append([faculty_member.first_name[:1]+' '+
                                           faculty_member.last_name+' has a conflict on '+key+'s:',
                                           row[0]+' conflicts with '+row[1]])

        for room_id in room_conflict_check_dict.keys():
            overlap_dict = check_for_conflicts(room_conflict_check_dict[room_id])
            room = Room.objects.get(pk = room_id)
            for key in overlap_dict:
                for row in overlap_dict[key]:
                    error_messages.append([room.building.abbrev+room.number+' has a conflict on '+key+'s:',
                                           row[0]+' conflicts with '+row[1]])

        id = 'id'+str(idnum)
        data_this_term = {'day_name': day,
                          'json_box_list': json_box_list,
                          'json_box_label_list':json_box_label_list,
                          'json_grid_list': json_grid_list,
                          'json_filled_row_list': json_filled_row_list,
                          'json_table_text_list': json_table_text_list,
                          'id':id,
                          'schedule':schedule,
                          'error_messages':error_messages,
                          'semester':current_semester_string
                          }
        data_list.append(data_this_term)

#    print data_list
    context={'data_list':data_list, 'year':academic_year_string, 'id': user_preferences.id, 'department': user_preferences.department_to_view}
    return render(request, 'weekly_schedule_dept_summary.html', context)

def create_flexible_schedule_grid(schedule,column_titles,chapel):
    """
    returns the coordinates for the lines that form the schedule grid in the
    form [[xbegin, ybegin, xend, yend],[...],[...]];
    this function is very similar to create_schedule_grid, except it creates
    a schedule where the cells for the various hours can be different heights.
    yes...I should have done this all in one function :(
    """

# chapel can be "every" (every column), "none" (no columns) or "MWF" (1st, 3rd and 5th columns)

    line_coordinates_array = []
    filled_row_array = []
    text_array = []

    b = schedule['border']
    c_h = schedule['height']
    c_w = schedule['width']
    w_h_n = schedule['width_hour_names']
    w_d = schedule['width_day']
    n_h_b = schedule['number_hour_blocks']
    h_h_b = schedule['height_hour_block']
    # h_h_b is actually a dictionary in this case!!!
    h_d_n = schedule['height_day_names']

    start_time = schedule['start_time'] 
    vertical_edges = [b,b+h_d_n]
    current_edge = b+h_d_n
    for ii in range(n_h_b):
        hour = start_time+ii
        current_edge = current_edge+h_h_b[hour]
        vertical_edges.append(current_edge)

    for ii in range(len(column_titles)):
        text_array.append([b+w_h_n+ii*w_d+w_d/2,b+h_d_n/2,
                           column_titles[ii],
                           schedule['table_header_font'],
                           schedule['table_header_text_colour']])

    if chapel == 'MWF':
        for ii in range(3):
            text_array.append([b+w_h_n+2*ii*w_d+w_d/2,vertical_edges[4]+h_h_b[10]/2,
                               'chapel',
                               schedule['table_header_font'],
                               schedule['table_header_text_colour']])
    elif chapel == 'every':
        for ii in range(len(column_titles)):
            text_array.append([b+w_h_n+ii*w_d+w_d/2,vertical_edges[4]+h_h_b[10]/2,
                               'chapel',
                               schedule['table_header_font'],
                               schedule['table_header_text_colour']])

    for ii in range(n_h_b):
        time_int = start_time+ii
        time = str(time_int)+':00'
        text_array.append([b+w_h_n/2,vertical_edges[1+ii]+h_h_b[7+ii]/2,
                           time,
                           schedule['table_header_font'],
                           schedule['table_header_text_colour']])


    # coordinates for the vertical lines in the grid
    line_coordinates_array.append([b,b,b,c_h-b])
    for ii in range(len(column_titles)+1):
        line_coordinates_array.append([b+w_h_n+ii*w_d,b,b+w_h_n+ii*w_d,c_h-b])
    # coordinates for the horizontal lines in the grid
    line_coordinates_array.append([b,b,c_w-b,b])
    line_coordinates_array.append([b,c_h-b,c_w-b,c_h-b])

    colour_on = True

    for ii in range(n_h_b):
        line_coordinates_array.append([b,vertical_edges[ii+1],c_w-b,vertical_edges[ii+1]])
        if colour_on:
            filled_row_array.append([b,vertical_edges[ii+1],c_w-2*b,h_h_b[7+ii],
                                     schedule['row_background_fill_colour'],
                                     schedule['grid_line_width'],
                                     schedule['row_background_fill_colour']])
            colour_on = False
        else:
            colour_on = True

    return line_coordinates_array, filled_row_array, text_array

def rectangle_coordinates_flexible_schedule(schedule, vertical_edges, text_list, day_int, hour):
    """
    returns the coordinates required (by the javascript in the template)
    to display a rectangular box for a single class meeting
    """
    
    b = schedule['border']
    w_h_n = schedule['width_hour_names']
    w_d = schedule['width_day']
    h_h_b = schedule['height_hour_block']
    h_d_n = schedule['height_day_names']

    # base_hour is the earliest hour on the schedule
                                                                              
    base_hour = schedule['start_time']
    xleft = b+w_h_n+day_int*w_d

    begin_height = vertical_edges[hour-base_hour+1]
    height = h_h_b[hour]
    line_sep = schedule['box_text_line_sep_pixels']
    
# format for filled rectangles is: [xleft, ytop, width, height, fillcolour, linewidth, bordercolour]

    box_data = [xleft, begin_height, w_d, height, schedule['box_fill_colour'],
                schedule['box_line_width'], schedule['box_border_colour']]

    text_data = []
    
    text_height = begin_height
    for line in text_list:
        if len(line)>0:
            text_height = text_height+line_sep
        else:
            text_height = text_height+line_sep/2

        text_data.append([xleft+w_d/2, text_height, line,
                          schedule['box_font'],
                          schedule['table_header_text_colour']])

    return box_data, text_data

@login_required
def select_course(request):
    """
    Allows the user to select a course, as the first step in creating a new course offering.
    """
    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department = user_preferences.department_to_view

    if request.method == 'POST':
        form = CourseSelectForm(department.id, request.POST)
        if form.is_valid():
            course = form.cleaned_data.get('course')
            url_string = '/planner/addcourseoffering/'+str(course.id)+'/1/'
            print url_string
            return redirect(url_string)
        else:
            return render(request, 'select_course.html', {'form': form})
    else:
        form = CourseSelectForm(department.id)
        context = {'form': form}
        if "never_alerted_before" in request.session:
            context['never_alerted_before'] = False
        else:
            context['never_alerted_before'] = True
        return render(request, 'select_course.html', context)

@login_required
def add_course_confirmation(request, daisy_chaining):
    """
    Tries to verify that the user really does wish to create a new course.
    """
    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department = user_preferences.department_to_view

    if request.method == 'POST':
        form = CourseSelectForm(department.id, request.POST)
        if form.is_valid():
            course = form.cleaned_data.get('course')
            url_string = '/planner/addcourseoffering/'+str(course.id)+'/1/'
            print url_string
            return redirect(url_string)
        else:
            url_string = '/planner/addcourseconfirmation/1/'
            return render(request, url_string, {'form': form})
    else:
        form = CourseSelectForm(department.id)
        context = {'form': form}
        return render(request, 'add_course_confirmation.html', context)
    
@login_required
def update_semester_for_course_offering(request, id):
    """
    Allows the user to update the semester for the given course offering.
    """
    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department = user_preferences.department_to_view
    year_to_view = user_preferences.academic_year_to_view.begin_on.year
    year = user_preferences.academic_year_to_view

    instance = CourseOffering.objects.get(pk = id)
#    print instance

    if request.method == 'POST':
        form = SemesterSelectForm(year, request.POST, instance=instance)
        if form.is_valid():
            form.save()
            next = request.GET.get('next', 'home')
            return redirect(next)
        else:
            return render(request, 'update_semester.html', {'form':form, 'course_offering': instance})
    else:
        form = SemesterSelectForm(year, instance=instance)
        return render(request, 'update_semester.html', {'form':form, 'course_offering': instance})

def close_all_divs(request):
    """
    resests the sessions variables so that all divs on the faculty load summary page will be closed upon reload
    """
    user = request.user
    user_preferences = user.user_preferences.all()[0]
    key = "dept_load_summary-"+str(ALL_FACULTY_DIV_ID)
    request.session[key] = 'closed'
    key = "dept_load_summary-"+str(UNDERASSIGNED_LOAD_DIV_ID)
    request.session[key] = 'closed'
    for faculty in user_preferences.faculty_to_view.all():
        key = "dept_load_summary-"+str(faculty.id)
        request.session[key] = 'closed'
    return

@login_required
def open_close_div_tracker(request,id):
    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
# if the id is for one of the profs, first close divs for all faculty except the incoming one
    if ((int(id) != ALL_FACULTY_DIV_ID) and (int(id) != UNDERASSIGNED_LOAD_DIV_ID)):
        for faculty in user_preferences.faculty_to_view.all():
            if faculty.id != int(id):
                key = "dept_load_summary-"+str(faculty.id)
                request.session[key] = 'closed'
# now deal with the one that came in        
    key = "dept_load_summary-"+id
    if key in request.session:
        if request.session[key] == 'closed':
            request.session[key] = 'open'
        else:
            request.session[key] = 'closed'
    else:
        request.session[key] = 'open'

    return_string = "div #"+id+"is now "+request.session[key]
#    print "list of keys:"
#    for key in request.session.keys():
#        print key, request.session[key]

    return HttpResponse(return_string)

def construct_json_open_div_id_list(request):
    """
    constructs a json-formatted list of ids for the divs that should be open upon loading the dept load summary page
    """
    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    open_div_list = []

    all_prof_ids_closed = True
    close_all_prof_ids = False
    for faculty in user_preferences.faculty_to_view.all():
        key = "dept_load_summary-"+str(faculty.id)
        if key in request.session:
            if request.session[key]=='open':
                if all_prof_ids_closed == False: #apparently there are more than one that are marked as open; oops! close them all
                    close_all_prof_ids = True
                else:
                    all_prof_ids_closed = False
                    open_div_list.append(faculty.id)
    if close_all_prof_ids: # there has been an irregularity; close all the prof divs; reset the session variables, too
        open_div_list = []
        for faculty in user_preferences.faculty_to_view.all():
            key = "dept_load_summary-"+str(faculty.id)
            request.session[key]='closed'

    key = "dept_load_summary-"+str(ALL_FACULTY_DIV_ID)
    if key in request.session:
        if request.session[key]=='open':
            open_div_list.append(ALL_FACULTY_DIV_ID)

    key = "dept_load_summary-"+str(UNDERASSIGNED_LOAD_DIV_ID)
    if key in request.session:
        if request.session[key]=='open':
            open_div_list.append(UNDERASSIGNED_LOAD_DIV_ID)

    json_open_div_id_list = simplejson.dumps(open_div_list)

    return json_open_div_id_list

@login_required
def alert_register(request):
    """
    sets the session variable never_alerted_before to false, which will
    turn off future alerts during this session when adding a course section
    """
    request.session["never_alerted_before"] = False
    return HttpResponse("")
