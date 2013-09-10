from django.core.management.base import BaseCommand, CommandError
from planner.models import Semester, SemesterName, AcademicYear
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

        semester_dates = {}
        for semesterName in SemesterName.objects.all():
            if semesterName.fall:
                year = academicYear.begin_on.year
                semester_dates[semesterName] = (academicYear.begin_on,
                                                datetime.date(year, 12, 18))
            elif semesterName.j_term:
                year = academicYear.end_on.year
                semester_dates[semesterName] = (datetime.date(year, 1, 3),
                                                datetime.date(year, 1, 28))
            elif semesterName.spring:
                year = academicYear.end_on.year
                semester_dates[semesterName] = (datetime.date(year, 1,31),
                                                datetime.date(year, 5,21))
            elif semesterName.summer:
                year = academicYear.end_on.year
                semester_dates[semesterName] = (datetime.date(year, 5,23),
                                                academicYear.end_on)

        for semesterName in semester_dates:
            begin_on, end_on = semester_dates[semesterName]
            semester = Semester.objects.get_or_create(name = semesterName,
                                                      year = academicYear,
                                                      begin_on = begin_on,
                                                      end_on = end_on)
                                                      


        

        
