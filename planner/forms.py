from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from .models import *
from django.forms.widgets import RadioSelect
from .constants import NO_OVERLAP_TIME_BLOCKS, ENDING_BEFORE_BEGINNING_TIME

class RequirementForm(forms.ModelForm):
    class Meta:
        model = Requirement
        fields = "__all__"

    def clean(self):
        courses = self.cleaned_data.get('courses')
        requirements = self.cleaned_data.get('requirements')
        if bool(courses) == bool(requirements):
            raise forms.ValidationError("You need either courses or requirements but not both.")

        return self.cleaned_data

class RegistrationForm(forms.ModelForm):
    username = forms.CharField(label=('User Name'))
    email = forms.EmailField(label=('Email Address'))
    password = forms.CharField(label=('Password'),
                               widget=forms.PasswordInput(render_value=False))

    password1 = forms.CharField(label=('Verify Password'),
                                widget=forms.PasswordInput(render_value=False))

    class Meta:
        model = Student
        exclude = ('user',)

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError("That username is already taken; please select another.")

    def clean(self):
        password = self.cleaned_data.get('password')
        password1 = self.cleaned_data.get('password1')
        if password and password1 and password != password1:
            raise forms.ValidationError("The passwords did not match.  Please try again.")

        # something seems to be wrong here -- it doesn't associate the error with
        # password; it does throw the exception, I think (i.e., it returns an error), but
        # it doesn't specifically give the password error message....
        return self.cleaned_data

"""
class AddStudentSemesterForm(forms.ModelForm):
    class Meta:
        model = StudentSemesterCourses
        exclude = ('semester','year','student')

    def __init__(self, *args, **kwargs):
        actyear = kwargs.pop('actual_year')
        sem = kwargs.pop('semester')
        super (AddStudentSemesterForm,self).__init__(*args,**kwargs)
        if sem == 0:
            self.fields['courses'].queryset = Course.objects.all()
        else:
            self.fields['courses'].queryset = Course.objects.filter(Q(semester__actual_year=actyear)
                                                                    & Q(semester__semester_of_acad_year = sem))

    def clean_student(self):
        courses = self.cleaned_data['courses']
        return courses
"""

class AddSandboxYearForm(forms.ModelForm):

    class Meta:
        model = AcademicYear
        exclude = ('begin_on', 'end_on', 'department', 'is_hidden')

class UpdateSandboxYearForm(forms.ModelForm):

    class Meta:
        model = AcademicYear
        exclude = ('begin_on', 'end_on', 'department')

class AddNoteForm(forms.ModelForm):

    class Meta:
        model = Note
        exclude = ('department', 'year')

class AddTransferCourse(forms.ModelForm):

    class Meta:
        model = TransferCourse
        exclude = ('semester', 'student',)

"""
class AddAdviseeForm(forms.ModelForm):

    class Meta:
        model = Professor
        exclude = ('user', 'name')
"""

class UpdateMajorForm(forms.ModelForm):

    class Meta:
        model = Student
        exclude = ('user', 'name', 'entering_year')

class CourseOfferingRestrictedByYearForm(forms.ModelForm):

    def __init__(self, academic_year_id, *args, **kwargs):
        super (CourseOfferingRestrictedByYearForm,self).__init__(*args,**kwargs)
        self.fields['semester'].queryset = Semester.objects.filter(Q(year__id = academic_year_id))

    class Meta:
        model = CourseOffering
        exclude = ('course','instructor','crn',)

    def clean(self):
        load_available = self.cleaned_data.get('load_available')
        if load_available < 0:
            raise forms.ValidationError("Load available must be greater than or equal to zero.")

        return self.cleaned_data

