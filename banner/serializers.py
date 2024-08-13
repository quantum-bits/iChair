from rest_framework import serializers
from planner.models import Semester

#from django.contrib.auth.models import User
from .models import SemesterCodeToImport
#from django.contrib.auth import  authenticate

# https://www.django-rest-framework.org/api-guide/serializers/#dealing-with-nested-objects
# https://stackoverflow.com/questions/20550598/django-rest-framework-could-not-resolve-url-for-hyperlinked-relationship-using
class SemesterCodeToImportSerializer(serializers.ModelSerializer):
    semester_object = serializers.SerializerMethodField()

    class Meta:
        model = SemesterCodeToImport
        fields = ['id', 'term_code', 'allow_room_requests', 'semester_object']

    def get_semester_object(self, obj):
        semesters = Semester.objects.filter(banner_code=obj.term_code)
        if len(semesters) == 1:
            semester = semesters[0]
            return {
              'id': semester.id,
              'name': semester.name.name,
              'banner_code': semester.banner_code
            }
        else:
            return None
