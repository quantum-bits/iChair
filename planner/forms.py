from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from models import *
from django.forms.widgets import RadioSelect


class RequirementForm(forms.ModelForm):
    class Meta:
        model = Requirement
    
    def clean(self):
        courses = self.cleaned_data.get('courses')
        requirements = self.cleaned_data.get('requirements')
        print self.cleaned_data
        if bool(courses) == bool(requirements):
            raise forms.ValidationError("You need either courses or requirements but not both.")
        
        return self.cleaned_data

class RegistrationForm(forms.ModelForm):
    username = forms.CharField(label=(u'User Name'))
    email = forms.EmailField(label=(u'Email Address'))
    password = forms.CharField(label=(u'Password'),
                               widget=forms.PasswordInput(render_value=False))
    
    password1 = forms.CharField(label=(u'Verify Password'),
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

class CourseOfferingForm(forms.ModelForm):

    class Meta:
        model = CourseOffering
        exclude = ('course', 'semester','instructor',)

    def clean(self):
        instructor = self.cleaned_data.get('instructor')
        max_enrollment = self.cleaned_data.get('max_enrollment')
        if max_enrollment < 0:
            raise forms.ValidationError("Maximum enrollment must be greater than or equal to zero.")

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

class BaseInstructorFormset(forms.models.BaseInlineFormSet):

#    def __init__(self,*args,**kwargs):
#        department_abbrev = kwargs.pop('department_abbrev')
#        super (BaseInstructorFormset, self).__init__(*args,**kwargs)
#        self.fields['instructor'].queryset = FacultyMember.objects.filter(department__abbrev=department_abbrev)

    def clean(self):
        if any(self.errors):
            return
        instructors = []
        for subform in self.forms:
# need to do a "try/except" here b/c the form could have some blank rows if the user skips
# down and enters data a few rows down....
            try:
                instructor = subform.cleaned_data['instructor']
#                delete = subform.cleaned_data['delete']
#                print delete
                if instructor in instructors:
                    raise forms.ValidationError("Each instructor can only be listed once.")
                instructors.append(instructor)
            except KeyError:
                pass

class BaseClassScheduleFormset(forms.models.BaseInlineFormSet):

    def clean(self):
        if any(self.errors):
            return
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
                    raise forms.ValidationError("Ending time must be after beginning time.")

                for time_block in day_schedules[day]:
                    if (begin_time_decimal < time_block[1] and begin_time_decimal > time_block[0]
                        ) or (end_time_decimal < time_block[1] and end_time_decimal > time_block[0] 
                        ) or (begin_time_decimal < time_block[0] and end_time_decimal > time_block[1]):
                        raise forms.ValidationError("Time blocks for a given day within a course offering cannot overlap.")

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
        (7, "7:00"),
        (8, "8:00"),
        (9, "9:00"),
        (10, "10:00"),
        (11, "11:00"),
        (12, "12:00"),
        (13, "13:00"),
        (14, "14:00"),
        (15, "15:00"),
        (16, "16:00"),
        (17, "17:00"),
        (18, "18:00"),
        (19, "19:00"),
        (20, "20:00"),
        (21, "21:00"),
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
    room = forms.ModelChoiceField(queryset = Room.objects.all())


class AddCourseForm(forms.ModelForm):

    class Meta:
        model = Course
        exclude = ('prereqs','coreqs','attributes',)

    def __init__(self, dept_id, *args, **kwargs):
        print "got here"
        department_id = dept_id
        print "foo", dept_id
        super (AddCourseForm,self).__init__(*args,**kwargs)
        self.fields['subject'].queryset = Subject.objects.filter(Q(department__id = department_id))
