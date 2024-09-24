from rest_framework import viewsets, generics

from .serializers import DeltaCourseOfferingSerializer, RoomSerializer, DepartmentSerializer

from .models import DeltaCourseOffering, Room, Department, Semester

from banner.models import CourseOffering as BannerCourseOffering
from banner.models import Subject as BannerSubject

# authentication, etc., code taken from: https://blog.devgenius.io/django-rest-knox-token-authentication-f134760a4a7b
#from rest_framework import generics, authentication, permissions
#from rest_framework.settings import api_settings
#from rest_framework.authtoken.serializers import AuthTokenSerializer
# https://github.com/James1345/django-rest-knox/blob/develop/docs/auth.md#global-usage-on-all-views
#from django.contrib.auth import login


# knox imports
#from knox.views import LoginView as KnoxLoginView
#from knox.auth import TokenAuthentication

# local apps import

#from rest_framework.authentication import SessionAuthentication

# https://www.django-rest-framework.org
# ViewSets define the view behavior.
# class UserViewSet(viewsets.ModelViewSet):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer

class DeltaCourseOfferingViewSet(viewsets.ModelViewSet):
    queryset = DeltaCourseOffering.objects.all()
    serializer_class = DeltaCourseOfferingSerializer

class DeltaCourseOfferingList(generics.ListAPIView):
    serializer_class = DeltaCourseOfferingSerializer

    def get_queryset(self):
        # some dcos have just a course offering, some have just a crn and some have both; 
        # to get all dcos for a given department and semester, we get two separate querysets
        # and then return their union....
        # https://www.django-rest-framework.org/api-guide/filtering/
        #queryset = DeltaCourseOffering.objects.all()
        department_id = self.request.query_params.get('department_id')
        semester_id = self.request.query_params.get('semester_id')
        department = Department.objects.get(pk=department_id)
        semester = Semester.objects.get(pk=semester_id)
        #print('dept found!', department)
        #print('semester id:', semester_id)
        subject_ids = [subject.id for subject in department.subjects.all()]
        subject_abbrevs = [subject.abbrev for subject in department.subjects.all()]
        # https://stackoverflow.com/questions/9304908/how-can-i-filter-a-django-query-with-a-list-of-values
        queryset = DeltaCourseOffering.objects.filter(course_offering__course__subject__id__in=subject_ids)\
                .filter(semester__id=semester_id)

        banner_subject_ids = [subject.id for subject in BannerSubject.objects.filter(abbrev__in=subject_abbrevs)]
        #print('banner subjects:', BannerSubject.objects.filter(abbrev__in=subject_abbrevs))
        #print('banner subject ids:', banner_subject_ids)
        crns = [bco.crn for bco in \
            BannerCourseOffering.objects.filter(course__subject__id__in=banner_subject_ids)\
            .filter(term_code=semester.banner_code)]
        
        queryset_by_crns = DeltaCourseOffering.objects.filter(crn__in=crns).filter(semester__id=semester_id)
        #print('crns:', crns)
        #print(' ')
        #print('queryset:', queryset)
        #print(' ')
        #print('queryset by crns:', queryset_by_crns)

        # https://stackoverflow.com/questions/4411049/how-can-i-find-the-union-of-two-django-querysets
        return (queryset | queryset_by_crns).distinct()

class RoomViewSet(viewsets.ModelViewSet):
    # https://stackoverflow.com/questions/844556/how-to-filter-empty-or-null-names-in-a-queryset
    queryset = Room.objects.filter(inactive_after__isnull=True)
    serializer_class = RoomSerializer

class DepartmentView(generics.ListAPIView):
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer