from django.core.management import BaseCommand
from django.db.models import Q

from planner.models import *
from banner.models import CourseOffering as BannerCourseOffering
from banner.models import SemesterCodeToImport as BannerSemesterCodeToImport

class Command(BaseCommand):
    # https://stackoverflow.com/questions/30230490/django-custom-command-error-unrecognized-arguments
    help = "Copies delivery methods from the banner database to the iChair database for all iChair course offerings that have a CRN."

    def handle(self, *args, **options):
        num_unmatched = 0
        num_multiple_matches = 0
        num_exact_matches = 0
        num_delivery_method_errors = 0
        num_course_offerings_with_crn = 0
        num_already_had_delivery_method = 0
        num_did_not_have_delivery_method = 0
        num_no_stored_crn_now_updated_delivery_method = 0
        num_no_crn_and_no_match_found_in_banner = 0
        num_course_offerings = 0
        for banner_semester in BannerSemesterCodeToImport.objects.all():
            for co in CourseOffering.objects.filter(semester__banner_code = banner_semester.term_code):
                # only add a delivery method if the course offering doesn't currently have one
                num_course_offerings += 1
                if co.delivery_method is None:
                    num_did_not_have_delivery_method += 1
                    if co.crn is not None:
                        num_course_offerings_with_crn += 1
                        banner_course_offerings = BannerCourseOffering.objects.filter(Q(crn = co.crn) & Q(term_code = co.semester.banner_code))
                        
                        if len(banner_course_offerings) == 0:
                            print('could not find a match for ', co.crn, co)
                            num_unmatched += 1
                        elif len(banner_course_offerings) == 1:
                            num_exact_matches += 1
                            bco = banner_course_offerings[0]

                            delivery_method = DeliveryMethod.objects.filter(code = bco.delivery_method.code)
                            # next lines commented out to prevent accidental use of this command...although the code should now actually be safe....
                            #if len(delivery_method) == 1:
                            #    co.delivery_method = delivery_method[0]
                            #    co.save()
                            #else:
                            #    num_delivery_method_errors += 1

                        else:
                            print('??? well that is weird...there seem to be two banner course offerings for this iChair course offering: ',co)
                            num_multiple_matches += 1
                    else:
                        # in this case the iChair course offering is not currently aligned with a banner course offering, 
                        # so need to try to see if there is a reasonable match....
                        candidate_banner_course_offerings = BannerCourseOffering.objects.filter(
                            Q(term_code=banner_semester.term_code) &
                            Q(course__subject__abbrev=co.course.subject.abbrev) &
                            Q(course__credit_hours=co.course.credit_hours))
                        # now find the course number matches, truncating the iChair ones to the same # of digits (in the comparison) as the banner ones
                        # https://www.pythonforbeginners.com/basics/list-comprehensions-in-python
                        # https://www.pythoncentral.io/cutting-and-slicing-strings-in-python/
                        banner_options = [bco for bco in candidate_banner_course_offerings if bco.course.number ==
                                        co.course.number[:len(bco.course.number)]]
                        if len(banner_options) > 0:
                            print("iChair: ", co)
                            print("banner: ", banner_options)
                            banner_delivery_method = banner_options[0].delivery_method
                            delivery_method = DeliveryMethod.objects.filter(code = banner_delivery_method.code)
                            # next lines commented out to prevent accidental use of this command...although the code should now actually be safe....
                            #if len(delivery_method) == 1:
                            #    co.delivery_method = delivery_method[0]
                            #    co.save()
                            #    num_no_stored_crn_now_updated_delivery_method += 1
                            #else:
                            #    num_delivery_method_errors += 1
                            #print("banner delivery method: ", banner_delivery_method)
                            #print("updated iChair delivery method: ", co.delivery_method)
                        else:
                            num_no_crn_and_no_match_found_in_banner += 1
                else:
                    print('already has a delivery method: ', co)
                    num_already_had_delivery_method += 1
        
        print('number of iChair course offerings: ', num_course_offerings)
        print('number of course offerings that already had a delivery method: ', num_already_had_delivery_method)
        print('number of course offerings that did not already have a delivery method:', num_did_not_have_delivery_method)
        print('number that did not have a stored crn but a match was found and delivery method was updated: ', num_no_stored_crn_now_updated_delivery_method)
        print('number that did not have a stored crn and no match was found: ', num_no_crn_and_no_match_found_in_banner)
        print('number of unmatched course offerings: ',num_unmatched)
        print('number of multiple matches: ', num_multiple_matches)
        print('number of exact matches: ', num_exact_matches)
        print('checksum: ', num_unmatched+num_multiple_matches+num_exact_matches-num_course_offerings_with_crn)
        print('number of delivery method errors: ', num_delivery_method_errors)