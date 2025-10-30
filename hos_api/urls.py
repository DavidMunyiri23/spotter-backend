from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework import routers
from trips.views import TripViewSet, DailyLogViewSet, mongodb_status, calculate_route, generate_eld_logs, save_trip_with_eld_logs, get_trip_eld_logs, generate_eld_logs, generate_eld_logs

def health_check(request):
    return JsonResponse({"status": "healthy", "service": "FMCSA HOS Tracker API"})

router = routers.DefaultRouter()
router.register(r'trips', TripViewSet)
router.register(r'logs', DailyLogViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/health/', health_check, name='health-check'),
    path('api/mongodb-status/', mongodb_status, name='mongodb-status'),
    path('api/calculate-route/', calculate_route, name='calculate-route'),
    path('api/generate-eld-logs/', generate_eld_logs, name='generate-eld-logs'),
    path('api/save-trip-with-eld/', save_trip_with_eld_logs, name='save-trip-with-eld'),
    path('api/trips/<str:trip_id>/eld-logs/', get_trip_eld_logs, name='get-trip-eld-logs'),
]