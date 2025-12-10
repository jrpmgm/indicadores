from django.http import JsonResponse
from django.db.models import Q, Sum
from ..models import Factura, Partner
from datetime import datetime
from django.utils.timezone import make_aware


def load_partners(request):
    partners = Partner.objects.all().values("id", "name")
    return JsonResponse(list(partners), safe=False)



