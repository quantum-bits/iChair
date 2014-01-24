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

import csv
from django.http import HttpResponse
import xlwt
from os.path import expanduser
from datetime import date

def home(request):
    return render(request, 'home.html')

@login_required
def profile(request):
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
                'id': user_preferences.id
                }
    return render(request, 'profile.html', context)

@login_required
def display_notes(request):

    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view.begin_on.year
    academic_year_string = str(academic_year)+'-'+str(academic_year+1)

    temp_data = Note.objects.all().filter(Q(department__abbrev=department.abbrev)&Q(year__begin_on__year=academic_year))

    can_edit = True
    if user_preferences.permission_level == 0:
        can_edit = False
        

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
        'can_edit': can_edit
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

    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view.begin_on.year
    academic_year_string = str(academic_year)+'-'+str(academic_year+1)
    can_edit = True
    if user_preferences.permission_level == 0:
        can_edit = False

# the following lines select out semester objects for 2013...below we use a different approach
#    year_object=AcademicYear.objects.filter(begin_on__year='2013')[0]
#    semester_objects=year_object.semesters.all()

# need to think about offering instructors...just from dept?  make dept many to many?
# also, when picking out offering instructors, maybe queryset them so they are only from dept?!?!?!?!
# also...we could do a queryset on instructors, most likely, in the form (see AddStudentSemesterForm for an example),
# but would we want to change this by year or something...?
# right now it gags if there is a faculty member from outside of the dept...could fix by adding the extra names
# in to instructordict, etc.
#
#----------------------
# ...ah...maybe there should be an object in the database for each academic year, listing exactly which instructors
# to include in the load list for a given department.  Then it could change year by year.  Easy-peasy.
#----------------------
#
# NOTES:
# 1.  In the following code, it is assumed that each course offering can only correspond to one semester.  Accordingly,
#     the load for each person in each row, can only be one number (for fall, J-term or spring...but only one of those)
# 2.  Summer has been deleted from the load schedule.  If there is any load for summer, it is added to the spring.  This is HARDCODED (yech!)
#

    ii = 0
    load_list_initial=[]
    instructordict=dict()
    instructor_id_list=[]
    instructor_name_list=[]
    instructor_name_dict=dict()
    instructor_integer_list=[]
    for faculty in user_preferences.faculty_to_view.filter(department=department):
        instructordict[faculty.id] = ii
        instructor_name_list.append(faculty.first_name[0]+'. '+faculty.last_name)
        instructor_name_dict[faculty.id] = faculty.first_name[0]+'. '+faculty.last_name
        instructor_id_list.append(faculty.id)
        instructor_integer_list.append(ii)
        ii=ii+1

    number_faculty=ii

    ii = 0
    semesterdict=dict()
    for semester in SemesterName.objects.all():
        semesterdict[semester.name] = ii
        ii=ii+1
#
# load for summer is added to the spring....
#
    semesterdict[u'Summer']=2

    data_list = []

    number_semesters = 4

    faculty_summary_load_list = []
    for ii in range(number_faculty):
        faculty_summary_load_list.append([0,0,0])

    for subject in department.subjects.all():
        for course in subject.courses.all():
            for course_offering in course.offerings.all():
                semester_name = course_offering.semester.name.name

                scheduled_classes = course_offering.scheduled_classes.all()
                if len(scheduled_classes)==0:
                    meetings_scheduled = False
                    meeting_times_list = ["---"]
                    room_list = ["---"]
                else:
                    meetings_scheduled = True
                    meeting_times_list, room_list = class_time_and_room_summary(scheduled_classes)
#                    room_list = room_list_summary(scheduled_classes)

                if course_offering.semester.year.begin_on.year == academic_year:
                    number = u"{0} {1}".format(course_offering.course.subject,
                                               course_offering.course.number)
                    course_name = course_offering.course.title
                    available_load_hours = course_offering.load_available

                    if abs(round(available_load_hours)-available_load_hours)<0.01:
                        # if the load is close to an int, round it, then int it (adding 0.01 to be on the safe side)
                        available_load_hours = int(round(available_load_hours)+0.01)
                    # must be an easier way to do this....
                    load_list = []
                    for ii in range(number_faculty):
                        load_list.append([-1,0])
                    # using _set.all() allows us to get the info in the intermediate ("through") table
