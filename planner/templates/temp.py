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


------

{% block sidebar %}
{% if can_edit %}
<form action=""  method="post">
  {% csrf_token %}
<p> <h2>Type of Load Sheet to Export</h2></p>
<p>
  <div class="alert alert-student-info">
    <table class="table table-striped table-bordered table-hover">
      <tbody>
	<tr>
	  <td>
	  <div align="center">
	  <select name="doc_type" id="option1">
	    <option value="actual">Actual Load Sheet</option>
	    <option value="projected">Projected Load Sheet</option>
	  </select>
	  </div>
	  </td>
	</tr>
      </tbody>
    </table>
   </div>
</p>
<p><h2> Faculty Members to Include</h2></p>
<p>
  <div class="alert alert-student-info">
    <table class="table table-striped table-bordered table-hover">
      <tbody>
	    {% for faculty in faculty_list %}
	    <tr>
	    <th>
	    <div>
	      {{faculty.name}}
	    </div>
	    </th>
	    <td> <div align="center">{{faculty.hrs}}</div> </td>
	    <td>
	<input type="checkbox" checked = "yes" name="faculty_for_export" id="optiona{{faculty.id}}" value={{faculty.id}} />
	    </td>
	    </tr>
	    {% endfor %}
      </tbody>
    </table>
 </div>
</p>

<p> <h2>Name of Person Preparing Report</h2></p>
<p>
  <div class="alert alert-student-info">
    <table class="table table-striped table-bordered table-hover">
      <tbody>
	<tr>
	  <td>
	  <div align="center">
	  <input type = "text" name="name_preparer" id="option2">
	  </div>
	  </td>
	</tr>
      </tbody>
    </table>
   </div>
</p>


  <p><input type="submit" alt="register" /></p>
</form>
{% else %}
    <p> Sorry: You cannot Export. <p>
{% endif %}
