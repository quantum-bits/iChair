from django.db import models

from .common_models import *
from .campus_models import *

import logging
logger = logging.getLogger(__name__)

    
class RequirementBlock(models.Model):
    ANDREQ = 1
    ORREQ = 2
    AND_OR_CHOICES = (
        (ANDREQ, 'AND'),
        (ORREQ, 'OR')
    )

    name = models.CharField(max_length=50,
                            help_text="e.g., PhysicsBS Technical Electives, or GenEd Literature;"
                            "first part is helpful for searching (when creating a major).")
    
    display_name = models.CharField(max_length=50,
                                    help_text="e.g., Technical Electives, or Literature;"
                                    "this is the title that will show up when students"
                                    "do a graduation audit.")

    requirement_type  = models.IntegerField(choices=AND_OR_CHOICES, default = ANDREQ,
                                                help_text = "Choose AND if all are required,"
                                                "OR if a subset is required.")

    minimum_number_of_credit_hours = models.IntegerField(default = 10)
    
    list_order = models.PositiveIntegerField(default = 1,
                                             help_text="Preferred place in the list"
                                             "of requirements; it is OK if numbers"
                                             "are repeated or skipped.")
    
    text_for_user = models.CharField(max_length=200, blank = True,
                                     help_text="Optional helpful text for the user;"
                                     "will appear in the graduation audit.")
    
    courses = models.ManyToManyField(Course, help_text = "Select courses for this requirement.")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


# class StudentSemesterCourses
#
# This class used to represent courses taken by a student in a given semester. In the
# updated data model, this relationship is captured in the CourseTaken model, which
# relates a Student to CourseOffering. The CourseOffering has an associated Semester
# object, which tells us when the student took that course.


# class CreateYourOwnCourse
#
# This class has been replaced by the more sensibly-named TransferCourse.

class TransferCourse(models.Model):
    """Course transferred from another institution."""
    university = models.ForeignKey(University, related_name='transfer_courses')
    title = models.CharField(max_length=80)
    credit_hours = models.PositiveIntegerField(default=3)
    semester = models.ForeignKey(Semester)
    equivalent_course = models.ForeignKey(Course, related_name='transfer_courses')
    student = models.ForeignKey(Student, related_name='transfer_courses')

    def __str__(self):
        return self.title


class AdvisingNote(StampedModel):
    student = models.ForeignKey(Student, related_name='advising_notes')
    note = models.TextField()

    def __str__(self):
        return "{0} on {1}".format(self.student, self.updated_at)


class ClassStanding(models.Model):
    """Class standing (e.g., freshman, sophomore, ...)"""
    seq = models.PositiveIntegerField(default=10)
    name = models.CharField(max_length=20)

    class Meta:
        ordering = ['seq']

    def __str__(self):
        return self.name


# class PrepopulateSemesters is now class DegreeProgram
class DegreeProgram(StampedModel):
    """Courses in a degree program"""
    name = models.CharField(max_length=100, help_text="e.g., Physics BS, entering odd years")
    entering_year = models.CharField(max_length=1, choices=Course.SCHEDULE_YEAR_CHOICES)
    major = models.ForeignKey(Major, related_name='degree_programs')

    def __str__(self):
        return self.name


class DegreeProgramCourse(StampedModel):
    """Single course in a degree program"""
    degree_program = models.ForeignKey(DegreeProgram)
    course = models.ForeignKey(Course)
    class_standing = models.ForeignKey(ClassStanding)
    semester_name = models.ForeignKey(SemesterName)