#                    for instructor in course_offering.offeringinstructor_set.all():
                    for instructor in course_offering.offering_instructors.all():
                        if instructor.instructor in user_preferences.faculty_to_view.filter(department=department):
                            instructor_load = load_hour_rounder(instructor.load_credit)
                            instructor_id = instructor.instructor.id
                            ii = instructordict[instructor_id]
                            jj = semesterdict[semester_name]
                            load_list[ii][0] = instructor_load
                            load_list[ii][1] = jj
                            faculty_summary_load_list[ii][jj] = faculty_summary_load_list[ii][jj]+instructor_load

                    load_diff = load_hour_rounder(course_offering.load_difference())

                    data_list.append({'number':number,
                                      'name':course_name,
                                      'rooms':room_list,
                                      'load_hours': available_load_hours,
                                      'load_difference': load_diff,
                                      'load_hour_list': load_list,
                                      'id':course_offering.id,
                                      'comment':course_offering.comment,
                                      'semester':semester_name,
                                      'meeting_times':meeting_times_list,
                                      'meetings_scheduled':meetings_scheduled
                                      })

    admin_data_list=[]

    for other_load_type in user_preferences.other_load_types_to_view.all():
        load_list = []
        for ii in range(number_faculty):
            load_list.append([0,0,0])
        for other_load in other_load_type.other_loads.all():
            instructor_id = other_load.instructor.id
            if other_load.semester.year.begin_on.year == academic_year and instructor_id in instructor_id_list:
                semester_name = other_load.semester.name.name
                ii = instructordict[instructor_id]
                jj = semesterdict[semester_name]
                load_list[ii][jj] = load_list[ii][jj]+load_hour_rounder(other_load.load_credit)
                faculty_summary_load_list[ii][jj] = faculty_summary_load_list[ii][jj]+other_load.load_credit
        admin_data_list.append({'load_type': other_load_type.load_type,
                                'load_hour_list': load_list,
                                'id':other_load_type.id
                                })

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
            element = row['load_hour_list'][instructordict[instructor_id]]
            if element[0] > 0 or element[1] > 0 or element[2] > 0:
                admin_data.append({'load_type':row['load_type'],
                                   'load_hour_list':element,
                                   'id': row['id']
                                   })


        data_list_by_instructor.append({'instructor_id':instructordict[instructor_id],
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
             'can_edit': can_edit
             }
    return render(request, 'dept_load_summary.html', context)

@login_required
def export_data(request):
    """
    Exports data to an Excel file in 'actual load' or 'projected load' format.
    """
    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view
    faculty_to_view = user_preferences.faculty_to_view.all()

    home = expanduser("~")
    today = date.today()
    date_string = str(today.month)+'/'+str(today.day)+'/'+str(today.year)

    can_edit = True
    if user_preferences.permission_level == 0:
        can_edit = False

    ii = 0
    semesterdict=dict()
    for semester in SemesterName.objects.all():
        semesterdict[semester.name] = ii
        ii=ii+1
#
# load for summer is added to the spring....
#
    semesterdict[u'Summer']=2

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
            other_load_dict=dict()
            other_load_name_dict=dict()
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

                    course_load_dict[course_id][semesterdict[oi.course_offering.semester.name.name]] = course_load_dict[course_id][semesterdict[oi.course_offering.semester.name.name]] + oi.load_credit


                other_loads = faculty.other_loads.filter(semester=semester)
                for ol in other_loads:
                    other_load_id = ol.load_type.id
                    if other_load_id not in other_load_dict:
                        other_load_dict[other_load_id]=[0,0,0]
                        other_load_name_dict[other_load_id]=ol.load_type.load_type
                    
                    other_load_dict[other_load_id][semesterdict[ol.semester.name.name]] = other_load_dict[other_load_id][semesterdict[ol.semester.name.name]] + ol.load_credit


            faculty_data_list.append({'last_name':faculty.last_name, 
                                      'first_name':faculty.first_name, 
                                      'course_load_dict':course_load_dict,
                                      'course_name_dict':course_name_dict,
                                      'course_number_dict':course_number_dict,
                                      'other_load_dict':other_load_dict,
                                      'other_load_name_dict':other_load_name_dict})
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
        else:
            sheet = book.add_sheet(faculty['last_name'])

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
        sheet.write_merge(9,9,0,7,'Instructions:   Use one sheet per faculty member.  Include all assignments for which load credit is granted.  Non-teaching load (e.g. department',xlwt.easyxf(styles['calibri_font']+'border: top thin, right thin;'))
        sheet.write_merge(10,10,0,7,'chair duties) should be included and clearly identified.  DO NOT include independent studies/practicums.  For adjuncts, use one sheet with a',xlwt.easyxf(styles['calibri_font']+'border: right thin;'))
        sheet.write_merge(11,11,0,7,'combined total of load credit for each applicable term',xlwt.easyxf(styles['calibri_font']+'border: right thin;'))
        sheet.write_merge(12,12,0,7,'Forms should be emailed to your School Administrative Assistant by '+global_data['due_date']+'.',xlwt.easyxf(styles['calibri_centered']+'border: bottom thin, right thin;'))
        sheet.write_merge(13,13,2,5,table_title,xlwt.easyxf(styles['calibri_bold_bordered_centered']))
        sheet.write(14,0,'Faculty Member',xlwt.easyxf(styles['calibri_centered']+'border: top thin, right thin, bottom thin;'))
        sheet.write_merge(15,16,0,0,faculty['first_name']+' '+faculty['last_name'],xlwt.easyxf(styles['calibri_centered']+'border: top thin, right thin, bottom thin;'))
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
            sheet.write(row_data_start+i,7,'',style_calibri_bordered)
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
            sheet.write(row_data_start+i,7,'',style_calibri_bordered)
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
def update_course_offering(request,id):
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
    }

    if request.method == 'POST':
        form = CourseOfferingForm(request.POST, instance = instance)
        formset = InstructorFormset(request.POST, instance = instance)

        formset.is_valid()
        prof_repeated_errors=formset.non_form_errors()

        if form.is_valid() and formset.is_valid() and not prof_repeated_errors:
            form.save()
            formset.save()
            next = request.GET.get('next', 'profile')
            return redirect(next)
