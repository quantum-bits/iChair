from django.core.management.base import BaseCommand, CommandError
from planner.models import CourseOffering, Course

class Command(BaseCommand):
    args = ''
    help = "Sets all course offering's credit hours to their proper default value."

    def handle(self, *args, **kwargs):
        for co in CourseOffering.objects.all():
            min_possible_credit_hour = min(co.course.credit_hours.possible_credit_hours())
            if co.credit_hours != min_possible_credit_hour:
                co.credit_hours = min_possible_credit_hour 
                co.save()
            

