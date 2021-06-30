from django.db import models
from django.db.models import Q

# may need to add a campus to a course offering(?)
# what are the rules concerning primary/secondary instructors?

class StampedModel(models.Model):
    "Model with time stamps"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


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

class Subject(StampedModel):
    """Subject areas such as COS, PHY, SYS, etc. Note that subject and department are not the
    same thing. A department usually offers courses in multiple subjects.
    """
    abbrev = models.CharField(max_length=10) # EG: COS, SYS
    
    def __str__(self):
        return self.abbrev

    class Meta:
        ordering = ['abbrev']

class Course(StampedModel):
    """Course as listed in the catalog."""

    subject = models.ForeignKey(Subject, related_name='courses', on_delete=models.CASCADE)
    number = models.CharField(max_length=10)
    title = models.CharField(max_length=80)
    credit_hours = models.PositiveIntegerField(default=3)

    def __str__(self):
        return "{0} {1} - {2}".format(self.subject, self.number, self.title)

    class Meta:
        ordering = ['subject', 'number' , 'title']


class FacultyMember(StampedModel):

    pidm = models.CharField(max_length=25)
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    formal_first_name = models.CharField(max_length=60, blank=True, null=True)
    middle_name = models.CharField(max_length=60, blank=True, null=True)
    
    def __str__(self):
        return "{0} {1}".format(self.first_name, self.last_name)

    class Meta:
        ordering = ['last_name','first_name']

class DeliveryMethod(StampedModel):

    code = models.CharField(max_length=3)
    description = models.CharField(max_length=30)

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['description']

class CourseOffering(StampedModel):
    """Course as listed in the course schedule (i.e., an offering of a course)."""

    # FULL_SEMESTER, etc., _must_ match the corresponding properties in planner.CourseOffering!!!
    FULL_SEMESTER = 0
    FIRST_HALF_SEMESTER = 1
    SECOND_HALF_SEMESTER = 2

    PARTIAL_SEMESTER_CHOICES = (
        (FULL_SEMESTER, 'Full Semester'),
        (FIRST_HALF_SEMESTER, 'First Half Semester'),
        (SECOND_HALF_SEMESTER, 'Second Half Semester')
    )

    U = 'U'
    OCP = 'OCP'
    OCD = 'OCD'

    CAMPUS_CHOICES = (
        (U, 'U'),
        (OCP, 'OCP'),
        (OCD, 'OCD')
    )

    course = models.ForeignKey(Course, related_name='offerings', on_delete=models.CASCADE)
    term_code = models.CharField(max_length=6)
    semester_fraction = models.IntegerField(choices = PARTIAL_SEMESTER_CHOICES, default = FULL_SEMESTER)
    campus = models.CharField(max_length = 3, choices = CAMPUS_CHOICES, default = U)
    instructor = models.ManyToManyField(FacultyMember, through='OfferingInstructor',
                                        blank=True,
                                        related_name='course_offerings')
    max_enrollment = models.PositiveIntegerField(default=10)
    #banner_comment = models.CharField(max_length=20, blank=True, null=True, help_text="(optional)")
    crn = models.CharField(max_length=5)
    ichair_id = models.PositiveIntegerField(blank=True, null=True) # id of corresponding ichair course offering, if it exists
    delivery_method = models.ForeignKey(DeliveryMethod, related_name='offerings', blank=True, null=True, on_delete=models.SET_NULL)

    def comment_list(self):
        # https://stackoverflow.com/questions/2872512/python-truncate-a-long-string/39017530
        comment_list = []
        ii = 0
        summary = '---'
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
        

    def __str__(self):
        return "{0} ({1})".format(self.course, self.term_code)

    @property
    def is_linked(self):
        """True if there is a (unique) course offering in the iChair database that has been identified with the current (banner) course offering.""" 
        return self.ichair_id is not None

    @classmethod
    def filtered_objects(cls, subject, term_code, is_own_subject, extra_departmental_courses):
        """
        Returns a list of banner course offerings that are filtered by subject and term code.  The behaviour is as follows:
        is_own_subject == True (i.e., the subject is owned by the department):
            returns all banner course offerings for this subject and term_code; ignores extra_departmental_courses
        is_own_subject == False (i.e., the subject is not owned by the department):
            returns only banner course offerings (for this term_code) associated with the list of courses in extra_departmental_courses
        """
        if is_own_subject:
            return cls.objects.filter(Q(course__subject__abbrev=subject.abbrev) & Q(term_code=term_code))
        else:
            course_offerings = []
            #print('extra departmental courses: ', extra_departmental_courses)
            for course in extra_departmental_courses:
                if subject.abbrev == course['subject_abbrev']:
                    for ii in range(1,len(course["number"])+1):
                        # iChair course numbers might be something like '311L'; this needs to match '311' in Banner;
                        # here I am considering the beginnings of the iChair course numbers and looking for an exact match
                        # with Banner: '3', '31', '311' and '311L' would all be searched
                        course_num = course["number"][:ii]
                        #print(course)
                        #print('searching course number....', course_num)
                        #print('subject abbreviation: ', subject.abbrev)
                        for co in cls.objects.filter(
                            Q(course__subject__abbrev=subject.abbrev) & 
                            Q(term_code=term_code) & 
                            Q(course__credit_hours = course["credit_hours"]) & 
                            Q(course__number = course_num)):
                            print('>>>>>found the following: ', co, ' ', co.id)
                            list_contains_co = False
                            for collected_co in course_offerings:
                                if co.id == collected_co.id:
                                    list_contains_co = True
                                    print('Yikes!  Almost copied this one twice!!!')
                            if not list_contains_co:
                                course_offerings.append(co)
            #print('>>>>>>>extra-departmental course offerings found: ', course_offerings)
            return course_offerings

