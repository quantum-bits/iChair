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

def home(request):
    return render(request, 'home.html')

def student_registration(request):
    if request.user.is_authenticated():
        return redirect('profile')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(username = form.cleaned_data['username'],
                                            email = form.cleaned_data['email'],
                                            password = form.cleaned_data['password'])
            user.save()

            student = Student(user=user,
                              name=form.cleaned_data['name'],
                              entering_year=form.cleaned_data['entering_year'],
                              major = form.cleaned_data['major'])
            student.save()

            yearlist = [0, 1, 2, 3, 4, 5]
            semesterlist = [1, 2, 3, 4]
            for year_temp in yearlist:
                if year_temp == 0:
                    semester_temp = 0
                    p1 = StudentSemesterCourses(student=student,
                                                year=year_temp,
                                                semester=semester_temp)
                    p1.save()
                else:
                    for semester_temp in semesterlist:
                        p1 = StudentSemesterCourses(student=student,
                                                    year=year_temp,
                                                    semester=semester_temp)
                        p1.save()

            if student.major is not None:
                courses_added = prepopulate_student_semesters(student.id)
            else:
                courses_added = False

            return redirect('profile')
        else:
            return render(request, 'register.html', {'form': form})

        # Should the other things (advising notes, etc.) be included here as well?!?

    else:
        # User is not submitting the form; show them the blank registration form.
        form = RegistrationForm()
        context = {'form': form}
        return render(request, 'register.html', context)

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
def update_major(request, id):
    request_id = request.user.get_student_id()
    incoming_id = int(id)

    if request_id != incoming_id:
        return redirect('profile')

    instance = Student.objects.get(pk=id)

    if request.method == 'POST':
        form = UpdateMajorForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('profile')
        else:
            return render(request, 'updatemajor.html', {'form': form})
    else:
        # User is not submitting the form; show them the blank add major form.
        form = UpdateMajorForm(instance=instance)
        context = {'form': form}
        return render(request, 'updatemajor.html', context)


# problems:
# --> I think the way that I have passed the object's id is not the best way to do it....
# --> maybe look here:
#     http://stackoverflow.com/questions/9013697/django-how-to-pass-object-object-id-to-another-template
@login_required
def update_student_semester(request, id):
    instance = StudentSemesterCourses.objects.get(pk = id)

    # The following statement kicks the person out if he/she is trying to hack into
    # someone else's "update student semester" function...if the name of the requester and
    # the person who "belongs" to the id are different, the requester gets sent back to
    # his/her profile as punishment :)
    request_id = request.user.get_student_id()
    incoming_id = instance.student.id
    if request_id != incoming_id:
        return redirect('profile')

    year = instance.actual_year
    semester = instance.semester
    student_local = request.user
    student_created_courses = CreateYourOwnCourse.objects.all().filter(Q(student=student_local) &
                                                                       Q(semester=semester) &
                                                                       Q(actual_year=year))
    courselist= Course.objects.filter(Q(sospring=1) & Q(semester__actual_year=year) & Q(semester__semester_of_acad_year = semester))
    current_course_list = Course.objects.filter(Q(semester__actual_year=year) & Q(semester__semester_of_acad_year = semester))

    sccdatablock=[]
    for scc in student_created_courses:
        if scc.equivalentcourse:
            eqnum = ", equiv to " + scc.equivalentcourse.number
        else:
            eqnum  =  ""
        if scc.sp:
            SPtemp = ", SP"
        else:
            SPtemp = ""
        if scc.cc:
            CCtemp = ", CC"
        else:
            CCtemp = ""
        sccdatablock.append({'cname':scc.name,
                             'cnumber':scc.number,
                             'ccredithrs':scc.credit_hours,
                             'csemester':scc.semester,
                             'cyear':scc.actual_year,
                             'equivalentcourse':eqnum,
                             'sp':SPtemp,
                             'cc':CCtemp,
                             'courseid':scc.id})

    if request.method == 'POST':
        my_kwargs = dict(instance=instance,
                         actual_year=year,
                         semester=semester)
        form = AddStudentSemesterForm(request.POST, **my_kwargs)
        if form.is_valid():
            form.save()
            return redirect('four_year_plan')
        else:
            return render(request, 'updatesemester.html',
                          {'form': form, 'sccdatablock':sccdatablock})
    else:
        # User is not submitting the form; show them the blank add semester form.
        my_kwargs = dict(instance=instance,
                         actual_year=year,
                         semester=semester)
        form = AddStudentSemesterForm(**my_kwargs)
        context = {'form': form,
                   'sccdatablock':sccdatablock,
                   'instanceid':id,
		   'courselist': courselist,
		   'current_course_list': current_course_list,
		   'semester': semester}
        return render(request, 'updatesemester.html', context)


@login_required
def display_notes(request):

    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view.begin_on.year
    academic_year_string = str(academic_year)+'-'+str(academic_year+1)

    temp_data = Note.objects.all().filter(Q(department__abbrev=department.abbrev)&Q(year__begin_on__year=academic_year))

#    print temp_data

    datablock = []
    ii = 0
    for adv_notes in temp_data:
        ii = ii + 1
        datablock.append([adv_notes.updated_at, adv_notes.note, adv_notes.id, ii])

