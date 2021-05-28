from django.core.management.base import BaseCommand, CommandError
from planner.campus_models import *

from banner.models import CourseOffering as BannerCourseOffering

from django.db.models import Q

class Command(BaseCommand):
    help = 'List number of course offerings and delta objects by year and department.'
    def handle(self, *args, **options):

        for year in AcademicYear.objects.all():
            print(' ')
            print(year)
            print(' ')

            #course = models.ForeignKey(Course, related_name='offerings', on_delete=models.CASCADE)
            #term_code = models.CharField(max_length=6)
            #semester_fraction = models.IntegerField(choices = PARTIAL_SEMESTER_CHOICES, default = FULL_SEMESTER)
            #instructor = models.ManyToManyField(FacultyMember, through='OfferingInstructor',
                                      #  blank=True,
                                    #    related_name='course_offerings')
            #max_enrollment = models.PositiveIntegerField(default=10)
            #banner_comment = models.CharField(max_length=20, blank=True, null=True, help_text="(optional)")
            #crn = models.CharField(max_length=5)

            term_codes = []
            for semester in year.semesters.all():
                term_codes.append(semester.banner_code)

            print('term codes: ', term_codes)

            delta_objects = DeltaCourseOffering.objects.filter(Q(semester__year = year))
            delta_objects_no_co = DeltaCourseOffering.objects.filter(Q(semester__year = year) & Q(course_offering = None))
            print('# of delta objects: ', len(delta_objects))
            print('# of delta objects with no course offering: ', len(delta_objects_no_co))
            count_of_dco_no_co = 0

            for department in Department.objects.all():
                subject_list = [subject.abbrev for subject in department.subjects.all()]
                print(' ')
                print(' ', department)
                print('   ', subject_list)
                course_offerings = CourseOffering.objects.filter(Q(course__subject__department = department) & Q(semester__year = year))
                print('    # course offerings: ', len(course_offerings))
                delta_objects_with_course_offering = DeltaCourseOffering.objects.filter(Q(semester__year = year) & Q(course_offering__course__subject__department = department))
                print('    # delta objects with course offering: ', len(delta_objects_with_course_offering))
                delta_objects_no_course_offering = []
                for term_code in term_codes:
                    for dco in DeltaCourseOffering.objects.filter(Q(semester__banner_code = term_code) & Q(course_offering = None)):
                        for bco in BannerCourseOffering.objects.filter(Q(crn = dco.crn) & Q(term_code = term_code) & Q(course__subject__abbrev__in=subject_list)):
                            delta_objects_no_course_offering.append(bco)
                #print('delta objects with crn but no course offering: ', delta_objects_no_course_offering)
                # the following is really counting the banner course offering(s) that apparently go with the delta object
                print('    (approx) # delta objects crn and no course offering: ', len(delta_objects_no_course_offering))
                count_of_dco_no_co += len(delta_objects_no_course_offering)
            
            # If the user requests a delete, the registrar will delete the course offering and then the delta object will essentially be "orphaned"
            print('Approximate # of identified delta objects with crn, but no course offering: ', count_of_dco_no_co)