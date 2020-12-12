from django.core.management import BaseCommand

from planner.models import *
from banner.models import DeliveryMethod as BannerDeliveryMethod

class Command(BaseCommand):
    # https://stackoverflow.com/questions/30230490/django-custom-command-error-unrecognized-arguments
    help = "Copies the delivery methods from the banner database to the iChair one."

    def handle(self, *args, **options):
        for banner_delivery_method in BannerDeliveryMethod.objects.all():
            ichair_delivery_methods = DeliveryMethod.objects.filter(code = banner_delivery_method.code)
            if len(ichair_delivery_methods) > 0:
                print('the following delivery method already exists in iChair: ', banner_delivery_method.description, '(', banner_delivery_method.code, ')')
            else:
                delivery_method = DeliveryMethod.objects.create(
                    code = banner_delivery_method.code,
                    description = banner_delivery_method.description)
                delivery_method.save()
                print(' > delivery method did not exist; created the following in iChair: ', delivery_method.description, '(', delivery_method.code, ')')
