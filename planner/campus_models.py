from .common_models import *

from banner.models import CourseOffering as BannerCourseOffering

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

    def outside_faculty_this_year(self, academic_year_object):
        """Returns a list of faculty members not in the department who are teaching something in the department this year."""

        instructor_id_list = []
        instructor_list = []
        for instructor in [oi.instructor for oi in OfferingInstructor.objects.filter(
            Q(course_offering__course__subject__department = self) & 
            Q(course_offering__semester__year = academic_year_object) & 
            ~Q(instructor__department = self))]:
            #print('instructor: ', instructor)
            if instructor.id not in instructor_id_list:
                #print('not in list!')
                instructor_id_list.append(instructor.id)
                instructor_list.append(instructor)
        #print('final instructor list: ', instructor_list)
        return instructor_list

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

    def subjects_including_outside_courses(self, semester_object, course_id_list):
        """Returns a list of department subjects, plus subjects for outside (extra-departmental) courses that are offered this semester."""
        subject_id_list = [subj.id for subj in self.subjects.all()]
        #print(semester_object)
        for course_id in course_id_list:
            for course_offering in CourseOffering.objects.filter((~Q(course__subject__pk__in = subject_id_list)) &
                                                                    Q(semester__pk = semester_object.id) &
                                                                    Q(course__pk = course_id)):
                if (course_offering.course.subject.id not in subject_id_list):
                    subject_id_list.append(course_offering.course.subject.id)
        # now check if there are offerings of these courses in Banner for this semester (but only if the subject is not already in the list)
        # https://www.pythonforbeginners.com/basics/list-comprehensions-in-python
        extra_departmental_courses = [{
            "credit_hours": course.credit_hours,
            "title": course.title,
            "subject_abbrev": course.subject.abbrev,
            "number": course.number,
            "banner_titles": course.banner_title_list
            } for course in Course.objects.filter(pk__in = course_id_list) if course.subject.id not in subject_id_list]

        subject_abbrev_list = [subject.abbrev for subject in Subject.objects.filter(pk__in = subject_id_list)]
        unused_subjects = [course.subject for course in Course.objects.filter(pk__in = course_id_list) if course.subject.id not in subject_id_list]
        #print('here are the courses whose subjects are not yet in the subject list: ', extra_departmental_courses)
        #print('here are the unused subjects: ', unused_subjects)
        #print('subject abbrev list (before getting Banner ones): ', subject_abbrev_list)
        #print('subject id list (before looking in banner): ', subject_id_list)
        
        # the following is a bit tricky...the subjects are iChair subjects, but we now need to see if there are Banner offerings
        # during this semester, and if so, add the corresponding iChair version of the subject
        term_code = semester_object.banner_code
        for subject in unused_subjects: #these are iChair subjects
            for bco in BannerCourseOffering.filtered_objects(subject, term_code, False, extra_departmental_courses):
                if (bco.course.subject.abbrev not in subject_abbrev_list):
                    subject_id_list.append(subject.id)
                    subject_abbrev_list.append(bco.course.subject.abbrev)
        
        #print('subject abbrev list (after getting the Banner ones): ', subject_abbrev_list)
        #print('subject id list (after looking in banner): ', subject_id_list)
        # now fetch the objects themselves
        subject_list = []
        for subject_id in subject_id_list:
            subject = Subject.objects.get(pk = subject_id)
            subject_list.append(subject)
        subject_list.sort(key=lambda x: x.abbrev)
        return subject_list

    # department.subjects.all():

    def is_trusted_by_subject(self, subject):
        """True if the present department is trusted by the subject in the other department."""
        return self in subject.trusted_departments.all()

    def available_instructors(self, academic_year, course_offering, faculty_to_view_ids):
        """Returns a list of instructors that are available to teach this course offering in this academic year."""
        active_fm_ids = [fm.id for fm in self.faculty.all() if fm.is_active(academic_year)]
        # in addition, there could be faculty from other depts that are in the group of "faculty_to_view" in user preferences, so add those in, too....
        for fm_to_view_id in faculty_to_view_ids:
            fm = FacultyMember.objects.get(pk = fm_to_view_id)
            if fm.is_active(academic_year) and (fm.id not in active_fm_ids):
                active_fm_ids.append(fm.id)
        # finally, since this is used to populate drop-down lists, should add in any faculty members who *may already be teaching this course
        # offering*, since otherwise will get strange behaviour in forms when trying to edit loads
        for oi in course_offering.offering_instructors.all():
            if oi.instructor.id not in active_fm_ids:
                active_fm_ids.append(oi.instructor.id)
                
        instructors_available_to_teach = [{
                                            'id': fm.id,
                                            'name': fm.first_name+' ' + fm.last_name
                                        } for fm in FacultyMember.objects.filter(id__in=active_fm_ids)]

        return instructors_available_to_teach

    def messages_this_year(self, academic_year, non_dismissed_only = True):
        message_list = []
        for message in self.messages.all().filter(year = academic_year):
            #print('got a message!')
            if (non_dismissed_only and not message.dismissed) or (not non_dismissed_only):
                print('inside if!')
                fragments = []
                for fragment in message.fragments.all():
                    fragments.append({
                        'indentation_level': fragment.indentation_level,
                        'text': fragment.fragment,
                        'sequence_number': fragment.sequence_number
                    })
                message_list.append({
                    'message_type': message.message_type,
                    'dismissed': message.dismissed,
                    'updated_at': message.updated_at,
                    'fragments': fragments,
                    'id': message.id
                })
        #print('messages: ', message_list)
        return message_list

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
    ADJUNCT_RANK = 'Adj'
    RANK_CHOICES = (('Inst', 'Instructor'),
                    (ADJUNCT_RANK, 'Adjunct Professor'),
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
        return self.rank == self.ADJUNCT_RANK
    
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
        ordering = ['year', 'begin_on']

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

    @property
    def short_name(self):
        return '{0} {1}'.format(self.building.abbrev, self.number)

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

    def restricted_course_offerings(self, department, semester, course_id_list):
        """
        Returns a list of course offerings for this semester for this subject.  If the subject is owned by the department,
        it returns all course offerings.  If not, it only returns course offerings corresponding to courses in the list.
        """
        if self.department == department:
            return CourseOffering.objects.filter(Q(semester=semester) & Q(course__subject=self))
        else:
            return CourseOffering.objects.filter(Q(semester=semester) & Q(course__subject=self) & Q(course__pk__in = course_id_list))

    def restricted_course_offerings_no_crn(self, department, semester, course_id_list):
        """
        Returns a list of course offerings for this semester for this subject that have no CRN.  If the subject is owned by the department,
        it returns all course offerings.  If not, it only returns course offerings corresponding to courses in the list.
        """
        if self.department == department:
            #print('departments do not agree!', self, self.department, department)
            return CourseOffering.objects.filter(Q(semester=semester) & Q(course__subject=self) & Q(crn__isnull=True))
        else:
            #print('departments do agree!', self, self.department, department)
            return CourseOffering.objects.filter(Q(semester=semester) & Q(course__subject=self) & Q(course__pk__in = course_id_list) & Q(crn__isnull=True))

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
    # update: now BannerTitle is its own class, with a FK to Course; that way we can have multiple Banner Titles for each course
    #banner_title = models.CharField(max_length=80, blank=True, null=True)
    prereqs = models.ManyToManyField('Requirement', blank=True, related_name='prereq_for')
    coreqs  = models.ManyToManyField('Requirement', blank=True, related_name='coreq_for')

    attributes = models.ManyToManyField(CourseAttribute, related_name='courses', blank=True)

    schedule_semester = models.ManyToManyField(SemesterName, blank=True, help_text='Semester(s) offered')
    schedule_year = models.CharField(max_length=1, choices=SCHEDULE_YEAR_CHOICES, default = 'B')

    def __str__(self):
        return "{0} {1} - {2}".format(self.subject, self.number, self.title)

    def number_offerings_this_year(self, academic_year_object):
        return len(self.offerings.filter(semester__year = academic_year_object))

    @property
    def department(self):
        return self.subject.department

    @property
    def banner_title_list(self):
        """Returns a list of banner titles (as strings) for this course."""
        return [banner_title.title for banner_title in self.banner_titles.all()]

    @property
    def banner_title_dict_list(self):
        """Returns a list of banner title dicts."""
        return [{ 
                "title": banner_title.title,
                "id": banner_title.id
                } for banner_title in self.banner_titles.all()]

    @property
    def banner_titles_string(self):
        """Returns a list of banner titles in a string form that can be used as a tooltip."""

        banner_title_list = [banner_title.title for banner_title in self.banner_titles.all()]
        if len(banner_title_list) == 0:
            banner_titles = 'Banner Name(s):\n' + '   same as iChair (or unknown)'
        else:
            banner_titles = 'Banner Name(s):\n'
            counter = 1
            for bt in banner_title_list:
                if counter < len(banner_title_list):
                    banner_titles += '   ' + bt + '\n'
                else:
                    banner_titles += '   ' + bt
                counter += 1
        return banner_titles

    class Meta:
        ordering = ['subject', 'number' , 'title']


class BannerTitle(StampedModel):
    """A banner version of the title for a course; there can be multiple banner titles for each course."""
    course = models.ForeignKey(Course, related_name='banner_titles', on_delete=models.CASCADE)
    title = models.CharField(max_length=80) # probably 30 characters is sufficient, given what shows up in the Data Warehouse data, but OK....

    def __str__(self):
        return self.title


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

    @property
    def snapshot(self):
        """Returns a snapshot, in the form of a dictionary, of all/most relevant properties associated with this course offering."""
        # https://stackoverflow.com/questions/11880430/how-to-write-inline-if-statement-for-print
        course_offering_information = {
            "name": "{0} {1} ({2})".format(self.course.subject, self.course.number, self.semester),
            "short_name": "{0} {1}".format(self.course.subject, self.course.number),
            "semester": "{0}".format(self.semester),
            "semester_id": self.semester.id,
            "semester_fraction": self.semester_fraction,
            "load_available": self.load_available,
            "max_enrollment": self.max_enrollment,
            "comment": self.comment,
            "public_comments": [{
                    "id": pc.id,
                    "text": pc.text,
                    "sequence_number": pc.sequence_number
                } for pc in self.offering_comments.all()],
            "scheduled_classes": [{
                    "id": sc.id,
                    "begin_at": sc.begin_at,
                    "end_at": sc.end_at,
                    "day": sc.day,
                    "room_id": sc.room.id if sc.room != None else None,
                    "room": sc.room.short_name if sc.room != None else "",
                } for sc in self.scheduled_classes.all()],
            "offering_instructors": [{
                    "id": oi.id,
                    "instructor": {
                        "id": oi.instructor.id,
                        "name": "{0} {1}".format(oi.instructor.first_name[:1], oi.instructor.last_name)
                    },
                    "load_credit": oi.load_credit,
                    "is_primary": oi.is_primary
                } for oi in self.offering_instructors.all()]

        }
        #print(course_offering_information)
        return course_offering_information

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

    @classmethod
    def semester_frac_text(cls, semester_fraction):
        if (semester_fraction == cls.FULL_SEMESTER):
            return 'Full Sem'
        elif (semester_fraction == cls.FIRST_HALF_SEMESTER):
            return '1st Half'
        else:
            return '2nd Half'

    def is_full_semester(self):
        return self.semester_fraction == self.FULL_SEMESTER

    def is_in_semester_fraction(self, semester_fraction):
        return (self.semester_fraction == self.FULL_SEMESTER) or (self.semester_fraction == semester_fraction) or (semester_fraction == self.FULL_SEMESTER)

    def comment_list(self):
        # https://stackoverflow.com/questions/2872512/python-truncate-a-long-string/39017530
        comment_list = []
        ii = 0
        summary = ''
        summary_contains_all_text = True
        comments = self.offering_comments.all()
        for comment in comments:
            comment_list.append({
                "id": comment.id, 
                "text": comment.text,
                "sequence_number": comment.sequence_number})
            if ii == 0:
                if len(comments) == 1:
                    summary = (comment.text[:20] + '...') if len(comment.text) > 20 else comment.text
                    if len(comment.text) > 20:
                        summary_contains_all_text = False
                else:
                    summary = (comment.text[:20] + '...') if len(comment.text) > 20 else comment.text + '...'
                    summary_contains_all_text = False
            ii = ii + 1
        
        # summary_contains_all_text is true if the summary text contains all the detail of the comments 
        # (i.e., there will be no need for a tooltip containing more detail)
        return { 
            "summary": summary,
            "comment_list": comment_list,
            "summary_contains_all_text": summary_contains_all_text
        }

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

    @classmethod
    def semester_fraction_long_name(cls, semester_fraction):
        if (semester_fraction == cls.FULL_SEMESTER):
            return 'Full Semester'
        elif (semester_fraction == cls.FIRST_HALF_SEMESTER):
            return '1st Half Semester'
        else:
            return '2nd Half Semester'

class CourseOfferingPublicComment(StampedModel):
    """A comment that can be added to the course offering for display on TU's public website."""
    course_offering = models.ForeignKey(CourseOffering, related_name='offering_comments', on_delete=models.CASCADE)
    text = models.CharField(max_length=60)
    # sequence number is stored as a decimal in Banner (why?!?), so I am following that here, although there
    # could be problems with rounding, since SQLite does not actually have a real decimal type.
    # To ensure that there are no problems, just use the sequence number to order the comments, and do the 
    # same in the ichair database.  In this case, small rounding errors shouldn't be a problem.
    sequence_number = models.DecimalField(max_digits=23, decimal_places=20)

    def __str__(self):
        return "{0} ({1}, {2}): {3} {4}".format(self.course_offering.course, self.course_offering.semester, self.course_offering.crn, self.sequence_number, self.text)

    class Meta:
        ordering = ['sequence_number']

class DeltaCourseOffering(StampedModel):
    """Proposed change to a banner version of a course offering.  Used for communication with the registrar."""

    CREATE = 0
    UPDATE = 1
    DELETE = 2

    ACTION_CHOICES = (
        (CREATE, 'Create'),
        (UPDATE, 'Update'),
        (DELETE, 'Delete')
    )

    # CREATE: - only has a course_offering
    # UPDATE: - has both a crn and a course_offering (need both for the diff)
    # DELETE: - only has a crn
    #
    # could get messy in the UPDATE cases if the crn and course_offering fall out of sync with each other.  (We're aligning these dynamically, so it's conceivable.)
    #   - before submitting to the registrar, need to check that the crn/course offering (as applicable) of the "delta" object agree with 
    #     those that are currently in the two databases.  if not, trash the delta object.  in particular, for an UPDATE, check that the
    #     course offering has the right crn and that the banner course offering has the right course_offering_id

    crn = models.CharField(max_length=5, blank=True, null=True) # crn of the banner course offering, if it exists
    semester = models.ForeignKey(Semester, related_name='delta_offerings', on_delete=models.CASCADE) # this allows us to get the term_code as well, for finding the banner course offering
    course_offering = models.ForeignKey(CourseOffering, related_name='delta_offerings', blank=True, null=True, on_delete=models.CASCADE)

    extra_comment = models.CharField(max_length=500, blank=True, null=True, help_text="(optional comment for the registrar)")

    # the action requested of the registrar
    requested_action = models.IntegerField(choices = ACTION_CHOICES, default = UPDATE)

    # the following are used for UPDATEs and CREATEs, and specify which of the course offering fields should be aligned with the iChair versions
    # (some may not need to be updated, others could be updated/created, but the user is not electing to do so at present)

    update_meeting_times = models.BooleanField(default=False)
    update_instructors = models.BooleanField(default=False)
    update_semester_fraction = models.BooleanField(default=False)
    update_max_enrollment = models.BooleanField(default=False)
    update_public_comments = models.BooleanField(default=False)

    def __str__(self):
        if self.course_offering is not None:
            return "{0} ({1})".format(self.course_offering, self.semester)
        elif self.crn is not None:
            return "{0} ({1})".format(self.crn, self.semester)
        else:
            return "{0} ({1})".format('Unknown course offering', self.semester)

    @classmethod
    def actions(cls):
        return {
            'create': cls.CREATE,
            'update': cls.UPDATE,
            'delete': cls.DELETE
        }

    @classmethod
    def actions_reverse_lookup(cls, action_value):
        if action_value == cls.CREATE:
            return 'create'
        elif action_value == cls.UPDATE:
            return 'update'
        elif action_value == cls.DELETE:
            return 'delete'
        else:
            return None
    

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
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['instructor__last_name','instructor__first_name']


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
    # at some point might want to make this a one-to-one field; see here for a useful tutorial:
    # https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
    # if do this, might be able to write a decorator that redirects away from a form (for example) if the user
    # doesn't have sufficient permission:
    # https://medium.com/@MicroPyramid/custom-decorators-to-check-user-roles-and-permissions-in-django-ece6b8a98d9d
    # might want to do this using two decorators (i.e., keeping @login_required); in that case:
    # https://blog.tecladocode.com/python-how-to-use-multiple-decorators-on-one-function/

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


class Message(StampedModel):

    WARNING = 0
    INFORMATION = 1
    ERROR = 3

    MESSAGE_TYPE_CHOICES = (
        (WARNING, 'Warning'),
        (INFORMATION, 'Information'),
        (ERROR, 'Error'),
    )

# in the view, should be able to use ...filter(message_type = Message.WARNING), etc.
    message_type = models.IntegerField(choices = MESSAGE_TYPE_CHOICES, default = WARNING)

    department = models.ForeignKey(Department, related_name='messages', on_delete=models.CASCADE)

    year = models.ForeignKey(AcademicYear, related_name='messages', on_delete=models.CASCADE)
    dismissed = models.BooleanField(default=False)

    def __str__(self):
        return "{0} on {1}".format(self.department, self.updated_at)

class MessageFragment(StampedModel):

    TAB_ZERO = 0
    TAB_ONE = 1
    TAB_TWO = 2
    TAB_THREE = 3
    INDENTATION_CHOICES = (
        (TAB_ZERO, 'Top-level'),
        (TAB_ONE, 'Single-tabbed'),
        (TAB_TWO, 'Double-tabbed'),
        (TAB_THREE, 'Triple-tabbed'),
    )

    indentation_level = models.IntegerField(choices = INDENTATION_CHOICES, default = TAB_ZERO)
    fragment = models.TextField()
    sequence_number = models.IntegerField()
    message = models.ForeignKey(Message, related_name='fragments', on_delete=models.CASCADE)

    def __str__(self):
        return "{0}. {1}".format(self.sequence_number, self.fragment)

    class Meta:
        ordering = ['sequence_number']