class CourseSelectForm(forms.ModelForm):

    def __init__(self, dept_id, *args, **kwargs):
        department_id = dept_id
        super (CourseSelectForm,self).__init__(*args,**kwargs)
        self.fields['course'].queryset = Course.objects.filter(Q(subject__department__id = department_id))
    
    class Meta:
        model = CourseOffering
        exclude = ('semester','instructor','load_available','max_enrollment', 'comment', 'crn', 'semester_fraction', 'delivery_method',)

    def clean(self):
        return self.cleaned_data

class DynamicCourseSelectForm(forms.ModelForm):
    
    #subject = forms.ModelChoiceField(queryset=Subject.objects.none())

    subject = forms.ChoiceField(choices = ())

    def __init__(self, dept, *args, **kwargs):
        
        department = dept
        super (DynamicCourseSelectForm,self).__init__(*args,**kwargs)
        self.fields['course'].queryset = Course.objects.none()
        subjects =[['','---------']]
        for subj in Subject.objects.filter(department=department):
            subjects.append([subj.id,subj.abbrev])
        subjects.append(['','-- Subjects in Other Departments --'])
        for subj in Subject.objects.filter(~Q(department=department)):
            if department.is_trusted_by_subject(subj):
                subjects.append([subj.id,subj.abbrev])
        subjects_tuple = ([(subject[0], subject[1]) for subject in subjects])
        self.fields['subject'].choices = subjects_tuple
        self.initial['subject'] = subjects_tuple[0][0]

        if 'course' in self.data:
            try:
                subject_id = int(self.data.get('subject'))
                self.fields['course'].queryset = Course.objects.filter(subject_id=subject_id).order_by('number')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty course queryset
        # I think the following would be used for an update, although I'm not sure it would work....
        elif self.instance.pk:
            self.fields['course'].queryset = self.instance.subject.course_set.order_by('number')
    
    class Meta:
        model = CourseOffering
        exclude = ('semester','instructor','load_available','max_enrollment', 'comment', 'crn', 'semester_fraction',)

    def clean(self):
        return self.cleaned_data


class FacultySearchForm(forms.Form):
    name = forms.CharField(label=('Faculty Name'))

    def clean(self):
        return self.cleaned_data

class CourseOfferingForm(forms.ModelForm):

    class Meta:
        model = CourseOffering
        exclude = ('course', 'semester','instructor','crn','semester_fraction',)

    def clean(self):
        instructor = self.cleaned_data.get('instructor')
        max_enrollment = self.cleaned_data.get('max_enrollment')
        load_available = self.cleaned_data.get('load_available')
#        if max_enrollment < 0:
#            raise forms.ValidationError("Maximum enrollment must be greater than or equal to zero.")
        if load_available < 0:
            raise forms.ValidationError("Load available must be greater than or equal to zero.")

        return self.cleaned_data

class ScheduledClassForm(forms.ModelForm):

    class Meta:
        model = CourseOffering
        exclude = ('course_offering',)

#    def clean(self):
#        instructor = self.cleaned_data.get('instructor')
#        print instructor
#        max_enrollment = self.cleaned_data.get('max_enrollment')
#        if max_enrollment < 0:
#            raise forms.ValidationError("Maximum enrollment must be greater than or equal to zero.")

#        return self.cleaned_data

class BaseInstructorFormSet(forms.models.BaseInlineFormSet):

    def clean(self):
        if any(self.errors):
            return
        instructors = []
        instructor_error = False
        print('inside clean method')
        for subform in self.forms:
# need to do a "try/except" here b/c the form could have some blank rows if the user skips
# down and enters data a few rows down....
            try:
                instructor = subform.cleaned_data['instructor']
#                delete = subform.cleaned_data['delete']
#                print delete
                if not subform.cleaned_data["DELETE"]:
                    if instructor in instructors:
                        instructor_error = True
                        raise forms.ValidationError("Each instructor can only be listed once.")
                    instructors.append(instructor)
            except KeyError:
                pass
        #print('instructors: ', instructors)
        if not instructor_error:
            #print('no instructor error!')
            number_primary_instructors = 0
            for subform in self.forms:
                try:
                    print(subform.cleaned_data)
                    is_primary = subform.cleaned_data['is_primary']
                    to_be_deleted = subform.cleaned_data['DELETE']
            
                    print(is_primary)
                    print('delete?', to_be_deleted)
