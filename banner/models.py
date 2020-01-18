from django.db import models

# may need to add a campus to a course offering(?)
# what are the rules concerning primary/secondary instructors?

class StampedModel(models.Model):
    "Model with time stamps"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

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

    course = models.ForeignKey(Course, related_name='offerings', on_delete=models.CASCADE)
    term_code = models.CharField(max_length=6)
    semester_fraction = models.IntegerField(choices = PARTIAL_SEMESTER_CHOICES, default = FULL_SEMESTER)
    instructor = models.ManyToManyField(FacultyMember, through='OfferingInstructor',
                                        blank=True,
                                        related_name='course_offerings')
    max_enrollment = models.PositiveIntegerField(default=10)
    #banner_comment = models.CharField(max_length=20, blank=True, null=True, help_text="(optional)")
    crn = models.CharField(max_length=5)
    ichair_id = models.PositiveIntegerField(blank=True, null=True) # id of corresponding ichair course offering, if it exists

    def comment_list(self):
        comment_list = []
        for comment in self.offering_comments.all():
            comment_list.append({
                "id": comment.id, 
                "text": comment.text,
                "sequence_number": comment.sequence_number})
        return comment_list

    def __str__(self):
        return "{0} ({1})".format(self.course, self.term_code)

    @property
    def is_linked(self):
        """True if there is a (unique) course offering in the iChair database that has been identified with the current (banner) course offering.""" 
        return self.ichair_id is not None


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
#    instructor = models.ForeignKey(FacultyMember, blank=True, null=True)
# at this point let the instructor(s) be determined by CourseOffering...  Eventually
# it might be good to be able to have one instructor on one day and another on another
# day, but leave that for later....

    def __str__(self):
        return '{0} ({1} {2})'.format(self.course_offering, self.day, self.begin_at)