from django.core.management import BaseCommand

from planner.models import *


class Command(BaseCommand):
    help = "find duplicate faculty in iChair db"

    def handle(self, *args, **options):
        
        subjects = [subj.abbrev for subj in Subject.objects.all()]
        
        subj_unique = []

        for subject in subjects:
            if subject not in subj_unique:
                subj_unique.append(subject)
        print(subj_unique)
        print(len(subj_unique))

        for abbrev in subj_unique:
            subjects = Subject.objects.filter(abbrev = abbrev)
            if len(subjects) > 1:
                for s in subjects:
                    num_offerings = 0
                    for course in s.courses.all():
                        num_offerings+=len(course.offerings.all())
                    print(s, ' - ', num_offerings, ' ', s.department, '(id: '+str(s.id)+')')