#                   delete = subform.cleaned_data['delete']
#                   print delete
                    if (is_primary) and (not to_be_deleted): 
                        number_primary_instructors += 1
                except KeyError:
            #    print('key error')
                    pass
            if (len(instructors) > 1) and (number_primary_instructors != 1):
                raise forms.ValidationError("Please choose one instructor to be the primary instructor.")


class InstructorForm(forms.ModelForm):

    def __init__(self, department_id, year, faculty_to_view_ids, course_offering, *args, **kwargs):
        super (InstructorForm,self).__init__(*args,**kwargs)
        # following code from Tom Nurkkala
        # list of all active faculty in the dept (used for dropdown lists)
        active_fm_ids = [fm.id
                         for fm in FacultyMember.objects.filter(department__id=department_id)
                         if fm.is_active(year)]
        # in addition, there could be faculty from other depts that are in the group of "faculty_to_view" in user preferences, so add those in, too....
        for fm_to_view_id in faculty_to_view_ids:
            fm = FacultyMember.objects.get(pk = fm_to_view_id)
            if fm.is_active(year) and (fm.id not in active_fm_ids):
                active_fm_ids.append(fm.id)
        # in addition, need to add to this list anyone who is already teaching this course offering,
        # or else that faculty member won't show up on drop-down lists, which can lead to a form crashing 
        # (if you try to edit the loads and that instructor is already teaching the course offering but
        # is not being viewed(!))
        for oi in course_offering.offering_instructors.all():
            if oi.instructor.id not in active_fm_ids:
                print('found an instructor that needed to be added!!!')
                print(oi.instructor)
                active_fm_ids.append(oi.instructor.id)
        #for choice in self.fields['course_offering'].choices:
        #    print(choice)
        fm_objects = FacultyMember.objects.filter(id__in=active_fm_ids)
        self.fields['instructor'].queryset = fm_objects


    class Meta:
        model = OfferingInstructor
        exclude = ()
        #fields = "__all__"


#class ManageCourseOfferingForm(forms.ModelForm):

#    def __init__(self, year_id, *args, **kwargs):
#        super (ManageCourseOfferingForm,self).__init__(*args,**kwargs)
#        self.fields['semester'].queryset = Semester.objects.filter(Q(year__id = year_id))

#    class Meta:
#        model = CourseOffering
#        exclude = ('instructor',)


class BaseOtherLoadOneFacultyFormset(forms.models.BaseInlineFormSet):
    """can be used to set up validation errors, etc."""
    def clean(self):
        if any(self.errors):
            return

class OtherLoadOneFacultyForm(forms.ModelForm):

    def __init__(self, year_to_view, *args, **kwargs):
        super (OtherLoadOneFacultyForm,self).__init__(*args,**kwargs)
        # following code from Tom Nurkkala
        #        self.fields['instructor'].queryset = FacultyMember.objects.filter(Q(department__id = department_id))
        #        self.fields['semester'].queryset = Semester.objects.filter(Q(year__begin_on__year=year_to_view))
        self.fields['semester'].queryset = Semester.objects.filter(Q(year = year_to_view))

    class Meta:
        model = OtherLoad
        fields = "__all__"

