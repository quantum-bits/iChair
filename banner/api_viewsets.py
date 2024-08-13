from rest_framework import viewsets, generics

from .serializers import SemesterCodeToImportSerializer

from .models import SemesterCodeToImport

class SemesterCodeToImportView(generics.ListAPIView):
    serializer_class = SemesterCodeToImportSerializer
    queryset = SemesterCodeToImport.objects.all()
    #permission_classes = (permissions.IsAuthenticated,)
