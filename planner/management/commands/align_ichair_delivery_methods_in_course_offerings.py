from django.core.management import BaseCommand
from django.db.models import Q

from planner.models import *
from banner.models import CourseOffering as BannerCourseOffering

class Command(BaseCommand):
    # https://stackoverflow.com/questions/30230490/django-custom-command-error-unrecognized-arguments
    help = "Copies delivery methods from the banner database to the iChair database for all iChair course offerings that have a CRN.  This command overwrites the delivery methods property and should not generally be used."

    def handle(self, *args, **options):
        num_unmatched = 0
        num_multiple_matches = 0
        num_exact_matches = 0
        num_delivery_method_errors = 0
        num_course_offerings_with_crn = 0
        for co in CourseOffering.objects.all():
            if co.crn != None:
                num_course_offerings_with_crn += 1
                banner_course_offerings = BannerCourseOffering.objects.filter(Q(crn = co.crn) & Q(term_code = co.semester.banner_code))
                
                if len(banner_course_offerings) == 0:
                    print('could not find a match for ', co.crn, co)
                    num_unmatched += 1
                elif len(banner_course_offerings) == 1:
                    num_exact_matches += 1
                    bco = banner_course_offerings[0]
                    delivery_method = DeliveryMethod.objects.filter(code = bco.delivery_method.code)
                    # next lines commented out to prevent accidental use of this command
                    #if len(delivery_method) == 1:
                    #    co.delivery_method = delivery_method[0]
                    #    co.save()
                    #else:
                    #    num_delivery_method_errors += 1

                else:
                    print('??? well that is weird...there seem to be two banner course offerings for this iChair course offering: ',co)
                    num_multiple_matches += 1

        print('number of unmatched course offerings: ',num_unmatched)
        print('number of multiple matches: ', num_multiple_matches)
        print('number of exact matches: ', num_exact_matches)
        print('checksum: ', num_unmatched+num_multiple_matches+num_exact_matches-num_course_offerings_with_crn)
        print('number of delivery method errors: ', num_delivery_method_errors)