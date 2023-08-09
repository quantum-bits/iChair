from rest_framework import serializers

from django.contrib.auth.models import User
#from django.contrib.auth import  authenticate

# https://www.django-rest-framework.org
# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']