class CourseOfferingComment(StampedModel):
    """A comment that can be added to the course offering for display on TU's public website."""
    course_offering = models.ForeignKey(CourseOffering, related_name='offering_comments', on_delete=models.CASCADE)
    text = models.CharField(max_length=60)
    # sequence number is stored as a decimal in Banner (why?!?), so I am following that here, although there
    # could be problems with rounding, since SQLite does not actually have a real decimal type.
    # To ensure that there are no problems, just use the sequence number to order the comments, and do the 
    # same in the ichair database.  In this case, small rounding errors shouldn't be a problem.
    sequence_number = models.DecimalField(max_digits=23, decimal_places=20)

    def __str__(self):
        return "{0} ({1}, {2}): {3} {4}".format(self.course_offering.course, self.course_offering.term_code, self.course_offering.crn, self.sequence_number, self.text)

    class Meta:
        ordering = ['sequence_number']

class OfferingInstructor(StampedModel):
    """
    Relate a course offering to one (of the possibly many) instructors teaching the
    course. The primary purpose for this model is to track which instructor is the primary.
    """
    course_offering = models.ForeignKey(CourseOffering, related_name='offering_instructors', on_delete=models.CASCADE)
    instructor = models.ForeignKey(FacultyMember,related_name='offering_instructors', on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['instructor__last_name','instructor__first_name']
        
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
    # leave out the room for now....
    #room = models.ForeignKey(Room, related_name='scheduled_classes', blank=True, null=True, on_delete=models.SET_NULL)
    rooms = models.ManyToManyField(Room, related_name = 'scheduled_class_objects', blank=True)
#    instructor = models.ForeignKey(FacultyMember, blank=True, null=True)
# at this point let the instructor(s) be determined by CourseOffering...  Eventually
# it might be good to be able to have one instructor on one day and another on another
# day, but leave that for later....

    def __str__(self):
        return '{0} ({1} {2})'.format(self.course_offering, self.day, self.begin_at)

class SubjectToImport(StampedModel):
    """
    Abbreviations of Subjects that should be imported from the Data Warehouse (e.g., 'MAT', 'PHY',....)
    We might not want to import _all_ subjects, so this lets us restrict the scope to the ones that we want.
    There is not a direct link from these SubjectToImport objects and the Subject objects; the Subject objects get wiped out
    every time there is an import, but the SubjectToImport objects persist in the database.
    """
    abbrev = models.CharField(max_length=10) # EG: COS, SYS
    
    def __str__(self):
        return self.abbrev

    class Meta:
        ordering = ['abbrev']

class SemesterCodeToImport(StampedModel):
    """
    Semester codes (e.g., '202010', '202190') in Banner format for which we should import data.  These will need to be adjusted
    from time to time, but this allows us the ability to import old data (when setting up a new department, for example).
    """
    term_code = models.CharField(max_length=6)
    allow_room_requests = models.BooleanField(default=False) # set to true when the registrar is ready to receive room requests for this semester

    def __str__(self):
        return self.term_code

    class Meta:
        ordering = ['term_code']