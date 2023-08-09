from rest_framework import viewsets

from .serializers import UserSerializer

from .models import User

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
from .serializers import UserSerializer

#from rest_framework.authentication import SessionAuthentication

# https://www.django-rest-framework.org
# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer