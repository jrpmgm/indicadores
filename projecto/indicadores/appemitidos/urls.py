from django.urls import path
from .vistas import vw_app_views, vw_test
from .modules import md_invoiced, md_invoicedLocation
from .vistas import vw_sales  # Import the views module to access the views defined there
from appemitidos.vistas import vw_locations, vw_invoicedLocation     # Import views from appemitidos
#from appemitidos.vistas import 
#from indicadores.appemitidos import  summarysales, update_filters

urlpatterns = [
    path('mostrar_csv/', vw_app_views.mostrar_csv, name='mostrar_csv'),
    path('loadissued/', vw_app_views.loadissued, name='loadissued'),
    path('dataobtained/<str:pyears>/<str:pmonths>/', vw_app_views.dataobtained, name='dataobtained'),
    path('api/invoiced/', md_invoiced.api_invoiced, name='api_invoiced'),
    path('star_parameters/', vw_app_views.star_parameters, name='star_parameters'),
    path('api/consolidado_emitidos/<str:pyears>/<str:pmonths>/<str:pgrouptype>/<str:ptypedocument>/', md_invoiced.consolidado_emitidos, name='consolidado_emitidos'),
    path('api/consolidado_emitidos_filtrado/<str:pyears>/<str:pmonths>/<str:pgrouptype>/<int:param_filter>/<str:ptypedocument>/', md_invoiced.consolidado_emitidos_filtrado, name='consolidado_emitidos_filtrado'),
    path('api/consolidate/', vw_app_views.consolidate, name='consolidate'),
    path('api/invoice_excel/', vw_app_views.invoice_excel, name='invoice_excel'),
    path('api/guardar/', vw_app_views.guardar_facturas_ajax, name='guardar'),
    path('api/upload_excel/', vw_app_views.upload_and_process_excel, name='upload_and_process_excel'),
    path('summary/sales/', vw_sales.summarysales, name='sales'),
    path('summary/update_filters/', vw_sales.update_filters, name='update_filters'),
    path('test/test/<int:mes>/', vw_test.test, name='test'),  # Add the new URL pattern for loadissued
    path('locationslist/', vw_locations.location_list, name='location_list'),
    path('locations/create/', vw_locations.location_create, name='location_create'),
    path('locations/edit/<int:pk>/', vw_locations.location_edit, name='location_edit'),
    path('locations/delete/<int:pk>/', vw_locations.location_delete, name='location_delete'),
    path('locations/create_child/<int:parent_pk>/', vw_locations.location_create_child, name='location_create_child'),
    path('api/load_location/<int:level>/<str:parent_id>/', md_invoiced.load_location, name='load_location'),
    path("locations/", vw_locations.children_options, name="children_options"),
    path("locations/<int:parent_id>/", vw_locations.children_options, name="children_by_parent"),
    path("children_options/", vw_locations.children_options, name="children_options"),
    path('api/invoicedLocation/', vw_invoicedLocation.consolidado_emitidos_localizacion_load, name='consolidado_emitidos_localizacion_load'),
    path('api/invoicedLocationdata/<str:pyears>/<str:pmonths>/<str:pgrouptype>/', md_invoicedLocation.consolidado_emitidos_localizacion_data, name='consolidado_emitidos_localizacion_data'),
    path("api/locationDetails/<str:level>/<int:locId>/<str:pyears>/<str:pmonths>/<str:pgrouptype>/", md_invoicedLocation.invoiced_location_details_by_id, name="invoiced_location_details_by_id"),
]