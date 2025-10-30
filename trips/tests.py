from django.test import TestCase
from .models import Trip, DailyLog


class TripModelTest(TestCase):
    def setUp(self):
        self.trip = Trip.objects.create(
            current_location="Chicago, IL",
            pickup_location="Denver, CO",
            dropoff_location="Atlanta, GA",
            current_cycle_used=45.5,
            distance=1200.0
        )

    def test_trip_creation(self):
        self.assertEqual(self.trip.current_location, "Chicago, IL")
        self.assertEqual(self.trip.pickup_location, "Denver, CO")
        self.assertEqual(self.trip.dropoff_location, "Atlanta, GA")
        self.assertEqual(self.trip.current_cycle_used, 45.5)
        self.assertEqual(self.trip.distance, 1200.0)

    def test_trip_str(self):
        expected = "Trip from Denver, CO to Atlanta, GA"
        self.assertEqual(str(self.trip), expected)