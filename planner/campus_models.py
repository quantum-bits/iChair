from .common_models import *
from django.db import models
from itertools import chain
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
from django.db.models import Q

import logging
logger = logging.getLogger(__name__)
LOG_FILENAME = 'constraint.log'
logging.basicConfig(filename=LOG_FILENAME, level = logging.DEBUG, filemode = 'w')


class University(StampedModel):
    """University. Top-level organizational entity."""
    name = models.CharField(max_length=100)
    url = models.URLField()

    class Meta:
        verbose_name_plural = 'universities'

    def __str__(self):
        return self.name


class School(StampedModel):
    """School within university. Some institutions refer to this as a 'college' or 'division'."""
    name = models.CharField(max_length=100)
    university = models.ForeignKey(University, related_name='schools', on_delete=models.CASCADE)
    dean = models.OneToOneField('FacultyMember', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class Department(models.Model):
    """Academic department"""
    # not every department has a convient abbreviation.
    abbrev = models.CharField(max_length=10, blank=True)
    name = models.CharField(max_length=100)
    school = models.ForeignKey(School, related_name='departments', on_delete=models.CASCADE)
    chair = models.OneToOneField('FacultyMember', blank=True, null=True,
                                 related_name='department_chaired', on_delete=models.SET_NULL)

    class Meta:
        ordering = ['name']

    def outside_courses_this_year(self, academic_year_object):
        course_list = []
        for fac in self.faculty.all():
            for co in fac.outside_course_offerings_this_year(academic_year_object):
                if co.course not in course_list:
                    course_list.append(co.course)
        # https://stackoverflow.com/questions/403421/how-to-sort-a-list-of-objects-based-on-an-attribute-of-the-objects
        course_list.sort(key=lambda x: x.number)
        return course_list

    def outside_courses_any_year(self):
        course_list = []
        subject_id_list = [subj.id for subj in self.subjects.all()]
        for fac in self.faculty.all():
            for co in fac.course_offerings.filter(~Q(course__subject__pk__in = subject_id_list)):
                if co.course not in course_list:
                    course_list.append(co.course)
        course_list.sort(key=lambda x: x.number)
        return course_list

    def is_trusted_by_subject(self, subject):
        """True if the present department is trusted by the subject in the other department"""
        return self in subject.trusted_departments.all()

    def __str__(self):
        return self.name

class Major(models.Model):
    """Academic major"""
    name = models.CharField(max_length=80)
    department = models.ForeignKey(Department, related_name='majors', on_delete=models.CASCADE)

    def __str__(self):
        return self.name
        

class Minor(models.Model):
    """Academic minor"""
    name = models.CharField(max_length=80)
    department = models.ForeignKey(Department, related_name='minors', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class AcademicYear(models.Model):
    begin_on = models.DateField()
    end_on = models.DateField()

    class Meta:
        ordering = [ 'begin_on' ]

    def __str__(self):
        return '{0}-{1}'.format(self.begin_on.year, self.end_on.year)
 
    
class FacultyMember(Person):
    RANK_CHOICES = (('Inst', 'Instructor'),
                    ('Adj', 'Adjunct Professor'),
                    ('Asst', 'Assistant Professor'),
                    ('Assoc', 'Associate Professor'),
                    ('Full', 'Professor'))
    university = models.ForeignKey(University, related_name='faculty', on_delete=models.CASCADE)
    pidm = models.CharField(max_length=25, blank=True, null=True)
    department = models.ForeignKey(Department, related_name='faculty', on_delete=models.CASCADE)
    rank = models.CharField(max_length=8, choices=RANK_CHOICES)
    inactive_starting = models.ForeignKey(AcademicYear, related_name='faculty', blank=True, null=True, on_delete=models.SET_NULL)
    
    class Meta:
        ordering = ['last_name','first_name']

    def load(self, academic_year_object):
        """Total load for this faculty member for a particular academic year"""

        total_load = 0
        for oi in OfferingInstructor.objects.filter(
                Q(instructor = self)&
                Q(course_offering__semester__year=academic_year_object)):
            total_load += oi.load_credit
        for ol in OtherLoad.objects.filter(
                Q(instructor = self)&
                Q(semester__year=academic_year_object)):
            total_load += ol.load_credit

        return total_load

    def load_in_dept(self, department_object, academic_year_object):
        """Total load for this faculty member in a given department for a particular academic year"""

        total_load = 0
        for oi in OfferingInstructor.objects.filter(
                Q(instructor = self)&
                Q(course_offering__semester__year=academic_year_object)&
                Q(course_offering__course__subject__department = department_object)):
            total_load += oi.load_credit
        # only include "other load" if the faculty member's department is department
        if self.department == department_object:
            for ol in OtherLoad.objects.filter(
                    Q(instructor = self)&
                    Q(semester__year=academic_year_object)):
                total_load += ol.load_credit

        return total_load

    def is_active(self, academic_year_object):
        """
        Returns True if the person is still active in the given academic year
        """
        active = True
        if not self.inactive_starting:
            return active
        else:
            if self.inactive_starting.begin_on.year <= academic_year_object.begin_on.year:
                # this person is currently inactive
                active = False
                return active
            else:
                # this person is inactive, but in a later year
                return active
        
    def is_adjunct(self):
        """Returns True if the person is an adjunct."""
        if self.rank == 'Adj':
            return True
        else:
            return False
    
    def outside_course_offerings(self, semester_object):
        """
        Returns the courses that the faculty member is teaching outside his or her home department this semester.
        """
        #Printself.offering_instructors.all()
        subject_list = self.department.subjects.all()
        course_offering_list = []
        #return [co for co in self.offering_instructors.filter(course_offering__semester=semester_object) for sl in self.department.subjects.all() if co.course.subject not in sl]
        for oi in self.offering_instructors.filter(course_offering__semester=semester_object):
            if oi.course_offering.course.subject not in subject_list:
                course_offering_list.append(oi.course_offering)
        return course_offering_list

    def outside_course_offerings_this_year(self, academic_year_object):
        """
        Returns the courses that the faculty member is teaching outside his or her home department this year.
        """
        #Printself.offering_instructors.all()
        subject_list = self.department.subjects.all()
        course_offering_list = []
        #return [co for co in self.offering_instructors.filter(course_offering__semester=semester_object) for sl in self.department.subjects.all() if co.course.subject not in sl]
        for oi in self.offering_instructors.filter(course_offering__semester__year=academic_year_object):
            if oi.course_offering.course.subject not in subject_list:
                course_offering_list.append(oi.course_offering)
        return course_offering_list

    @property
    def number_course_offerings(self):
        """ returns the # of course offerings taught by this faculty member """
        return len(self.course_offerings.all())
            
class StaffMember(Person):
    university = models.ForeignKey(University, related_name='staff', on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=25)
    department = models.ForeignKey(Department, related_name='staff', on_delete=models.CASCADE)

class SemesterName(models.Model):
    """Name for a semester. Using model here may be overkill, but it provides a nice way in
    which to order the semesters throughout the academic year.
    """
    seq = models.PositiveIntegerField(default=10)
    name = models.CharField(max_length=40)

    class Meta:
        ordering = ['seq']

    def __str__(self):
        return self.name


class Semester(models.Model):
    """Instance of a single semester in a given academic year."""

    name = models.ForeignKey(SemesterName, on_delete=models.CASCADE)
    year = models.ForeignKey(AcademicYear, related_name='semesters', on_delete=models.CASCADE)
    begin_on = models.DateField()
    end_on = models.DateField()
    banner_code = models.CharField(max_length=6, help_text="e.g., 201990", blank=True, null=True)
    
    class Meta:
        ordering = ['year', 'name']

    def __str__(self):
        return '{0} {1}'.format(self.name, self.year)


class Holiday(models.Model):
    """Range of days off within a semester. Can be a single day (begin and end are the same
    date) or multiple consecutive days. A semester may have multiple holidays.
    """
    name = models.CharField(max_length=30)
    begin_on = models.DateField()
    end_on = models.DateField()
    semester = models.ForeignKey(Semester, related_name='holidays', on_delete=models.CASCADE)

    class Meta:
        ordering = [ 'begin_on' ]

    def includes(self, date):
        """Does date fall on in this holiday?"""
        return self.begin_on <= date <= self.end_on

    def __str__(self):
        return self.name


class Building(StampedModel):
    """Campus building."""
    abbrev = models.CharField(max_length=20)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ['abbrev']
        
    def __str__(self):
        return self.name


class Room(StampedModel):
    """Room within a building."""
    number = models.CharField(max_length=20)
    building = models.ForeignKey(Building, related_name='rooms', on_delete=models.CASCADE)
    capacity = models.PositiveIntegerField(default=20)

    class Meta:
        ordering = ['building__name','number']

    def __str__(self):
        return '{0} {1}'.format(self.building, self.number)

    def classes_scheduled(self, academic_year_object, department_object):
        """True if classes scheduled for this room by this dept during this academic year"""

        scheduled = False
        scheduled_classes = ScheduledClass.objects.filter(
            Q(course_offering__semester__year = academic_year_object) &
            Q(room = self) &
            Q(course_offering__course__subject__department = department_object)
        )
        if len(scheduled_classes) > 0:
            scheduled = True

        return scheduled


    
class Subject(StampedModel):
    """Subject areas such as COS, PHY, SYS, etc. Note that subject and department are not the
    same thing. A department usually offers courses in multiple subjects.
    """
    department = models.ForeignKey(Department, related_name='subjects', on_delete=models.CASCADE)
    abbrev = models.CharField(max_length=10) # EG: COS, SYS
    name = models.CharField(max_length=80)   # EG: Computer Science, Systems
    # trusted_departments are those that the present subject trusts to make changes to the present subject's course offerings
    trusted_departments = models.ManyToManyField(Department, related_name='subject_trusting_departments', blank=True)

    def __str__(self):
        return self.abbrev

    class Meta:
        ordering = ['abbrev']

class CourseAttribute(StampedModel):
    """Course attribute such as SP or CC."""
    abbrev = models.CharField(max_length=10)
    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name


class Constraint(models.Model):
    name = models.CharField(max_length = 80)
    constraint_text = models.CharField(max_length = 100)

    def __str__(self):
        return self.name

    def parse_constraint_text(self):
        tokens = self.constraint_text.split()
        name,args = tokens[0],tokens[1:]
        parameters = {}
        for i in range(0, len(args), 2):
            parameters[args[i]] = args[i + 1]
        return (name, parameters)

    def satisfied(self, courses, requirement):
        name, arguments = self.parse_constraint_text()
        return getattr(self, name)(courses, requirement, **arguments)

    def any(self, courses, requirement, **kwargs):
        required_courses = requirement.all_courses()
        common_courses = set(required_courses).intersection(set(courses))
        return len(common_courses) >= 1

    def all(self, courses, requirement, **kwargs):
        required_courses = requirement.all_courses()
        un_met_courses = set(required_courses) - set(courses)
        return un_met_courses == 0

    def meet_some(self, courses, requirement, **kwargs):
        required_courses = requirement.all_courses()
        met_courses = set(required_courses).intersection(set(courses))
        at_least = int(kwargs['at_least'])
        return len(met_courses) >= at_least
    
    def min_required_credit_hours (self, courses, requirement, **kwargs):
        at_least = int(kwargs['at_least'])
        all_courses = requirement.all_courses()
        courses_meeting_reqs = set(all_courses).intersection(set(courses))
        return sum(course.credit_hours for course in courses_meeting_reqs) >= at_least

    def all_sub_categories_satisfied(self, courses, requirement, **kwargs):
        sub_categories = requirement.sub_categories()
        satisfied = [sub_category.satisfied(*courses) for sub_category in sub_categories]
        return all(satisfied)

    def satisfy_some_sub_categories(self, courses, requirement, **kwargs):
        at_least = int(kwargs['at_least'])
        return len(requirement.satisfied_sub_categories(courses)) >= at_least
        
        
class Requirement(models.Model):
    name = models.CharField(max_length=50,
                            help_text="e.g., PhysicsBS Technical Electives, or GenEd Literature;"
                            "first part is helpful for searching (when creating a major).")
    
    display_name = models.CharField(max_length=50,
                                    help_text="e.g., Technical Electives, or Literature;"
                                    "this is the title that will show up when students"
                                    "do a graduation audit.")

    constraints = models.ManyToManyField(Constraint, related_name='constraints', blank=True)
    requirements = models.ManyToManyField('self', symmetrical=False, blank=True, related_name = 'sub_requirements')
    courses = models.ManyToManyField('Course', related_name = 'courses', blank=True)
    
    def __str__(self):
        return self.name

    def satisfied_sub_categories(self, courses):
        satisfied_sub_categories = [sub_category 
                                    for sub_category in self.sub_categories()
                                    if sub_category.satisfied(*courses)]
        return satisfied_sub_categories

    def all_courses(self):
        courses = self.courses.all()
        reqs = self.requirements.all()
        req_courses = [list(req.all_courses()) for req in reqs]

        return list(courses) + (list(chain(*req_courses)))

    def satisfied(self, *courses):
        satisfied = True
        for constraint in self.constraints.all():
            constraint_satisfied = constraint.satisfied(courses, self)
            if not constraint_satisfied:
                logging.debug('{}: {} not satisfied'.format(self, constraint.name))
            satisfied = constraint_satisfied and satisfied 
        return satisfied

    def sub_categories(self):
        return [sub_category for sub_category in self.requirements.all()]


class Course(StampedModel):
    """Course as listed in the catalog."""
    SCHEDULE_YEAR_CHOICES = (('E', 'Even'), ('O', 'Odd'), ('B', 'Both'))

    subject = models.ForeignKey(Subject, related_name='courses', on_delete=models.CASCADE)
    # only the first x characters of the course 'number' are checked against Banner, where x is the number of characters for this field in Banner
    # thus, PHY 311 in Banner will match PHY 311L here (which is good, since Banner uses the same number for both the lecture and the lab)
    # because of this, some further checking needs to be done against the # of credit hours
    number = models.CharField(max_length=10)
    title = models.CharField(max_length=80)
    credit_hours = models.PositiveIntegerField(default=3)
    # banner_title used to store a (possibly different) title for this same course, as it appears in Banner
    # when checking to see if two courses are the same, we check first against title, and then against banner_title (if necessary)
    banner_title = models.CharField(max_length=80, blank=True, null=True)
    prereqs = models.ManyToManyField('Requirement', blank=True, related_name='prereq_for')
    coreqs  = models.ManyToManyField('Requirement', blank=True, related_name='coreq_for')

    attributes = models.ManyToManyField(CourseAttribute, related_name='courses', blank=True)

    schedule_semester = models.ManyToManyField(SemesterName, blank=True, help_text='Semester(s) offered')
    schedule_year = models.CharField(max_length=1, choices=SCHEDULE_YEAR_CHOICES, default = 'B')

    def __str__(self):
        return "{0} {1} - {2}".format(self.subject, self.number, self.title)

    @property
    def department(self):
        return self.subject.department

    class Meta:
        ordering = ['subject', 'number' , 'title']


class Student(Person):
    university = models.ForeignKey(University, related_name='students', on_delete=models.CASCADE)
    student_id = models.CharField(max_length=25)
    entering_year = models.ForeignKey(AcademicYear, related_name='+',
                                      help_text='Year student entered university', on_delete=models.CASCADE)
    catalog_year = models.ForeignKey(AcademicYear, related_name='+',
                                     help_text='Catalog year for graduation plan', on_delete=models.CASCADE)
    majors = models.ManyToManyField(Major, related_name='students', blank=True)
    minors = models.ManyToManyField(Minor, related_name='students', blank=True)

class OtherLoadType(models.Model):
    """Types of load other than for teaching course (e.g., administrative load, sabbatical, etc.)"""
    load_type = models.CharField(max_length=20, help_text='e.g., Research, Chair, Sabbatical')

    def __str__(self):
        return self.load_type

    class Meta:
        ordering = ['load_type']
    
    def in_use(self, academic_year_object, department_object):
        """True if this type of load is in use by this dept during this academic year"""

        used = False
        loads = OtherLoad.objects.filter(
            Q(semester__year = academic_year_object) &
            Q(load_type = self) &
            Q(instructor__department = department_object)
        )
        if len(loads) > 0:
            used = True

        return used    

class OtherLoad(models.Model):
    """Instances of other load types for a given instructor in a given semester of a given academic year."""
    load_type = models.ForeignKey(OtherLoadType, related_name='other_loads', on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    instructor = models.ForeignKey(FacultyMember, related_name='other_loads', on_delete=models.CASCADE)
    load_credit = models.FloatField()
    comments = models.CharField(max_length=100, blank=True, null=True,
                                help_text='optional longer comments')


class CourseOffering(StampedModel):
    """Course as listed in the course schedule (i.e., an offering of a course)."""

    FULL_SEMESTER = 0
    FIRST_HALF_SEMESTER = 1
    SECOND_HALF_SEMESTER = 2

    PARTIAL_SEMESTER_CHOICES = (
        (FULL_SEMESTER, 'Full Semester'),
        (FIRST_HALF_SEMESTER, 'First Half Semester'),
        (SECOND_HALF_SEMESTER, 'Second Half Semester')
    )

    course = models.ForeignKey(Course, related_name='offerings', on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, related_name='offerings', on_delete=models.CASCADE)
    semester_fraction = models.IntegerField(choices = PARTIAL_SEMESTER_CHOICES, default = FULL_SEMESTER)
    instructor = models.ManyToManyField(FacultyMember, through='OfferingInstructor',
                                        blank=True,
                                        related_name='course_offerings')
    load_available = models.FloatField(default=3)
    max_enrollment = models.PositiveIntegerField(default=10)
    comment = models.CharField(max_length=20, blank=True, null=True, help_text="(optional)")
    crn = models.CharField(max_length=5, blank=True, null=True)


    def __str__(self):
        return "{0} ({1})".format(self.course, self.semester)

    def department(self):
        return self.course.department

    def students(self):
        """Students enrolled in this course offering"""
        return Student.objects.filter(courses_taken=self)

    def load_difference(self):
        """Difference between load available and assigned load"""
        load_assigned=0
#        for instructor in self.offeringinstructor_set.all():
        for instructor in self.offering_instructors.all():
            load_assigned = load_assigned + instructor.load_credit

        return self.load_available-load_assigned

    def semester_fraction_text(self):
        if (self.semester_fraction == self.FULL_SEMESTER):
            return 'Full Sem'
        elif (self.semester_fraction == self.FIRST_HALF_SEMESTER):
            return '1st Half'
        else:
            return '2nd Half'

    def is_full_semester(self):
        return self.semester_fraction == self.FULL_SEMESTER

    def is_in_semester_fraction(self, semester_fraction):
        return (self.semester_fraction == self.FULL_SEMESTER) or (self.semester_fraction == semester_fraction) or (semester_fraction == self.FULL_SEMESTER)

    @classmethod
    def partial_semesters(cls):
        return [
            {'semester_fraction': cls.FIRST_HALF_SEMESTER},
            {'semester_fraction': cls.SECOND_HALF_SEMESTER}
        ]

    @classmethod
    def full_semester(cls):
        return [
            {'semester_fraction': cls.FULL_SEMESTER}
        ]
            
    @classmethod
    def semester_fraction_name(cls, semester_fraction):
        if (semester_fraction == cls.FULL_SEMESTER):
            return 'Full Sem'
        elif (semester_fraction == cls.FIRST_HALF_SEMESTER):
            return '1st Half'
        else:
            return '2nd Half'


class Grade(models.Model):
    letter_grade = models.CharField(max_length=5)
    grade_points = models.FloatField()

    def __str__(self):
        return self.letter_grade


class CourseTaken(StampedModel):
    student = models.ForeignKey(Student, related_name='courses_taken', on_delete=models.CASCADE)
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE)
    final_grade = models.ForeignKey(Grade, blank=True, on_delete=models.CASCADE)


class OfferingInstructor(StampedModel):
    """Relate a course offering to one (of the possibly many) instructors teaching the
    course. The primary purpose for this model is to track load credit being granted to
    each instructor of the course.
    """
    course_offering = models.ForeignKey(CourseOffering, related_name='offering_instructors', on_delete=models.CASCADE)
    instructor = models.ForeignKey(FacultyMember,related_name='offering_instructors', on_delete=models.CASCADE)
    load_credit = models.FloatField(validators = [MinValueValidator(0.0), MaxValueValidator(100.0)])
    is_primary = models.BooleanField(default=True)


class ClassMeeting(StampedModel):
    """A single meeting of a class, which takes place on a given day, in a period of clock
    time, in a certain room, and led by a single instructor. This model allows
    considerable flexibility as to who teaches each meeting of a course. It also provides
    a hook where we can track content for each meeting of the course.
    """
    
    held_on = models.DateField()
    begin_at = models.TimeField()
    end_at = models.TimeField()
    course_offering = models.ForeignKey(CourseOffering, related_name='class_meetings', on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    instructor = models.ForeignKey(FacultyMember, related_name='class_meetings', on_delete=models.CASCADE)

    def __str__(self):
        return '{0} ({1} {2})'.format(self.course_offering, self.held_on, self.begin_at)

class ScheduledClass(StampedModel):
    """A scheduled meeting of a class, which takes place on a given
    day of the week, in a period of clock time, in a certain room, and
    led by a single instructor.
    """
    
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4

    DAY_CHOICES = (
        (MONDAY, 'Monday'),
        (TUESDAY, 'Tuesday'),
        (WEDNESDAY, 'Wednesday'),
        (THURSDAY, 'Thursday'),
        (FRIDAY, 'Friday')
    )

# in the view, should be able to use ...filter(day = ScheduledClass.MONDAY), etc.

    day = models.IntegerField(choices = DAY_CHOICES, default = MONDAY)
    begin_at = models.TimeField()
    end_at = models.TimeField()
    course_offering = models.ForeignKey(CourseOffering, related_name='scheduled_classes', on_delete=models.CASCADE)
    room = models.ForeignKey(Room, related_name='scheduled_classes', blank=True, null=True, on_delete=models.SET_NULL)
#    instructor = models.ForeignKey(FacultyMember, blank=True, null=True)
# at this point let the instructor(s) be determined by CourseOffering...  Eventually
# it might be good to be able to have one instructor on one day and another on another
# day, but leave that for later....

    comment = models.CharField(max_length=40, blank=True, null=True,
                                help_text='optional brief comment')


    def __str__(self):
        return '{0} ({1} {2})'.format(self.course_offering, self.day, self.begin_at)

class UserPreferences(models.Model):

    VIEW_ONLY = 0
    DEPT_SCHEDULER = 1
    SUPER = 2

    PERMISSION_CHOICES = (
        (VIEW_ONLY, 'view only'),
        (DEPT_SCHEDULER, 'department scheduler'),
        (SUPER, 'super-user')
    )

    user = models.ForeignKey(User, related_name = 'user_preferences', on_delete=models.CASCADE)
    department_to_view = models.ForeignKey(Department, related_name = 'user_preferences', on_delete=models.CASCADE)
    faculty_to_view = models.ManyToManyField(FacultyMember,
                                        blank=True,
                                        related_name='user_preferences')
    academic_year_to_view = models.ForeignKey(AcademicYear, related_name = 'user_preferences', on_delete=models.CASCADE)

    permission_level = models.IntegerField(choices = PERMISSION_CHOICES, default = VIEW_ONLY)

    rooms_to_view = models.ManyToManyField(Room,
                                           blank=True,
                                           related_name='user_preferences')

    other_load_types_to_view = models.ManyToManyField(OtherLoadType,
                                                      blank=True,
                                                      related_name='user_preferences')

    def __str__(self):
        return self.user.last_name

class Note(StampedModel):
    department = models.ForeignKey(Department, related_name='notes', on_delete=models.CASCADE)
    note = models.TextField()
    year = models.ForeignKey(AcademicYear, blank=True, null=True, related_name='notes', on_delete=models.CASCADE)

    def __str__(self):
        return "{0} on {1}".format(self.department, self.updated_at)




