from django.contrib import admin
from .models import Trip, DailyLog


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['id', 'current_location', 'pickup_location', 'dropoff_location', 'current_cycle_used', 'created_at']
    list_filter = ['created_at']
    search_fields = ['current_location', 'pickup_location', 'dropoff_location']


@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'trip', 'date', 'driving_hours', 'on_duty_hours', 'sleeper_berth_hours', 'off_duty_hours']
    list_filter = ['date', 'trip']
    search_fields = ['trip__pickup_location', 'trip__dropoff_location']