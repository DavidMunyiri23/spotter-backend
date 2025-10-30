import requests
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import math

class RouteService:
    """Service for calculating routes and generating HOS-compliant trip plans"""
    
    # Using OpenRouteService API (free tier: 2000 requests/day)
    ORS_BASE_URL = "https://api.openrouteservice.org/v2"
    
    def __init__(self, api_key: str = None):
        # Default API key - in production this should be in environment variables
        # This is a demo key, replace with your own from openrouteservice.org
        self.api_key = api_key or "5b3ce3597851110001cf6248d8b0ca25b2a043f1b4b6ef0ca2b2dc8a"
        self.headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def geocode_location(self, location: str) -> Optional[Tuple[float, float]]:
        """Convert location string to coordinates using fallback first"""
        # Use fallback coordinates for common cities first for reliability
        fallback_coords = {
            'new york': (40.7128, -74.0060),
            'los angeles': (34.0522, -118.2437),
            'chicago': (41.8781, -87.6298),
            'houston': (29.7604, -95.3698),
            'atlanta': (33.7490, -84.3880),
            'dallas': (32.7767, -96.7970),
            'philadelphia': (39.9526, -75.1652),
            'phoenix': (33.4484, -112.0740),
            'san antonio': (29.4241, -98.4936),
            'san diego': (32.7157, -117.1611),
            'detroit': (42.3314, -83.0458),
            'san jose': (37.3382, -121.8863),
            'indianapolis': (39.7684, -86.1581),
            'jacksonville': (30.3322, -81.6557),
            'san francisco': (37.7749, -122.4194),
            'columbus': (39.9612, -82.9988),
            'charlotte': (35.2271, -80.8431),
            'fort worth': (32.7555, -97.3308),
            'denver': (39.7392, -104.9903),
            'el paso': (31.7619, -106.4850),
            'memphis': (35.1495, -90.0490),
            'seattle': (47.6062, -122.3321),
            'boston': (42.3601, -71.0589),
            'nashville': (36.1627, -86.7816),
            'baltimore': (39.2904, -76.6122),
            'oklahoma city': (35.4676, -97.5164),
            'portland': (45.5152, -122.6784),
            'las vegas': (36.1699, -115.1398),
            'milwaukee': (43.0389, -87.9065),
            'albuquerque': (35.0844, -106.6504),
            'tucson': (32.2226, -110.9747),
            'fresno': (36.7378, -119.7871),
            'sacramento': (38.5816, -121.4944),
            'kansas city': (39.0997, -94.5786),
            'mesa': (33.4152, -111.8315),
            'virginia beach': (36.8529, -75.9780),
            'omaha': (41.2565, -95.9345),
            'colorado springs': (38.8339, -104.8214),
            'raleigh': (35.7796, -78.6382),
            'miami': (25.7617, -80.1918),
            'oakland': (37.8044, -122.2712),
            'minneapolis': (44.9778, -93.2650),
            'tulsa': (36.1540, -95.9928),
            'cleveland': (41.4993, -81.6944),
            'wichita': (37.6872, -97.3301),
            'arlington': (32.7357, -97.1081)
        }
        
        location_lower = location.lower()
        for key, coords in fallback_coords.items():
            if key in location_lower:
                print(f"Using fallback coordinates for '{location}': {coords}")
                return coords
        
        # Try OpenRouteService API as fallback
        try:
            url = f"{self.ORS_BASE_URL}/geocode/search"
            params = {
                'api_key': self.api_key,
                'text': location,
                'size': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data['features']:
                coords = data['features'][0]['geometry']['coordinates']
                return (coords[1], coords[0])  # Return as (lat, lon)
            
        except Exception as e:
            print(f"Geocoding error for '{location}': {e}")
        
        return None
    
    def calculate_route(self, start_coords: Tuple[float, float], 
                       end_coords: Tuple[float, float]) -> Dict:
        """Calculate route between two coordinates"""
        try:
            url = f"{self.ORS_BASE_URL}/directions/driving-car"
            
            body = {
                "coordinates": [[start_coords[1], start_coords[0]], 
                               [end_coords[1], end_coords[0]]],
                "format": "json",
                "instructions": True,
                "geometry": True
            }
            
            response = requests.post(url, 
                                   headers=self.headers, 
                                   json=body, 
                                   timeout=15)
            response.raise_for_status()
            
            data = response.json()
            route = data['routes'][0]
            
            # Extract route information
            distance_miles = route['summary']['distance'] * 0.000621371  # Convert meters to miles
            duration_hours = route['summary']['duration'] / 3600  # Convert seconds to hours
            
            # Decode geometry for map visualization
            geometry = self._decode_polyline(route['geometry'])
            
            # Extract turn-by-turn instructions
            instructions = []
            for step in route['segments'][0]['steps']:
                instructions.append({
                    'instruction': step['instruction'],
                    'distance': step['distance'] * 0.000621371,  # Convert to miles
                    'duration': step['duration'] / 60  # Convert to minutes
                })
            
            return {
                'distance_miles': distance_miles,
                'duration_hours': duration_hours,
                'geometry': geometry,
                'instructions': instructions,
                'success': True
            }
            
        except Exception as e:
            print(f"Route calculation error: {e}")
            # Return fallback route calculation
            distance_miles = self._calculate_distance_fallback(start_coords, end_coords)
            duration_hours = distance_miles / 55  # Assume 55 mph average
            
            return {
                'distance_miles': distance_miles,
                'duration_hours': duration_hours,
                'geometry': [start_coords, end_coords],
                'instructions': [
                    {'instruction': f'Drive from start to destination', 
                     'distance': distance_miles, 'duration': duration_hours * 60}
                ],
                'success': False,
                'fallback': True
            }
    
    def _decode_polyline(self, polyline_str: str) -> List[Tuple[float, float]]:
        """Decode polyline string to list of coordinates"""
        # This is a simplified decoder - for production use a proper polyline library
        try:
            import polyline
            return polyline.decode(polyline_str)
        except ImportError:
            # Fallback if polyline library not available
            return []
    
    def _calculate_distance_fallback(self, coord1: Tuple[float, float], 
                                   coord2: Tuple[float, float]) -> float:
        """Calculate distance using Haversine formula as fallback"""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in miles
        r = 3956
        return c * r
    
    def generate_hos_compliant_plan(self, route_info: Dict, current_cycle_used: float) -> Dict:
        """Generate HOS-compliant trip plan with breaks and fuel stops"""
        distance_miles = route_info['distance_miles']
        driving_hours = route_info['duration_hours']
        
        # HOS Rules (Property-carrying, 70hr/8-day cycle)
        max_driving_daily = 11  # hours
        max_on_duty_daily = 14  # hours
        max_cycle_hours = 70    # hours in 8 days
        mandatory_break_after = 8  # hours of driving
        fuel_stop_interval = 1000  # miles
        
        # Calculate available hours
        remaining_cycle_hours = max_cycle_hours - current_cycle_used
        
        # Calculate fuel stops needed
        fuel_stops = math.ceil(distance_miles / fuel_stop_interval) - 1
        fuel_stop_time = fuel_stops * 0.5  # 30 minutes per fuel stop
        
        # Add pickup/dropoff time (1 hour each)
        pickup_dropoff_time = 2.0
        
        # Calculate total on-duty time needed
        total_on_duty_needed = driving_hours + fuel_stop_time + pickup_dropoff_time
        
        # Calculate mandatory breaks needed
        mandatory_breaks = math.floor(driving_hours / mandatory_break_after)
        mandatory_break_time = mandatory_breaks * 0.5  # 30 min breaks
        
        # Calculate total time including breaks
        total_time_with_breaks = total_on_duty_needed + mandatory_break_time
        
        # Determine if multi-day trip is needed
        days_needed = math.ceil(total_time_with_breaks / max_on_duty_daily)
        
        # Generate day-by-day plan
        daily_plans = []
        remaining_distance = distance_miles
        remaining_driving = driving_hours
        current_day = 1
        
        while remaining_distance > 0 and current_day <= days_needed:
            # Calculate max driving for this day
            max_driving_today = min(max_driving_daily, remaining_driving)
            
            # Calculate distance covered today (assuming consistent speed)
            avg_speed = distance_miles / driving_hours if driving_hours > 0 else 55
            distance_today = max_driving_today * avg_speed
            
            # Check if we need fuel stops today
            fuel_stops_today = 0
            if distance_today >= fuel_stop_interval:
                fuel_stops_today = math.floor(distance_today / fuel_stop_interval)
            
            # Calculate breaks needed today
            breaks_today = math.floor(max_driving_today / mandatory_break_after)
            
            daily_plan = {
                'day': current_day,
                'driving_hours': max_driving_today,
                'distance_miles': distance_today,
                'fuel_stops': fuel_stops_today,
                'mandatory_breaks': breaks_today,
                'total_on_duty': max_driving_today + (fuel_stops_today * 0.5),
                'pickup_dropoff_time': pickup_dropoff_time if current_day == 1 else 0
            }
            
            # Add pickup time on first day, dropoff time on last day
            if current_day == 1:
                daily_plan['total_on_duty'] += 1  # Pickup time
            if remaining_distance - distance_today <= 0:
                daily_plan['total_on_duty'] += 1  # Dropoff time
            
            daily_plans.append(daily_plan)
            
            remaining_distance -= distance_today
            remaining_driving -= max_driving_today
            current_day += 1
        
        return {
            'total_distance': distance_miles,
            'total_driving_hours': driving_hours,
            'total_days_needed': days_needed,
            'total_fuel_stops': fuel_stops,
            'remaining_cycle_hours': remaining_cycle_hours,
            'cycle_compliant': total_time_with_breaks <= remaining_cycle_hours,
            'daily_plans': daily_plans,
            'summary': {
                'total_on_duty_time': total_on_duty_needed,
                'mandatory_break_time': mandatory_break_time,
                'fuel_stop_time': fuel_stop_time,
                'pickup_dropoff_time': pickup_dropoff_time
            }
        }
    
    def get_trip_plan(self, current_location: str, pickup_location: str, 
                     dropoff_location: str, current_cycle_used: float) -> Dict:
        """Complete trip planning with route calculation and HOS compliance"""
        
        # Geocode all locations
        current_coords = self.geocode_location(current_location)
        pickup_coords = self.geocode_location(pickup_location)
        dropoff_coords = self.geocode_location(dropoff_location)
        
        if not all([current_coords, pickup_coords, dropoff_coords]):
            return {
                'success': False,
                'error': 'Could not geocode one or more locations'
            }
        
        # Calculate route from current to pickup
        route_to_pickup = self.calculate_route(current_coords, pickup_coords)
        
        # Calculate main route from pickup to dropoff
        main_route = self.calculate_route(pickup_coords, dropoff_coords)
        
        # Combine routes
        total_distance = route_to_pickup['distance_miles'] + main_route['distance_miles']
        total_duration = route_to_pickup['duration_hours'] + main_route['duration_hours']
        
        combined_route_info = {
            'distance_miles': total_distance,
            'duration_hours': total_duration,
            'geometry': route_to_pickup['geometry'] + main_route['geometry'],
            'instructions': route_to_pickup['instructions'] + main_route['instructions']
        }
        
        # Generate HOS-compliant plan
        hos_plan = self.generate_hos_compliant_plan(combined_route_info, current_cycle_used)
        
        return {
            'success': True,
            'coordinates': {
                'current': current_coords,
                'pickup': pickup_coords,
                'dropoff': dropoff_coords
            },
            'route_to_pickup': route_to_pickup,
            'main_route': main_route,
            'combined_route': combined_route_info,
            'hos_plan': hos_plan
        }

# Global instance
route_service = RouteService()