class BaseClassScheduleFormset(forms.models.BaseInlineFormSet):

    class Meta:
        fields = "__all__"
    def clean(self):

        #if any(self.errors):
        #    print(self.errors)
        #    for subform in self.forms:
        #        print(subform.errors)
        #    don't let it return; needs to run to the end to see if there are any other errors....
        #    return

        begin_times = []
        end_times = []

        day_schedules = {0:[], 1:[], 2:[], 3:[], 4:[]}

        for subform in self.forms:
            # need to do a "try/except" here b/c the form could have some blank rows if the user skips
            # down and enters data a few rows down....
            try:
                begin_time = subform.cleaned_data['begin_at']
                end_time = subform.cleaned_data['end_at']
                day = subform.cleaned_data['day']
                begin_time_decimal = convert_time_to_decimal(begin_time)
                end_time_decimal = convert_time_to_decimal(end_time)
                if end_time_decimal <= begin_time_decimal:
                    raise forms.ValidationError(ENDING_BEFORE_BEGINNING_TIME)

                for time_block in day_schedules[day]:
                    if (begin_time_decimal < time_block[1] and begin_time_decimal > time_block[0]
                        ) or (end_time_decimal < time_block[1] and end_time_decimal > time_block[0]
                        ) or (begin_time_decimal <= time_block[0] and end_time_decimal >= time_block[1]):
                        raise forms.ValidationError(NO_OVERLAP_TIME_BLOCKS)

                day_schedules[day].append([begin_time_decimal, end_time_decimal])
            except KeyError:
                pass

def convert_time_to_decimal(time):

    decimal_time = time.hour+time.minute/60.0
    return decimal_time

class BaseCourseOfferingFormset(forms.models.BaseInlineFormSet):

# This can be used for future expansion -- e.g., for error trapping on field entries.

    def clean(self):
        if any(self.errors):
            return

class EasyDaySchedulerForm(forms.Form):
    DAY_OPTIONS = (
        ("MWF", "MWF"),
        ("MTWF", "MTWF"),
        ("MTWRF", "MTWRF"),
        ("MW", "MW"),
        ("TR", "TR"),
        ("M","M"),
        ("T", "T"),
        ("W","W"),
        ("R", "R"),
        ("F","F"),
        )

    START_OPTIONS = (
        (700, "7:00"),
        (730, "7:30"),
        (800, "8:00"),
        (830, "8:30"),
        (900, "9:00"),
        (930, "9:30"),
        (1000, "10:00"),
        (1030, "10:30"),
        (1100, "11:00"),
        (1130, "11:30"),
        (1200, "12:00"),
        (1230, "12:30"),
        (1300, "13:00"),
        (1330, "13:30"),
        (1400, "14:00"),
        (1430, "14:30"),
        (1500, "15:00"),
        (1530, "15:30"),
        (1600, "16:00"),
        (1630, "16:30"),
        (1700, "17:00"),
        (1730, "17:30"),
        (1800, "18:00"),
        (1830, "18:30"),
        (1900, "19:00"),
        (1930, "19:30"),
        (2000, "20:00"),
        (2030, "20:30"),
        (2100, "21:00"),
        )

    DURATION_OPTIONS = (
        (50, "0:50"),
        (75, "1:15"),
        (110, "1:50"),
        (170, "2:50"),
        )

    days = forms.ChoiceField(label="Days of the week",choices=DAY_OPTIONS)
    start = forms.ChoiceField(label="Class starting times",choices=START_OPTIONS)
    duration = forms.ChoiceField(label="Duration",choices=DURATION_OPTIONS)

    def __init__(self, sem_id, *args, **kwargs):
        # https://stackoverflow.com/questions/14660037/django-forms-pass-parameter-to-form
        # https://stackoverflow.com/questions/5685037/django-filter-query-based-on-custom-function
        # https://stackoverflow.com/questions/27310454/django-dynamic-modelchoicefield-field
        # https://stackoverflow.com/questions/2623325/is-a-modelchoicefield-always-required
        semester_id = sem_id
        semester = Semester.objects.get(pk=semester_id)
        super (EasyDaySchedulerForm,self).__init__(*args,**kwargs)
        active_room_ids = [room.id for room in Room.objects.all() if room.is_active(semester)]
        self.fields['room'] = forms.ModelChoiceField(
            queryset = Room.objects.filter(id__in = active_room_ids),
            required=False,)
        #self.fields['room'].required = False