#            return redirect('department_load_summary')
        else:

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
def update_class_schedule(request,id):
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
    }

    if request.method == 'POST':
#        form = CourseOfferingForm(request.POST, instance=instance)
        formset = ClassScheduleFormset(request.POST, instance = instance)

        formset.is_valid()
        formset_error=formset.non_form_errors()

        if formset.is_valid() and not formset_error:
#            form.save()
            formset.save()
            next = request.GET.get('next','profile')
            return redirect(next)
#            return redirect('department_load_summary')
        else:

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

    context={'data_list':data_list, 'year':academic_year_string}
    return render(request, 'weekly_schedule.html', context)

@login_required
def daily_schedule(request):
    """Display daily schedules for the department"""

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

            id = 'id'+str(idnum)
            data_this_day.append({'day_name': day,
                                  'json_box_list': json_box_list,
                                  'json_box_label_list':json_box_label_list,
                                  'json_grid_list': json_grid_list,
                                  'json_filled_row_list': json_filled_row_list,
                                  'json_table_text_list': json_table_text_list,
                                  'id':id,
                                  'schedule':schedule})
        data_list.append(data_this_day)

    context={'data_list':data_list, 'year':academic_year_string}
    return render(request, 'daily_schedule.html', context)


@login_required
def room_schedule(request):
    """Display daily schedules for the department"""

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

    for room in user_preferences.rooms_to_view.all().order_by('building','number'):
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

    context={'data_list':data_list, 'year':academic_year_string}
    return render(request, 'room_schedule.html', context)

@login_required
def course_schedule(request):
    """Display daily schedules for the department"""

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

    context={'data_list':data_list, 'year':academic_year_string}
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
def course_summary(request):
    """Display courses for the department and semesters in which they are taught"""

    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view

    can_edit = True
    if user_preferences.permission_level == 0:
        can_edit = False

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


    context={'course_data_list':data_list, 'year_list':year_list, 'number_semesters': number_semesters,
             'can_edit': can_edit}
    return render(request, 'course_summary.html', context)



@login_required
def manage_course_offerings(request,id):
    instance = Course.objects.get(pk = id)
# create the formset class
    CourseOfferingFormset = inlineformset_factory(Course, CourseOffering, formset = BaseCourseOfferingFormset, extra=2, exclude='instructor')
# create the formset
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

            return redirect('course_summary')
        else:

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

def new_class_schedule(request,id):
# start is the start time in hours (7 for 7:00, etc.)
# duration is the class duration in minutes

    course_offering = CourseOffering.objects.get(pk=id)

    if request.method == 'POST':
        form = EasyDaySchedulerForm(request.POST)
        if form.is_valid():
            day_dict = {'M':0, 'T':1, 'W':2, 'R':3, 'F':4}

            # Note: days will be something like u'MWF', start will be something like u'7' and duration will be something like u'50'
            days = form.cleaned_data.get('days')
            start = form.cleaned_data.get('start')
            duration = form.cleaned_data.get('duration')
            room = form.cleaned_data.get('room')

            for day in days:
                new_class = ScheduledClass(course_offering = course_offering)
                new_class.day = day_dict[day]
                new_class.begin_at = start+':00'
                end_hour = str(int(start)+int(int(duration)/60))
                minute = int(duration)%60
                if minute == 0:
                    end_minute = ':00'
                elif minute < 10:
                    end_minute = ':0'+str(minute)
                else:
                    end_minute = ':'+str(minute)
                new_class.end_at = end_hour+end_minute
                new_class.room = room
                # if the db hangs, try new_class.room_id = room.id
                new_class.save()

            return redirect('department_load_summary')
        else:
            return render(request, 'new_class_schedule.html', {'form':form, 'id':id, 'course':course_offering})

    else:
        form = EasyDaySchedulerForm()
        return render(request, 'new_class_schedule.html', {'form':form, 'id':id, 'course':course_offering })