#    print datablock

    context = {
        'department': department,
        'datablock': datablock
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
def display_four_year_plan(request):
    if request.user.is_student():
        isProfessor = False
        student_local = request.user.student
    else:
        isProfessor = True
        student_local = request.user.professor.advisee
        if student_local is None:
            # No advisee currently selected; go pick one first.
            return redirect('update_advisee', 1)

    total_credit_hours_four_years = 0
    temp_data = StudentSemesterCourses.objects.all().filter(student=student_local)
    temp_data2 = CreateYourOwnCourse.objects.all().filter(student=student_local)

    enteringyear = temp_data[0].student.entering_year

    studentid = temp_data[0].student.id
    pre_not_met_list, co_not_met_list = pre_co_req_check(studentid)

    # ssclist is used for later on when we try to find other semesters that a given course
    # is offered.
    ssclist=[]
    for ssc in temp_data:
        if ssc.semester !=0:
            # Don't include pre-TU ssc object here
            numcrhrsthissem = 0
            for course in ssc.courses.all():
                numcrhrsthissem = numcrhrsthissem + course.credit_hours
            # Now add in credit hours from any create your own type courses
            temp_data4 = temp_data2.filter(Q(semester=ssc.semester)&Q(actual_year=ssc.actual_year))
            for course in temp_data4:
                numcrhrsthissem = numcrhrsthissem + course.credit_hours
            ssclist.append([ssc.id, ssc.actual_year, ssc.semester, numcrhrsthissem])

    termdictionaryalphabetize={0:"aPre-TU", 1:"eFall", 2:"bJ-term", 3:"cSpring", 4:"dSummer"}
    termdictionary={0:"Pre-TU", 1:"Fall", 2:"J-term", 3:"Spring", 4:"Summer"}

    # First, form an array containing the info for the "create your own" type courses
    cyocarray=[]
    for cyoc in temp_data2:
        if cyoc.equivalentcourse:
            equivcourse_namestring = ' (equivalent to: '+cyoc.equivalentcourse.number+')'
        else:
            equivcourse_namestring =''
        cyocarray.append([cyoc.actual_year, termdictionaryalphabetize[cyoc.semester],
                          cyoc.name+equivcourse_namestring,
                          cyoc.number, cyoc.credit_hours, cyoc.sp, cyoc.cc, cyoc.id])

    datablock=[]
    # "Alphabetize" the semesters.
    for sem1 in temp_data:
        semestercontainscyoc = False
        temp_course_name=[]
        semtemp = sem1.semester
        act_year_temp = sem1.actual_year
        semid = sem1.id
        total_credit_hrs = 0
        tempcyocarray =[]
        ii = 0
        # Assemble any prereq or coreq comments into a list....
        precocommentlist=[]
        for row in co_not_met_list:
            if row[0] == semid:
                precocommentlist.append(row[4] + " is a corequisite for " +
                                        row[2] + "; the requirement is currently not being met.")
        for row in pre_not_met_list:
            if row[0] == semid:
                precocommentlist.append(row[4] + " is a prerequisite for " +
                                        row[2] + "; the requirement is currently not being met.")
        for row in cyocarray:
            if row[0] == act_year_temp and row[1] == termdictionaryalphabetize[semtemp]:
                tempcyocarray.append(ii)
            ii=ii+1
        for indexii in reversed(tempcyocarray):
            temparray = cyocarray.pop(indexii)
            total_credit_hrs = total_credit_hrs+temparray[4]
            iscyoc = True
            semestercontainscyoc = True
            temp_course_name.append({'cname': temparray[2],
                                   'cnumber': temparray[3],
                                   'ccredithours': temparray[4],
                                   'sp': temparray[5],
                                   'cc': temparray[6],
                                   'iscyoc': iscyoc,
                                   'courseid': temparray[7],
                                   'othersemesters': []})
        for cc in sem1.courses.all():
            iscyoc = False
            total_credit_hrs = total_credit_hrs + cc.credit_hours
            allsemestersthiscourse = cc.semester.all()
            # Form an array of other semesters when this course is offered.
            semarraynonordered = []
            for semthiscourse in allsemestersthiscourse:
                yearotheroffering=semthiscourse.actual_year
                semotheroffering=semthiscourse.semester_of_acad_year
                keepthisone = True
                if yearotheroffering == act_year_temp and semotheroffering == semtemp:
                    keepthisone = False
                else:
                    elementid = -1
                    for row in ssclist:
                        if yearotheroffering == row[1] and semotheroffering == row[2]:
                            elementid = row[0]
                            numhrsthissem = row[3]
                    if elementid == -1:
                        # Id wasn't found, meaning this course offering is not during a
                        # time the student is at TU.
                        keepthisone = False
                if keepthisone == True:
                    semarraynonordered.append([yearotheroffering, semotheroffering,
                                               elementid, numhrsthissem])

            semarrayreordered=reorder_list(semarraynonordered)
            semarray=[]
            for row in semarrayreordered:
                semarray.append({'semester': named_year(enteringyear, row[0], row[1]),
                                 'courseid': row[2],
                                 'numhrsthissem': row[3]})

            temp_course_name.append({'cname': cc.name,
                                   'cnumber': cc.number,
                                   'ccredithours': cc.credit_hours,
                                   'sp': cc.sp,
                                   'cc': cc.cc,
                                   'iscyoc': iscyoc,
                                   'courseid': cc.id,
                                   'othersemesters':semarray})
        datablock.append({'year': act_year_temp,
                          'semestername': termdictionaryalphabetize[semtemp],
                          'studentname': sem1.student.name,
                          'listofcourses': temp_course_name,
                          'semesterid': sem1.id,
                          'totalcredithours': total_credit_hrs,
                          'semestercontainscyoc': semestercontainscyoc,
                          'precocommentlist': precocommentlist})
        total_credit_hours_four_years = total_credit_hours_four_years + total_credit_hrs

    # initial sort
    datablock2 = sorted(datablock, key=lambda rrow: (rrow['year'], rrow['semestername']))
    datablock3 = []
    for row in datablock2:
        row['semestername'] = row['semestername'][1:]
        datablock3.append(row)

    if total_credit_hours_four_years > 159:
        credithrmaxreached = True
    else:
        credithrmaxreached = False

    # Now organize the 21 (pre-TU, plus 4 for each of freshman,..., super-senior) lists
    # into 6 (pre-TU, freshman, etc.)

    # First check to make sure that there are, in fact, 21 rows....
    if len(datablock3)!=21:
        assert False, locals()

    yearlist=[[0], [1, 2, 3, 4],
              [5, 6, 7, 8], [9, 10, 11, 12],
              [13, 14, 15, 16], [17, 18, 19, 20]]
    datablock4=[]
    for year in yearlist:
        temp=[]
        for semester in year:
            temp.append(datablock3[semester])
        datablock4.append(temp)

    context = {'student': student_local,
               'datablock': datablock4,
               'totalhrsfouryears': total_credit_hours_four_years,
               'credithrmaxreached': credithrmaxreached,
               'isProfessor': isProfessor}
    return render(request, 'fouryearplan.html', context)

CourseInfo = namedtuple("CourseInfo", "name, semester, actual_year, credit_hours, sp, cc, iscyoc, number, id, met")
class FourYearPlanCourses(object):
    def __init__(self):
        self.collection = {}
        self.sp_list = []
        self.cc_list = []

    def __contains__(self, course_number):
        """
        Returns True if course_number in collection.
        """
        return course_number in self.collection

    def __getitem__(self, course_number):
        """
        Returns course corresponding to course_number in collection.
        """
        return self.collection[course_number]

    def __setitem__(self, course_number, value):
        self.collection[course_number] = value

    def add(self, *courses):
        def sp_cc_info(course):
            termdictionary={0:"Pre-TU", 1:"Fall", 2:"J-term", 3:"Spring", 4:"Summer"}

            semester = course.semester
            course_name = course.name
            course_number = course.number
            actual_year = course.actual_year

            if semester == 0:
                comment = "Pre-TU"
            else:
                comment = termdictionary[semester]+', '+str(actual_year)
            return {'cname':course_name, 'comment':comment, 'cnumber':course_number}

        for course in courses:
            self.collection[course.number] = course
            if course.sp:
                self.sp_list.append(sp_cc_info(course))
            if course.cc:
                self.cc_list.append(sp_cc_info(course))

    @property
    def courses(self):
        return [self.collection[course_number] for course_number in self.collection]

    @property
    def num_sps(self):
        return len(self.sp_list)

    @property
    def num_ccs(self):
        return len(self.cc_list)

    @property
    def total_credit_hours(self):
        return sum(course.credit_hours for course in self.courses)

def major_courses(major):
    """
    Given a major, returrns a list of all of the courses for each of the requirements blocks.
    """
    pass

@login_required
def display_grad_audit(request):
    # NOTES:
    #       1. In the current approach no double-counting of courses is allowed, since the course gets popped
    #          out of studentcourselist as soon as it meets a requirement.  Maybe this should be changed?  The problem
    #          could be that in some situations, maybe a course is not ALLOWED to double-count.  Maybe if one course
    #          is used to meet requirements in two requirement blocks, a flag could be set and a warning given, in case
    #          such double-counting is not allowed.
    #       2. There is some redundancy between this function and display_four_year_plan.  Some methods/functions could
    #          probably be written that would serve in both places

    if request.user.is_student():
        isProfessor = False
        student_local = request.user.student
    else:
        isProfessor = True
        student_local = request.user.professor.advisee
        if student_local is None:
            # No advisee currently selected; go pick one first
            return redirect('update_advisee', 2)

    temp_data = StudentSemesterCourses.objects.filter(student=student_local)
    temp_data3 = CreateYourOwnCourse.objects.filter(student=student_local)

    studentid = temp_data[0].student.id
    pre_not_met_list, co_not_met_list = pre_co_req_check(studentid)

    if student_local.major is None:
        hasMajor = False
        context = {'student': student_local,'isProfessor': isProfessor,'hasMajor':hasMajor}
        return render(request, 'graduationaudit.html', context)
    else:
        hasMajor = True
        studentmajor = student_local.major

    enteringyear = student_local.entering_year

#
# OVERVIEW of majordatablock:
#
# one of the main tasks performed here is to construct "majordatablock";
# "majordatablock" is a list of dictionaries that is eventually reordered and renamed "majordatablock2";
# aside from the reordering, these two lists are identical.
# majordatablock2 is *the* main chunk of data that is sent to the graduationaudit template.
#
# each element in the list (majordatablock) is a "requirement block";
# the requirement blocks have the following keywords:
#
#  - listorder: an integer used to determine what order the requirements should be displayed in
#  - blockname: the name of the requirement block; this will show up on the grad audit page
#  - andorcomment: string that states whether all or only some of the courses need to be taken
#  - mincredithours: minimum # of credit hours to satisfy the requirement
#  - textforuser: optional text to display to the user
#  - credithrs: total # credit hours in this block so far
#  - creditsok: whether or not the # credit hours taken so far matches the required number
#  - blockcontainscyoc: whether or not the requirement block currently contains a course that is
#                       of the "create your own" variety; if so, a not is put at the bottom
#  - precocommentlist: list of comments about prereqs or coreqs not being met, if that is the case
#  - courselist: list of dictionaries; each element in the list represents a course
#                keywords are the following:
#      - cname: course name
#      - cnumber: course number (e.g., PHY311)
#      - ccredithrs': # credit hours required for this course requirement
#      - sp: boolean
#      - cc: boolean
#      - comment: comment to be associated with the course
#      - numcrhrstaken: # of credit hours taken for this requirement
#      - courseid: course id in the database
#      - sscid: id of the studentsemestercourse object associated with this course
#      - iscyoc: boolean; TRUE if the course is of the "create your own" variety
#      - othersemester: list of dictionaries; each element represents another
#                       semester during which this course could be taken;
#                       keywords are the following:
#           - semester: string that identifies the other semester (e.g., 'junior spring (2015)')
#           - courseid: *poorly named*; actually the id of the studentsemestercourse object for the course in the other semester
#           - numhrsthissem: # credit hrs currently being taken in the other semester
#

    # ssclist is used below to construct "semarray", which is eventually assigned to the keyword "othersemester" (see above)
    ssclist=[]

    for ssc in temp_data:
        if ssc.semester !=0:  # don't include pre-TU ssc object here
            numcrhrsthissem = student_local.num_credit_hours(ssc)
            ssclist.append([ssc.id, ssc.actual_year, ssc.semester, numcrhrsthissem])


    # the following assembles studentcourselist and coursenumberlist;
    # studentcourselist is a list of all courses in the student's plan;
    # elements in the list correspond to information about the courses (name, semester, etc.)
    # coursenumberlist is a parallel list to studentcourselist, but it just contains course numbers (e.g., PHY311)

    student_courses = FourYearPlanCourses()


    # loop through all studentsemestercourse objects for the student, picking out the courses in the student's plan
    for ssc in temp_data:
        numhrsthissemester = 0
        for course in ssc.courses.all():
            iscyoc = False

            course_info = CourseInfo(name = course.name,
                                     semester = ssc.semester,
                                     actual_year = ssc.actual_year,
                                     credit_hours = course.credit_hours,
                                     sp = course.sp,
                                     cc = course.cc,
                                     iscyoc = iscyoc,
                                     number = course.number,
                                     id = ssc.id,
                                     met = False)
            student_courses.add(course_info)

    # Now add in the user-created ("create your own") type courses.
    for cyoc in temp_data3:
        iscyoc = True
        if cyoc.equivalentcourse:
            equivcourse_namestring = ' (equivalent to: '+cyoc.equivalentcourse.number+')'
            eqcoursenum = cyoc.equivalentcourse.number
        else:
            equivcourse_namestring =''
            eqcoursenum = ''


        course_info = CourseInfo(name = cyoc.name + equivcourse_namestring,
                                 semester = ssc.semester,
                                 actual_year = ssc.actual_year,
                                 credit_hours = cyoc.credit_hours,
                                 sp = cyoc.sp,
                                 cc = cyoc.cc,
                                 iscyoc = iscyoc,
                                 number = cyoc.number,
                                 id = cyoc.id,
                                 met = False)

        student_courses.add(course_info)


    SPlist = student_courses.sp_list
    CClist = student_courses.cc_list
    numSPs = student_courses.num_sps
    numCCs = student_courses.num_ccs
    # the following checks to see if the SP and CC requirements have been met
    if numSPs < 2:
        SPreq = False
    else:
        SPreq = True
    if numCCs == 0:
        CCreq = False
    else:
        CCreq = True

    total_credit_hours_four_years= student_courses.total_credit_hours


    # the following code assembles majordatablock (described in detail above);
    # the general approach is the following:
    # - the outer loop cycles through each requirement block for the student's major
    #   - the next loop cycles through each course in the list of courses within the requirement block
    #   - if a course in the student's plan ("studentcourselist") matches a course in a requirement block, it is
    #     popped out of the student's course list (Edit: not anymore.)
    #   - for most courses in the requirement block, a list of semesters is constructed, showing when the course
    #     could be taken (or moved to, if it is currently being taken during some semester)

    majordatablock = []
    # loop over requirement blocks for the student's chosen major
    for mr in studentmajor.major_requirements.all():
        precocommentlist=[]
        requirementblockcontainscyoc = False
        courselisttemp=[]
        if mr.AND_or_OR_Requirement == 1:
            AND_OR_comment = "All of the following are required."
        else:
            AND_OR_comment = "Choose from the following."

        total_credit_hours_so_far = 0
        # loop over courses within each requirement block
        for course in mr.courselist.all():
            iscyoc=False
            cnumber=course.number
            course_id = course.id
            numcrhrstaken = ''
            sscid = -1
            requirement_met = cnumber in student_courses
            # if the requirement is met, pop the course out of the student's list of courses
            if requirement_met:
                # Assemble any prereq or coreq comments into a list.
                for row in co_not_met_list:
                    if row[1] == course_id:
                        precocommentlist.append(row[4] + " is a corequisite for " +
                                                row[2] + "; the requirement is currently not being met.")
                for row in pre_not_met_list:
                    if row[1] == course_id:
                        precocommentlist.append(row[4] + " is a prerequisite for " +
                                                row[2] + "; the requirement is currently not being met.")

                student_course = student_courses[cnumber]
                student_courses[cnumber] = student_course._replace(met=True)
                numcrhrstaken = student_course.credit_hours

                total_credit_hours_so_far+=numcrhrstaken
                semester = student_course.semester
                actual_year = student_course.actual_year
                sscid = student_course.id
                iscyoc = student_course.iscyoc

                if semester == 0:
                    commentfirstpart = "Pre-TU"
                else:
                    commentfirstpart = named_year(enteringyear, actual_year, semester)
                if iscyoc:
                    # This is a "create your own course...need to exercise some caution!
                    requirementblockcontainscyoc = True
                    comment = "{}; ({})*".format(commentfirstpart, course.number)
                else:
                    # Regular TU course...no problem....
                    comment = commentfirstpart
            else:
                # NOTE: comment is a string if there is a course scheduled; if not, it is
                # False, in which case it is used as a flag for things within graduation
                # html page
                comment = False
                semester = -1
                actual_year = -1

            # If course is user-defined ("cyoc"), then don't show options for moving the
            # course, so skip the next part
            semarray = []

            if not iscyoc:

                allsemestersthiscourse = course.semester.all()

                # Form an array of other semesters when this course is offered.
                semarraynonordered = []

                for semthiscourse in allsemestersthiscourse:
                    yearotheroffering = semthiscourse.actual_year
                    semotheroffering = semthiscourse.semester_of_acad_year
                    keepthisone = True
                    if yearotheroffering == actual_year and semotheroffering == semester:
                        keepthisone = False
                    else:
                        elementid = -1
                        for course_id, actual_year,semester, credit_hours in ssclist:
                            if yearotheroffering == actual_year and semotheroffering == semester:
                                elementid = course_id
                                numhrsthissem = credit_hours
                        if elementid == -1:
                            # Id wasn't found, meaning this course offering is not during
                            # a time the student is at TU
                            keepthisone = False

                    if keepthisone:
                        semarraynonordered.append([yearotheroffering,
                                                   semotheroffering,
                                                   elementid,
                                                   credit_hours])


                semarrayreordered=reorder_list(semarraynonordered)

                for row in semarrayreordered:
                    semarray.append({'semester': named_year(enteringyear, row[0], row[1]),
                                     'courseid': row[2],
                                     'numhrsthissem': row[3]})

            courselisttemp.append({'cname': course.name,
                                   'cnumber': course.number,
                                   'ccredithrs': course.credit_hours,
                                   'sp': course.sp,
                                   'cc': course.cc,
                                   'comment': comment,
                                   'numcrhrstaken': numcrhrstaken,
                                   'courseid': course.id,
                                   'othersemesters': semarray,
                                   'sscid': sscid,
                                   'iscyoc': iscyoc})

        if total_credit_hours_so_far>=mr.minimum_number_of_credit_hours:
            credits_ok=True
        else:
            credits_ok=False

        # the following appends a new dictionary for this particular requirement block
        majordatablock.append({'listorder': mr.list_order,
                               'blockname': mr.display_name,
                               'andorcomment': AND_OR_comment,
                               'mincredithours': mr.minimum_number_of_credit_hours,
                               'textforuser': mr.text_for_user,
                               'courselist': courselisttemp,
                               'credithrs': total_credit_hours_so_far,
                               'creditsok': credits_ok,
                               'blockcontainscyoc': requirementblockcontainscyoc,
                               'precocommentlist': precocommentlist})

        # the following reorders majordatablock in the desired order
        # (this ordering is defined when the requirement blocks are defined in the first place)
        majordatablock = sorted(majordatablock, key=lambda rrow: (rrow['listorder']))

        # anything remaining in the studentcourselist at this point has not been used to meet a
        # course requirement in one of the requirement blocks;  unusedcourses keeps track of these courses
        unusedcourses=[]
        unusedcredithours=0
        for course in student_courses.courses:
            # the last element in course is whether it was met. Earlier in the code this is
            # initialized to false, and set to true it is met.
            if not course.met:
                unusedcredithours=unusedcredithours+course[3]
                if course.semester == 0:
                    comment = "Pre-TU"
                else:
                    comment = named_year(enteringyear, course.actual_year, course.semester)
                    unusedcourses.append({'cname':course.name,'cnumber':course.number,
                                          'ccredithrs':course.credit_hours,'sp':course.sp,'cc':course.cc,
                                          'comment':comment})

        # the following checks to see if the SP and CC requirements have been met
        if numSPs < 2:
            SPreq = False
        else:
            SPreq = True
        if numCCs == 0:
            CCreq = False
        else:
            CCreq = True

    if total_credit_hours_four_years > 159:
        credithrmaxreached = True
    else:
        credithrmaxreached = False

    context = {'student': student_local,
               'majordatablock': majordatablock,
               'unusedcourses': unusedcourses,
               'unusedcredithours': unusedcredithours,
               'SPlist': SPlist,
               'CClist': CClist,
               'numSPs': numSPs,
               'numCCs': numCCs,
               'SPreq': SPreq,
               'CCreq': CCreq,
               'totalhrsfouryears': total_credit_hours_four_years,
               'credithrmaxreached': credithrmaxreached,
               'isProfessor': isProfessor,
               'hasMajor': hasMajor}

    return render(request, 'graduationaudit.html', context)

@login_required
def add_create_your_own_course(request,id):
    # The following list should just have one element(!)...hence "listofstudents[0]" is
    # used in the following....
    listofstudents = Student.objects.all().filter(user=request.user)
    ssc = StudentSemesterCourses.objects.get(pk = id)
    request_id = request.user.get_student_id()
    incoming_id = ssc.student.id
    if request_id != incoming_id:
        return redirect('profile')
    year=ssc.actual_year
    semester=ssc.semester

    if request.method == 'POST':
        form = AddCreateYourOwnCourseForm(request.POST)
        if form.is_valid():
            new_cyoc = CreateYourOwnCourse(student = listofstudents[0])
            new_cyoc.name = form.cleaned_data['name']
            new_cyoc.number = form.cleaned_data['number']
            new_cyoc.credit_hours = form.cleaned_data['credit_hours']
            new_cyoc.sp = form.cleaned_data['sp']
            new_cyoc.cc = form.cleaned_data['cc']
            new_cyoc.semester = semester
            new_cyoc.actual_year = year
            new_cyoc.equivalentcourse = form.cleaned_data['equivalentcourse']
            new_cyoc.save()
            return redirect('update_student_semester', id)
        else:
            return render(request, 'addcreateyourowncourse.html', {'form': form})
    else:
        # User is not submitting the form; show them the blank add create your own course
        # form.
        form = AddCreateYourOwnCourseForm()
        context = {'form': form}
        return render(request, 'addcreateyourowncourse.html', context)


@login_required
def update_create_your_own_course(request,id,id2):
    instance = CreateYourOwnCourse.objects.get(pk = id2)
    ssc = StudentSemesterCourses.objects.get(pk = id)
    request_id = request.user.get_student_id()
    incoming_id = ssc.student.id
    incoming_id2 = instance.student.id
    if request_id != incoming_id:
        return redirect('profile')
    if request_id != incoming_id2:
        return redirect('profile')

    if request.method == 'POST':
        form = AddCreateYourOwnCourseForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('update_student_semester', id)
        else:
            return render(request, 'addcreateyourowncourse.html', {'form': form})
    else:
        # User is not submitting the form; show them the blank add create your own course form
        form = AddCreateYourOwnCourseForm(instance=instance)
        context = {'form': form}
        return render(request, 'addcreateyourowncourse.html', context)


# In the following, "where_from" is:
#    0: fouryearplan
#    1: gradaudit
#    2: updatesemester
# "id" is:
#    0: coming from fouryearplan (doesn't matter; not used)
#    0: coming from gradaudit (doesn't matter; not used)
#    ssc id: coming from updatesemester
@login_required
def delete_create_your_own_course(request, where_from, id, id2):
    instance = CreateYourOwnCourse.objects.get(pk = id2)

    request_id = request.user.get_student_id()
    incoming_id2 = instance.student.id
    if request_id != incoming_id2:
        return redirect('profile')

    instance.delete()
    if int(where_from) == 2:
        return redirect('update_student_semester', id)
    elif int(where_from) == 0:
        return redirect('four_year_plan')
    else:
        return redirect('grad_audit')

# In the following, where_from is:
#    0: fouryearplan
#    1: gradaudit
# ssc_id is id of the ssc object
# course_id is id of the course itself
@login_required
def delete_course_inside_SSCObject(request, where_from, ssc_id, course_id):
    instance = StudentSemesterCourses.objects.get(pk = ssc_id)

    request_id = request.user.get_student_id()
    incoming_id = instance.student.id
    if request_id != incoming_id:
        return redirect('profile')

    StudentSemesterCourses.objects.get(pk = ssc_id).courses.remove(course_id)
    if int(where_from) == 0:
        return redirect('four_year_plan')
    else:
        return redirect('grad_audit')

# In the following, where_from is:
#    0: fouryearplan
#    1: gradaudit
#
# src_ssc_id is id of the current ssc object (from which the course needs to be deleted); set to
# "-1" if course is not currently being taken (which can happen if request comes from the
# grad audit page)
#
# dest_ssc_id is the id of the new ssc object (to which the course needs to be added)
#
# course_id is the id of the course itself
#
# This routine failed once and I don't know why!!! Said columns for course_id and ssc_id
# were not unique, or something, and gave an integrity error.
@login_required
def move_course_to_new_SSCObject(request, where_from, src_ssc_id, dest_ssc_id, course_id):
    src_ssc_id_int = int(src_ssc_id)

    # Using dest_ssc_id here instead of src_ssc_id, since sometimes we are only creating a
    # new course, and not deleting an old one.
    dest_ssc = StudentSemesterCourses.objects.get(pk=dest_ssc_id)
    request_id = request.user.get_student_id()
    incoming_id = dest_ssc.student.id
    if request_id != incoming_id:
        return redirect('profile')

    if src_ssc_id_int != -1:
        # If src_ssc_id == -1, the course is not being taken, so there is nothing to remove
        instance_old = StudentSemesterCourses.objects.get(pk=src_ssc_id_int)
        incoming_id_old = instance_old.student.id
        if request_id != incoming_id_old:
            return redirect('profile')
        StudentSemesterCourses.objects.get(pk=src_ssc_id).courses.remove(course_id)
    StudentSemesterCourses.objects.get(pk=dest_ssc_id).courses.add(course_id)
    if int(where_from) == 0:
        return redirect('four_year_plan')
    else:
        return redirect('grad_audit')


def pre_co_req_check(studentid):
    """Check prereqs and coreqs for all TU courses in student's plan;
    results returned as two lists of id #s"""
    studentdata = Student.objects.all().filter(pk=studentid)
    student = studentdata[0]
    sscdata = StudentSemesterCourses.objects.all().filter(student=student)
    cyocdata = CreateYourOwnCourse.objects.all().filter(student=student)

    enteringyear = student.entering_year
    courselist = []
    course_id_dict=dict()
    semesterdict=dict()
    for ssc in sscdata:
        sscid = ssc.id
        actual_year = ssc.actual_year
        semester = ssc.semester
        semestersincebeginning = get_semester_from_beginning(enteringyear, actual_year, semester)
        semesterdict[semestersincebeginning]=sscid
        for course in ssc.courses.all():
            course_id_dict[course.id]=course.number
            prereq = []
            coreq = []
            for pre in course.prereqs.all():
                prereq.append(pre.id)
                course_id_dict[pre.id]=pre.number
            for co in course.coreqs.all():
                coreq.append(co.id)
                course_id_dict[co.id]=co.number
            courselist.append([semestersincebeginning, actual_year, semester, course.id, prereq, coreq, sscid])

    # Now in add in "create your own" type courses that have exact equivalents at TU....
    # note: in the way I have done this, it is assumed that the course functions exactly
    # as a TU course; that is, it has the same prereqs and coreqs, it satisfies prereqs
    # and coreqs, etc.
    for cyoc in cyocdata:
        if cyoc.equivalentcourse is not None:
            semester = cyoc.semester
            actual_year = cyoc.actual_year
            semestersincebeginning = get_semester_from_beginning(enteringyear, actual_year, semester)
            sscid = semesterdict[semestersincebeginning]
            prereq = []
            coreq = []
            course = cyoc.equivalentcourse
            course_id_dict[course.id]=course.number
            for pre in course.prereqs.all():
                prereq.append(pre.id)
                course_id_dict[pre.id]=pre.number
            for co in course.coreqs.all():
                coreq.append(co.id)
                course_id_dict[co.id]=co.number
            courselist.append([semestersincebeginning, actual_year, semester, course.id, prereq, coreq, sscid])

    # Now need to do the actual check....
    all_pre_list = []
    all_co_list = []
    pre_not_met_list = []
    co_not_met_list = []
    courselist2=courselist
    for row in courselist:
        coursesemester = row[0]
        # Don't do prereq and coreq check for pre-TU courses, although pre-TU courses can
        # be pre and coreqs for OTHER courses
        if coursesemester != 0:
            prereq_list = row[4]
            coreq_list = row[5]
            sscid = row[6]
            course_id = row[3]
            # Now for each preid, need to find the semester that that course was taken,
            # check that it was earlier than course itself
            for preid in prereq_list:
                prereqsatisfied = False
                for row2 in courselist2:
                    course_idtemp = row2[3]
                    coursesemesterpre = row2[0]
                    if course_idtemp==preid and coursesemesterpre<coursesemester:
                        prereqsatisfied = True
                        all_pre_list.append([course_id_dict[course_id],course_id_dict[preid]])
                if prereqsatisfied == False:
                    pre_not_met_list.append([sscid, course_id, course_id_dict[course_id],
                                          preid, course_id_dict[preid]])
            # Now for each coid, need to find the semester that that course was taken,
            # check that it was <= than semester for course itself
            for coid in coreq_list:
                coreqsatisfied = False
                for row2 in courselist2:
                    course_idtemp = row2[3]
                    coursesemesterco = row2[0]
                    if course_idtemp==coid and coursesemesterco<=coursesemester:
                        coreqsatisfied = True
                        all_co_list.append([course_id_dict[course_id],course_id_dict[coid]])
                if coreqsatisfied == False:
                    co_not_met_list.append([sscid,
                                            course_id,
                                            course_id_dict[course_id],
                                            coid,
                                            course_id_dict[coid]])

    return pre_not_met_list, co_not_met_list

def get_semester_from_beginning(enteringyear, actual_year, semester):
    """Return semester #, starting with "0" for pre-TU, "1" for freshman fall, etc."""
    if semester == 0:
        semesteroutput = 0
    else:
        if semester == 1:
            semesteroutput = 4 * (actual_year - enteringyear) + semester
        else:
            semesteroutput = 4 * (actual_year - enteringyear - 1) + semester
    return semesteroutput

def named_year(enteringyear, actual_year, semester):
    termdict = {1: "fall", 2: "j-term", 3: "spring", 4: "summer"}
    yeardict = {0: "freshman", 1: "sophomore", 2: "junior", 3: "senior", 4: "supersenior"}
    if semester == 1:
        yeardiff = actual_year - enteringyear
    else:
        yeardiff = actual_year - enteringyear - 1
    return yeardict[yeardiff]+' '+termdict[semester]+' ('+str(actual_year)+')'

# list is assumed to be of the form:
#     - [[year, sem, id],[year, sem, id],...]; or
#     - [[year, sem, id, numcrhrssem],[year, sem, id, numcrhrssem],...]
def reorder_list(listin):
    alphdict={2:'a', 3:'b', 4:'c', 1:'d'}
    revalphdict={'a':2, 'b':3, 'c':4, 'd':1}
    new_list=[]
    for row in listin:
        if len(row) == 4:
            new_list.append([row[0],alphdict[row[1]],row[2], row[3]])
        else:
            new_list.append([row[0],alphdict[row[1]],row[2]])
    new_list2=sorted(new_list, key=lambda rrow: (rrow[0], rrow[1]))
    new_list3=[]
    for row in new_list2:
        if len(row) == 4:
            new_list3.append([row[0],revalphdict[row[1]],row[2], row[3]])
        else:
            new_list3.append([row[0],revalphdict[row[1]],row[2]])
    return new_list3

def prepopulate_student_semesters(studentid):
    student = Student.objects.all().get(pk = studentid)
    major = student.major
    enteringyear=student.entering_year
    datalist = PrepopulateSemesters.objects.all().filter(Q(major=major) &
                                                         Q(enteringyear__year=enteringyear))
    temp_data=StudentSemesterCourses.objects.all().filter(student=student)
    ssclist=[]
    for ssc in temp_data:
        if ssc.semester !=0:  # don't include pre-TU ssc object here
            ssclist.append([ssc.id, ssc.actual_year, ssc.semester])

    if len(datalist) == 0:
        return False

    # Assume that there is only one PrepopulateSemester object for a given major and
    # entering year!!!
    popsemdata=datalist[0]

    semarray = []

    semarray.append([enteringyear,     1, popsemdata.freshman_fall_courses.all()])
    semarray.append([enteringyear + 1, 2, popsemdata.freshman_jterm_courses.all()])
    semarray.append([enteringyear + 1, 3, popsemdata.freshman_spring_courses.all()])
    semarray.append([enteringyear + 1, 4, popsemdata.freshman_summer_courses.all()])

    semarray.append([enteringyear + 1, 1, popsemdata.sophomore_fall_courses.all()])
    semarray.append([enteringyear + 2, 2, popsemdata.sophomore_jterm_courses.all()])
    semarray.append([enteringyear + 2, 3, popsemdata.sophomore_spring_courses.all()])
    semarray.append([enteringyear + 2, 4, popsemdata.sophomore_summer_courses.all()])

    semarray.append([enteringyear + 2, 1, popsemdata.junior_fall_courses.all()])
    semarray.append([enteringyear + 3, 2, popsemdata.junior_jterm_courses.all()])
    semarray.append([enteringyear + 3, 3, popsemdata.junior_spring_courses.all()])
    semarray.append([enteringyear + 3, 4, popsemdata.junior_summer_courses.all()])

    semarray.append([enteringyear + 3, 1, popsemdata.senior_fall_courses.all()])
    semarray.append([enteringyear + 4, 2, popsemdata.senior_jterm_courses.all()])
    semarray.append([enteringyear + 4, 3, popsemdata.senior_spring_courses.all()])
    semarray.append([enteringyear + 4, 4, popsemdata.senior_summer_courses.all()])

    for sem in semarray:
        tempsem=sem[1]
        tempyear=sem[0]
        for ssc in ssclist:
            if ssc[1] == tempyear and ssc[2] == tempsem:
                sscid=ssc[0]
                for course in sem[2]:
                    course_id = course.id
                    StudentSemesterCourses.objects.get(pk = sscid).courses.add(course_id)

    return True

# In the following, "where_from" is:
# 0: profile
# 1: fouryearplan
# 2: graduaudit
# 3: advising note
@login_required
def update_advisee(request, where_from):
    if request.user.is_student():
        return redirect('profile')

    professor = request.user.professor

    if request.method == 'POST':
        form = AddAdviseeForm(request.POST, instance=professor)
        if form.is_valid():
            form.save()
            if int(where_from) == 0:
                return redirect('profile')
            elif int(where_from) == 1:
                return redirect('four_year_plan')
            elif int(where_from) == 2:
                return redirect('grad_audit')
            elif int(where_from) == 3:
                return redirect('notes')
            else:
                return redirect('profile')
        else:
            return render(request, 'addadvisee.html', {'form': form})
    else:
        # User is not submitting the form; show them the blank add advisee form
        form = AddAdviseeForm()
        context = {'form': form}
        return render(request, 'addadvisee.html', context)

# PUT in something to limit search results!!!!  maybe only display first 20 records or
# something!!!  !!! do we need to do any security stuff here to make sure this is really a
# prof?!?
@login_required
def search(request):
    """Determine the # of students enrolled in courses that match a search request."""

    if request.user.is_student():
        return redirect('profile')

    if 'q' in request.GET and request.GET['q']:
        q = request.GET['q']
        courses = Course.objects.filter(number__icontains=q)
        semesterdict = {1:"Fall", 2:"J-term", 3:"Spring", 4:"Summer"}
        datablock = []
        for course in courses:
            semlist = []

            # This approach is only going to capture non-pre-TU courses...which is good.
            for availablesemester in course.semester.all():
                actual_sem = availablesemester.semester_of_acad_year
                actual_year = availablesemester.actual_year

                # Now need to find all the ssc records for each of these courses....
                sscdata = StudentSemesterCourses.objects.filter(semester=actual_sem)
                numberstudents=0
                studentlist=[]
                for ssc in sscdata:
                    if ssc.actual_year == actual_year:
                        for courseinssc in ssc.courses.all():
                            if courseinssc.id == course.id:
                                numberstudents=numberstudents + 1
                                studentlist.append(ssc.student.name)
                semlist.append([actual_year, actual_sem, numberstudents,availablesemester.id])
            semlist2 = reorder_list(semlist)
            semlistfinal = []
            for row in semlist2:
                semlistfinal.append([semesterdict[row[1]] + ", " + str(row[0]),row[2], row[3]])
            datablock.append([course.id, course.name, course.number, semlistfinal])
        context={'courses':courses,'query':q, 'datablock':datablock}
        return render(request, 'course_enrollment_results.html',context)
    else:
        return redirect('profile')


@login_required
def view_enrolled_students(request,course_id,semesterid):
    """Display students enrolled in a given course and semester"""

    if request.user.is_student():
        return redirect('profile')

    actual_sem = Semester.objects.get(pk=semesterid).semester_of_acad_year
    actual_year = Semester.objects.get(pk=semesterid).actual_year
    sscdata = StudentSemesterCourses.objects.filter(semester=actual_sem)
    course = Course.objects.get(pk=course_id)
    course_name = course.name + ' (' + course.number + ')'
    semesterdict = {1:"Fall", 2:"J-term", 3:"Spring", 4:"Summer"}
    semester_name = semesterdict[actual_sem] + ' of ' + str(actual_year)
    studentlist=[]
    for ssc in sscdata:
        if ssc.actual_year == actual_year:
            for courseinssc in ssc.courses.all():
                if courseinssc.id == int(course_id):
                    studentlist.append(ssc.student.name)
    temp = request.META.items()
    context={'coursename':course_name,'semestername':semester_name,'studentlist':studentlist}
    return render(request, 'student_enrollment_results.html', context)

##############################################################################################################


@login_required
def department_load_summary(request):
    """Display loads for professors in the department"""

    user = request.user
    user_preferences = user.user_preferences.all()[0]

    department = user_preferences.department_to_view
    academic_year = user_preferences.academic_year_to_view.begin_on.year
    academic_year_string = str(academic_year)+'-'+str(academic_year+1)

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
    instructor_list=[]
    instructor_integer_list=[]
    for faculty in department.faculty.all():
        instructordict[faculty.last_name] = ii
        instructor_list.append(faculty.last_name)
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
                        instructor_load = load_hour_rounder(instructor.load_credit)
                        instructor_name = instructor.instructor.last_name
                        ii = instructordict[instructor_name]
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
            instructor_name = other_load.instructor.last_name
            if other_load.semester.year.begin_on.year == academic_year and instructor_name in instructor_list:
                semester_name = other_load.semester.name.name
                ii = instructordict[instructor_name]
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
    for instructor in instructor_list:
        instructor_data = []
        admin_data = []
        for row in data_list:
            if row['load_hour_list'][instructordict[instructor]][0] >= 0:
                instructor_data.append({'comment':row['comment'],
                                        'semester':row['semester'],
                                        'meetings_scheduled': row['meetings_scheduled'],
                                        'name': row['name'],
                                        'load_hour_list': [row['load_hour_list'][instructordict[instructor]][0],
                                                           row['load_hour_list'][instructordict[instructor]][1]],
                                        'id': row['id'],
                                        'load_hours': row['load_hours'],
                                        'meeting_times': row['meeting_times'],
                                        'rooms': row['rooms'],
                                        'number': row['number'],
                                        'load_difference': row['load_difference']
                                        })
        for row in admin_data_list:
            element = row['load_hour_list'][instructordict[instructor]]
            if element[0] > 0 or element[1] > 0 or element[2] > 0:
                admin_data.append({'load_type':row['load_type'],
                                   'load_hour_list':element,
                                   'id': row['id']
                                   })


        data_list_by_instructor.append({'instructor_id':instructordict[instructor],
                                        'course_info':instructor_data,
                                        'instructor':instructor,
                                        'admin_data_list':admin_data,
                                        'load_summary':faculty_summary_load_list[instructordict[instructor]],
                                        'total_load_hours':total_load_hours[instructordict[instructor]]
                                        })

    context={'course_data_list':data_list,
             'instructor_list':instructor_list,
             'faculty_load_summary':faculty_summary_load_list,
             'admin_data_list':admin_data_list,
             'total_load_hours':total_load_hours,
             'department':department,
             'academic_year':academic_year_string,
             'instructordict':instructordict,
             'instructorlist':instructor_list,
             'instructor_integer_list':instructor_integer_list,
             'data_list_by_instructor':data_list_by_instructor
             }
    return render(request, 'dept_load_summary.html', context)

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
    #    print department_abbrev
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

    for faculty_member in department.faculty.all().order_by('last_name'):
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
                table_title = faculty_member.last_name+' ('+semester_name+', '+str(academic_year)+')'
            else:
                table_title = faculty_member.last_name+' ('+semester_name+', '+str(academic_year+1)+')'

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

            for course_offering in course_offering_list:
                for scheduled_class in course_offering.scheduled_classes.all():
                    box_data, course_data, room_data = rectangle_coordinates_schedule(schedule, scheduled_class,
                                                                                      scheduled_class.day)
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
            data_this_professor.append({'prof_id': prof_id,
                                        'faculty_name': faculty_member.last_name,
                                        'json_box_list': json_box_list,
                                        'json_box_label_list':json_box_label_list,
                                        'json_grid_list': json_grid_list,
                                        'json_filled_row_list': json_filled_row_list,
                                        'json_table_text_list': json_table_text_list,
                                        'id':id,
                                        'schedule':schedule})
        data_list.append(data_this_professor)

    context={'data_list':data_list}
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
    for faculty_member in department.faculty.all():
        instructor_dict[faculty_member.last_name] = ii
        professor_list.append(faculty_member.last_name)
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
                    box_data, course_data, room_data = rectangle_coordinates_schedule(schedule, sc,
                                                                                      instructor_dict[instructor.instructor.last_name])
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

    context={'data_list':data_list}
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

            box_list = []
            box_label_list = []
            for sc in ScheduledClass.objects.filter(Q(room = room)&
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
            data_this_room.append({'room_id':roomid,
                                   'room_name': room.building.abbrev+' '+room.number,
                                  'json_box_list': json_box_list,
                                  'json_box_label_list':json_box_label_list,
                                  'json_grid_list': json_grid_list,
                                  'json_filled_row_list': json_filled_row_list,
                                  'json_table_text_list': json_table_text_list,
                                  'id':id,
                                  'schedule':schedule})
        data_list.append(data_this_room)

    context={'data_list':data_list}
    return render(request, 'room_schedule.html', context)


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


    context={'course_data_list':data_list, 'year_list':year_list, 'number_semesters': number_semesters}
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

    context={'registrar_data_list':registrar_data_list, 'department': department, 'academic_year': academic_year_string}
    return render(request, 'registrar_schedule.html', context)

@login_required
def update_other_load(request, id):
    """Update amounts of load and/or professor for 'other' (administrative-type) loads."""

    user = request.user
# assumes that users each have exactly ONE UserPreferences object
    user_preferences = user.user_preferences.all()[0]
    instance = OtherLoadType.objects.get(pk = id)
    print instance

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

