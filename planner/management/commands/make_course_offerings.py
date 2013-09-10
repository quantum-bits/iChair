from django.core.management.base import BaseCommand, CommandError
from planner.models import AcademicYear, Course, Semester, SemesterName, CourseOffering
import datetime

class Command(BaseCommand):
    args = 'start_year, end_year'
    help = "Makes semesters for a given AcademicYear."
    
    def handle(self, *args, **kwargs):
        start_year, end_year = args
        start_year = int(start_year)
        end_year   = int(end_year)
        
        try:
            academicYear = AcademicYear.objects.get(begin_on__year=start_year,
                                                    end_on__year  = end_year)
        except AcademicYear.DoesNotExist:
            raise CommandError('{}-{} Academic Year does not exist.'.format(start_year, end_year))

        semesterNames = SemesterName.objects.all()
        semesters = Semester.objects.filter(year = academicYear)

        semesterName_to_semester = dict(zip(semesterNames, semesters))

        for course in Course.objects.all():
            semesterNames = course.schedule_semester.all()
            for semesterName in semesterNames:
                if semesterName.fall:
                    year = academicYear.begin_on.year
                else:
                    year = academicYear.end_on.year
                if course.offered_this_year(year):
                    co,created = CourseOffering.objects.get_or_create(course = course,
                                                              semester = semesterName_to_semester[semesterName])
                    co.credit_hours = min(course.credit_hours.possible_credit_hours())
                    co.save()
                