def add_course(request):
# start is the start time in hours (7 for 7:00, etc.)
# duration is the class duration in minutes

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department_id = user_preferences.department_to_view.id

    if request.method == 'POST':
        form = AddCourseForm(department_id,request.POST)
        if form.is_valid():
            form.save()
            return redirect('course_summary')
        else:
            return render(request, 'add_course.html', {'form':form})

    else:
        form = AddCourseForm(department_id)
        return render(request, 'add_course.html', {'form':form})

@login_required
def update_course(request, id):

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department_id = user_preferences.department_to_view.id

    instance = Course.objects.get(pk = id)

    if request.method == 'POST':
        form = AddCourseForm(department_id, request.POST, instance=instance)
        if form.is_valid():
            form.save()
            next = request.GET.get('next', 'profile')
            return redirect(next)
#            return redirect('course_summary')
        else:
            return render(request, 'add_course.html', {'form': form})
    else:
        form = AddCourseForm(department_id, instance=instance)
        context = {'form': form}
        return render(request, 'add_course.html', context)

@login_required
def delete_course_confirmation(request, id):
    course = Course.objects.get(pk = id)
    context ={'course': course}
    return render(request, 'delete_course_confirmation.html', context)

@login_required
def delete_course(request, id):
    instance = Course.objects.get(pk = id)

    instance.delete()
    return redirect('course_summary')

@login_required
def registrar_schedule(request):
    """Display courses in roughly the format used by the registrar"""

    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view
    year_to_view = user_preferences.academic_year_to_view.begin_on.year

    academic_year_string = str(year_to_view)+'-'+str(year_to_view + 1)

    can_edit = True
    if user_preferences.permission_level == 0:
        can_edit = False

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
             'academic_year': academic_year_string, 'can_edit': can_edit}
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
            next = request.GET.get('next', 'profile')
            return redirect(next)
        else:
            if formset_error:
                errordict.update({'formset_error':formset_error})
            for subform in formset:
                if subform.errors:
                    errordict.update(subform.errors)

            return render(request, 'update_other_load.html', dict)

    else:
        return render(request, 'update_other_load.html', dict)

@login_required
def update_rooms_to_view(request, id):

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department_id = user_preferences.department_to_view.id

    instance = UserPreferences.objects.get(pk = id)

    if request.method == 'POST':
        form = UpdateRoomsToViewForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            next = request.GET.get('next', 'profile')
            return redirect(next)
        else:
            return render(request, 'update_rooms_to_view.html', {'form': form})
    else:
        form = UpdateRoomsToViewForm(instance=instance)
        context = {'form': form}
        return render(request, 'update_rooms_to_view.html', context)

@login_required
def update_faculty_to_view(request, id):

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department_id = user_preferences.department_to_view.id

    instance = UserPreferences.objects.get(pk = id)

    if request.method == 'POST':
        form = UpdateFacultyToViewForm(department_id, request.POST, instance=instance)
        if form.is_valid():
            form.save()
            next = request.GET.get('next', 'profile')
            return redirect(next)
        else:
            return render(request, 'update_faculty_to_view.html', {'form': form})
    else:
        form = UpdateFacultyToViewForm(department_id, instance=instance)
        context = {'form': form}
        return render(request, 'update_faculty_to_view.html', context)

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
            next = request.GET.get('next', 'profile')
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
            next = request.GET.get('next', 'profile')
            return redirect(next)
        else:
            return render(request, 'update_loads_to_view.html', {'form': form})
    else:
        form = UpdateLoadsToViewForm(instance=instance)
        context = {'form': form}
        return render(request, 'update_loads_to_view.html', context)


@login_required
def copy_courses(request, id, check_all_flag):

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    department = user_preferences.department_to_view

    academic_year_copy_from = AcademicYear.objects.get(pk = id)
    academic_year_copy_to = user_preferences.academic_year_to_view
    faculty_to_view = user_preferences.faculty_to_view.all()

    print academic_year_copy_from
    print academic_year_copy_to
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
                print instructor.instructor
                print instructor.load_credit
                # NOTE: instructors are only assigned to courses if they are currently listed as being "viewable"
                if instructor.instructor in faculty_to_view:
                    new_offering_instructor = OfferingInstructor.objects.create(course_offering = new_co,
                                                                                instructor = instructor.instructor,
                                                                                load_credit = instructor.load_credit
                                                                                )
                    new_offering_instructor.save()

            for sc in co.scheduled_classes.all():
                print sc

                schedule_addition = ScheduledClass.objects.create(course_offering = new_co,
                                                                  day = sc.day,
                                                                  begin_at = sc.begin_at,
                                                                  end_at = sc.end_at,
                                                                  room = sc.room,
                                                                  comment = sc.comment
                                                                  )
                schedule_addition.save()


        next = request.GET.get('next', 'profile')
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

