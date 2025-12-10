from django.http import JsonResponse
from ..models import Location
from django.shortcuts import render

def load_locations(request, level, parent_id=None):
    if parent_id:
        locs = Location.objects.filter(level=level, parent_id=parent_id)
    else:
        locs = Location.objects.filter(level=level)

    return JsonResponse(list(locs.values("id", "name")), safe=False)


def sales_dashboard_view(request):
    return render(request, "appemitidos/salesDB.html")