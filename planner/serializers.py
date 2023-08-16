from rest_framework import serializers

#from django.contrib.auth.models import User
from .models import DeltaCourseOffering, Semester, CourseOffering, Course, DeliveryMethod, ScheduledClass, Room
#from django.contrib.auth import  authenticate

# https://www.django-rest-framework.org
# Serializers define the API representation.
# class UserSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = User
#         fields = ['url', 'username', 'email', 'is_staff']

class RoomSerializer(serializers.HyperlinkedModelSerializer):
    building = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'building', 'number']

    def get_building(self, obj):
        return obj.building.abbrev

class CourseSerializer(serializers.HyperlinkedModelSerializer):

    subject = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['subject', 'number', 'title', 'credit_hours']

    def get_subject(self, obj):
        return obj.subject.abbrev

class DeliveryMethodSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = DeliveryMethod
        fields = ['code', 'description']

class SemesterSerializer(serializers.HyperlinkedModelSerializer):
    semester_name = serializers.SerializerMethodField()
    year_name = serializers.SerializerMethodField()

    class Meta:
        model = Semester
        fields = ['semester_name', 'year_name', 'banner_code']
    
    def get_semester_name(self, obj):
        return obj.name.name

    def get_year_name(self, obj):
        # https://www.geeksforgeeks.org/convert-integer-to-string-in-python/
        return str(obj.year.begin_on.year)+'-'+str(obj.year.end_on.year)[-2:]

class CourseOfferingSerializer(serializers.HyperlinkedModelSerializer):
    course = CourseSerializer()
    semester = SemesterSerializer()
    delivery_method = DeliveryMethodSerializer()
    instructors = serializers.SerializerMethodField()
    scheduled_classes = serializers.SerializerMethodField()

    class Meta:
        model = CourseOffering
        fields = ['course', 'crn', 'max_enrollment', 'semester', 'semester_fraction', \
            'delivery_method', 'instructors', 'scheduled_classes']

    def get_instructors(self, obj):
        return [{
                    "id": instructor.id,
                    "last_name": instructor.instructor.last_name,
                    "first_name": instructor.instructor.first_name,
                    "is_primary": instructor.is_primary
                    } for instructor in obj.offering_instructors.all()]

    def get_scheduled_classes(self, obj):
        return [{
                    "day": sc.day,
                    "begin_at": sc.begin_at,
                    "end_at": sc.end_at,
                    "rooms": [{
                                "id": room.id,
                                "name": room.short_name,
                                "building_code": room.building.abbrev,
                                "room_number": room.number
                                } for room in sc.rooms.all()]
                    } for sc in obj.scheduled_classes.all()]

# https://www.django-rest-framework.org/api-guide/serializers/#dealing-with-nested-objects
# https://stackoverflow.com/questions/20550598/django-rest-framework-could-not-resolve-url-for-hyperlinked-relationship-using
class DeltaCourseOfferingSerializer(serializers.HyperlinkedModelSerializer):
    semester = SemesterSerializer()
    course_offering = CourseOfferingSerializer()

    # CREATE = 0
    # UPDATE = 1
    # DELETE = 2
    # NO_ACTION = 3

    # ACTION_CHOICES = (
    #     (CREATE, 'Create'),
    #     (UPDATE, 'Update'),
    #     (DELETE, 'Delete'),
    #     (NO_ACTION, 'No Action'),
    # )

     #'course_offering',

    class Meta:
        model = DeltaCourseOffering
        fields = ['crn', 'semester', 'course_offering', 'extra_comment', 'requested_action',\
            'update_meeting_times', 'update_instructors', 'update_semester_fraction', 'update_max_enrollment', \
            'update_public_comments', 'update_delivery_method', 'id']

