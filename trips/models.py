from django.db import models


class Trip(models.Model):
    current_location = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    current_cycle_used = models.FloatField(help_text="Hours used in the 70hr/8-day cycle")
    distance = models.FloatField(default=0)
    route_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trip from {self.pickup_location} to {self.dropoff_location}"

    class Meta:
        ordering = ['-created_at']


class DailyLog(models.Model):
    trip = models.ForeignKey(Trip, related_name="logs", on_delete=models.CASCADE)
    date = models.DateField()
    driving_hours = models.FloatField()
    on_duty_hours = models.FloatField()
    sleeper_berth_hours = models.FloatField()
    off_duty_hours = models.FloatField()
    log_image_url = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Daily Log for {self.date} - Trip {self.trip.id}"

    class Meta:
        ordering = ['-date']