class AddCourseForm(forms.ModelForm):

    class Meta:
        model = Course
        exclude = ('prereqs','coreqs','attributes','schedule_semester', 'schedule_year',)

    def __init__(self, dept_id, *args, **kwargs):
        department_id = dept_id
        super (AddCourseForm,self).__init__(*args,**kwargs)
        self.fields['subject'].queryset = Subject.objects.filter(Q(department__id = department_id))

#class OtherLoadForm(forms.ModelForm):

#    class Meta:
#        model = OtherLoad
#        exclude = ('load_type',)

#    def __init__(self, dept_id, *args, **kwargs):
#        department_id = dept_id
#        super (AddCourseForm,self).__init__(*args,**kwargs)
#        self.fields['subject'].queryset = Subject.objects.filter(Q(department__id = department_id))

class BaseOtherLoadFormset(forms.models.BaseInlineFormSet):

# This can be used for future expansion -- e.g., for error trapping on field entries.

    def clean(self):
        if any(self.errors):
            return

class OtherLoadForm(forms.ModelForm):

    def __init__(self, department_id, year_to_view, *args, **kwargs):
        super (OtherLoadForm,self).__init__(*args,**kwargs)
        # following code from Tom Nurkkala
        active_fm_ids = [fm.id
                         for fm in FacultyMember.objects.filter(department__id=department_id)
                         if fm.is_active(year_to_view)]
        fm_objects = FacultyMember.objects.filter(id__in=active_fm_ids)
        self.fields['instructor'].queryset = fm_objects
        #        self.fields['instructor'].queryset = FacultyMember.objects.filter(Q(department__id = department_id))
        #        self.fields['semester'].queryset = Semester.objects.filter(Q(year__begin_on__year=year_to_view))
        self.fields['semester'].queryset = Semester.objects.filter(Q(year = year_to_view))

    class Meta:
        model = OtherLoad
        fields = "__all__"
        
class UpdateRoomsToViewForm(forms.ModelForm):

    class Meta:
        model = UserPreferences
        exclude = ('user','department_to_view','faculty_to_view','academic_year_to_view',
                   'permission_level','other_load_types_to_view',)

class UpdateYearToViewForm(forms.ModelForm):

    def __init__(self, department, is_superuser, *args, **kwargs):
        super (UpdateYearToViewForm, self).__init__(*args, **kwargs)
        # filter out the 'sandbox' academic years
        if not is_superuser:
            # regular department members and department schedulers
            self.fields['academic_year_to_view'].queryset = AcademicYear.objects.filter(Q(department = None) | (Q(department = department) & Q(is_hidden = False)))
        else:
            self.fields['academic_year_to_view'].queryset = AcademicYear.objects.filter(department = None) 

    class Meta:
        model = UserPreferences
        exclude = ('user','department_to_view','faculty_to_view','rooms_to_view',
                   'permission_level','other_load_types_to_view',)

class UpdateLoadsToViewForm(forms.ModelForm):

    class Meta:
        model = UserPreferences
        exclude = ('user','department_to_view','faculty_to_view','rooms_to_view',
                   'permission_level','academic_year_to_view',)



class UpdateFacultyToViewForm(forms.ModelForm):

    class Meta:
        model = UserPreferences
        exclude = ('user','department_to_view','rooms_to_view','academic_year_to_view',
                   'permission_level','other_load_types_to_view',)

    def __init__(self, dept_id, *args, **kwargs):
        department_id = dept_id
        super (UpdateFacultyToViewForm,self).__init__(*args,**kwargs)
        self.fields['faculty_to_view'].queryset = FacultyMember.objects.filter(Q(department__id = department_id))

class UpdateDepartmentToViewForm(forms.ModelForm):

    class Meta:
        model = UserPreferences
        exclude = ('user','faculty_to_view','rooms_to_view','academic_year_to_view',
                   'permission_level','other_load_types_to_view',)

    def __init__(self, *args, **kwargs):
        super (UpdateDepartmentToViewForm,self).__init__(*args, **kwargs)
        self.fields['department_to_view'].queryset = Department.objects.filter(is_active = True)


class AddFacultyForm(forms.ModelForm):

    class Meta:
        model = FacultyMember
        exclude = ('university', 'pidm', 'department',
                   'nickname', 'home_phone',
                   'cell_phone', 'work_phone', 'photo', 'inactive_starting')

    def clean(self):
        last_name = self.cleaned_data.get('last_name')
        first_name = self.cleaned_data.get('first_name')
        faculty_list = [fm for fm in FacultyMember.objects.filter(Q(last_name__icontains = last_name)&Q(first_name__icontains = first_name))]
        if len(faculty_list)>0:
            error_message = 'This faculty member may already exist in the database.  Please contact the iChair site administrator.'                          
            raise forms.ValidationError(error_message)
        return self.cleaned_data


class UpdateFacultyMemberForm(forms.ModelForm):

    def __init__(self, drop_names, *args, **kwargs):
        super (UpdateFacultyMemberForm,self).__init__(*args,**kwargs)
        if drop_names:
            print('has a pidm!')
            self.fields.pop('first_name')
            self.fields.pop('last_name')

    class Meta:
        model = FacultyMember
        exclude = ('university', 'pidm', 'department',
                   'nickname', 'home_phone',
                   'cell_phone', 'work_phone', 'photo',)

    def clean(self):
        inactive_starting_year = self.cleaned_data.get('inactive_starting')
        if inactive_starting_year == None:
            return self.cleaned_data
        else:
            years_with_nonzero_load = []
            have_problem = False
            for year in AcademicYear.objects.all():
                if year.begin_on >= inactive_starting_year.begin_on:
                    #have_problem = True
                    #years_with_nonzero_load.append('{0}-{1}'.format(year.begin_on.year, year.end_on.year))
                    for oi in self.instance.offering_instructors.filter(course_offering__semester__year=year):
                        have_problem = True
                        course_string = '{0} {1} ({2}-{3})'.format(
                            oi.course_offering.course.subject.abbrev,
                            oi.course_offering.course.number,
                            year.begin_on.year, 
                            year.end_on.year
                        )
                        years_with_nonzero_load.append(course_string)
                    for ol in self.instance.other_loads.filter(semester__year=year):
                        have_problem = True
                        print(ol.load_type.load_type)
                        other_load_string = '{0} ({1}-{2})'.format(
                            ol.load_type.load_type,
                            year.begin_on.year, 
                            year.end_on.year
                        )
                        years_with_nonzero_load.append(other_load_string)
            if have_problem:
                year_string = ''
                for year in years_with_nonzero_load:
                    year_string+=year+', '
                if len(year_string)>2:
                    year_string=year_string[:-2]
                
                error_message = 'This faculty member is carrying load during one or more academic years [' + year_string + '] that prevent her or him from being listed as inactive during '+'{0}-{1}'.format(inactive_starting_year.begin_on.year, inactive_starting_year.end_on.year) + '.  Please reassign the load for the years in question before listing the faculty member as inactive.'                          
                raise forms.ValidationError(error_message)

        return self.cleaned_data

class SemesterSelectForm(forms.ModelForm):

    def __init__(self, year, *args, **kwargs):
        super (SemesterSelectForm,self).__init__(*args,**kwargs)
        self.fields['semester'].queryset = Semester.objects.filter(year=year)
#        self.fields['semester'].queryset = Semester.objects.filter(Q(year__begin_on__year=year_to_view))

    class Meta:
        model = CourseOffering
        exclude = ('course','instructor','load_available','max_enrollment', 'comment','crn','delivery_method')

    def clean(self):
        return self.cleaned_data
