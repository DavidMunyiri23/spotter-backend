from datetime import datetime, timedelta
from typing import Dict, List
import json

class ELDLogGenerator:
    """Generate Electronic Logging Device logs based on HOS-compliant trip plans"""
    
    def __init__(self):
        # HOS Rules for property-carrying drivers
        self.max_driving_daily = 11  # hours
        self.max_on_duty_daily = 14  # hours
        self.mandatory_break_after = 8  # hours of driving
        self.mandatory_break_duration = 0.5  # 30 minutes
        self.min_off_duty_daily = 10  # hours between shifts
        
        # Duty status codes
        self.DUTY_STATUS = {
            'OFF_DUTY': 'off_duty',
            'SLEEPER_BERTH': 'sleeper_berth', 
            'DRIVING': 'driving',
            'ON_DUTY_NOT_DRIVING': 'on_duty_not_driving'
        }
    
    def generate_daily_logs(self, trip_plan: Dict, start_date: str = None) -> List[Dict]:
        """Generate detailed daily logs from HOS trip plan"""
        
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        daily_logs = []
        
        coordinates = trip_plan.get('coordinates', {})
        current_location = self._format_location(coordinates.get('current', []))
        pickup_location = self._format_location(coordinates.get('pickup', []))
        dropoff_location = self._format_location(coordinates.get('dropoff', []))
        hos_plan = trip_plan.get('hos_plan', {})
        
        # Calculate intermediate locations for multi-day trips
        daily_plans = hos_plan.get('daily_plans', [])
        
        for day_idx, daily_plan in enumerate(daily_plans):
            log_date = start_datetime + timedelta(days=day_idx)
            
            # Generate duty status changes for this day
            duty_status_changes = self._generate_duty_status_changes(
                daily_plan, 
                day_idx,
                current_location,
                pickup_location,
                dropoff_location,
                log_date
            )
            
            # Calculate totals
            totals = self._calculate_daily_totals(duty_status_changes)
            
            # Generate log sheet data
            daily_log = {
                'date': log_date.strftime('%Y-%m-%d'),
                'day_of_trip': day_idx + 1,
                'driver_name': 'Commercial Driver',  # This should come from trip data
                'duty_status_changes': duty_status_changes,
                'total_drive_time': totals['driving'],
                'total_on_duty_time': totals['on_duty_not_driving'] + totals['driving'],
                'total_sleeper_berth_time': totals['sleeper_berth'],
                'total_off_duty_time': totals['off_duty'],
                'distance_traveled': daily_plan['distance_miles'],
                'fuel_stops': daily_plan.get('fuel_stops', 0),
                'mandatory_breaks': daily_plan.get('mandatory_breaks', 0),
                'odometer_start': self._calculate_odometer(day_idx, daily_plans, 250000),  # Starting odometer
                'odometer_end': self._calculate_odometer(day_idx + 1, daily_plans, 250000),
                'vehicle_id': 'TRUCK001',
                'trailer_id': 'TRAILER001',
                'carrier_name': 'Commercial Carrier',
                'hos_compliant': self._check_hos_compliance(totals),
                'violations': self._check_violations(totals, duty_status_changes),
                'log_sheet_data': self._generate_log_sheet_grid(duty_status_changes)
            }
            
            daily_logs.append(daily_log)
        
        return daily_logs
    
    def _generate_duty_status_changes(self, daily_plan: Dict, day_idx: int, 
                                    current_loc: str, pickup_loc: str, 
                                    dropoff_loc: str, log_date: datetime) -> List[Dict]:
        """Generate detailed duty status changes for a day"""
        
        changes = []
        current_time = log_date.replace(hour=6, minute=0, second=0)  # Start at 6 AM
        
        # Start with off-duty status
        if day_idx > 0:  # If not first day, start with end of 10-hour break
            changes.append({
                'status': self.DUTY_STATUS['OFF_DUTY'],
                'time': current_time.strftime('%H:%M'),
                'location': current_loc if day_idx == 0 else 'Rest Area',
                'odometer': self._calculate_odometer(day_idx, [], 250000),
                'notes': 'End of required 10-hour off-duty period'
            })
        
        # Pre-trip inspection (On Duty Not Driving)
        current_time += timedelta(minutes=15)
        changes.append({
            'status': self.DUTY_STATUS['ON_DUTY_NOT_DRIVING'],
            'time': current_time.strftime('%H:%M'),
            'location': current_loc if day_idx == 0 else 'Rest Area',
            'odometer': self._calculate_odometer(day_idx, [], 250000),
            'notes': 'Pre-trip inspection'
        })
        
        # Pickup activities (if first day)
        if day_idx == 0:
            current_time += timedelta(minutes=45)
            changes.append({
                'status': self.DUTY_STATUS['ON_DUTY_NOT_DRIVING'],
                'time': current_time.strftime('%H:%M'),
                'location': pickup_loc,
                'odometer': self._calculate_odometer(day_idx, [], 250000) + 50,  # Travel to pickup
                'notes': 'Arrived at pickup location'
            })
            
            # Pickup time (1 hour)
            current_time += timedelta(hours=1)
            changes.append({
                'status': self.DUTY_STATUS['ON_DUTY_NOT_DRIVING'],
                'time': current_time.strftime('%H:%M'),
                'location': pickup_loc,
                'odometer': self._calculate_odometer(day_idx, [], 250000) + 50,
                'notes': 'Completed pickup - ready to drive'
            })
        
        # Driving periods with mandatory breaks
        driving_hours = daily_plan['driving_hours']
        remaining_driving = driving_hours
        total_distance = daily_plan['distance_miles']
        distance_covered = 0
        
        while remaining_driving > 0:
            # Driving period (max 8 hours before mandatory break)
            driving_segment = min(8.0, remaining_driving)
            
            # Start driving
            changes.append({
                'status': self.DUTY_STATUS['DRIVING'],
                'time': current_time.strftime('%H:%M'),
                'location': self._interpolate_location(distance_covered, total_distance, pickup_loc, dropoff_loc),
                'odometer': self._calculate_odometer(day_idx, [], 250000) + distance_covered,
                'notes': 'Begin driving'
            })
            
            # Add fuel stops during driving if needed
            segment_distance = (driving_segment / driving_hours) * total_distance
            if daily_plan.get('fuel_stops', 0) > 0 and segment_distance > 500:
                # Add fuel stop in middle of segment
                fuel_time = current_time + timedelta(hours=driving_segment/2)
                fuel_distance = distance_covered + segment_distance/2
                
                changes.append({
                    'status': self.DUTY_STATUS['ON_DUTY_NOT_DRIVING'],
                    'time': fuel_time.strftime('%H:%M'),
                    'location': f'Fuel Stop - {self._interpolate_location(fuel_distance, total_distance, pickup_loc, dropoff_loc)}',
                    'odometer': self._calculate_odometer(day_idx, [], 250000) + fuel_distance,
                    'notes': 'Fueling - 30 minutes'
                })
                
                # Resume driving after fuel
                fuel_time += timedelta(minutes=30)
                changes.append({
                    'status': self.DUTY_STATUS['DRIVING'],
                    'time': fuel_time.strftime('%H:%M'),
                    'location': f'Fuel Stop - {self._interpolate_location(fuel_distance, total_distance, pickup_loc, dropoff_loc)}',
                    'odometer': self._calculate_odometer(day_idx, [], 250000) + fuel_distance,
                    'notes': 'Resume driving after fuel'
                })
            
            # End of driving segment
            current_time += timedelta(hours=driving_segment)
            distance_covered += segment_distance
            remaining_driving -= driving_segment
            
            # Mandatory break if more driving remains and we've driven 8+ hours
            if remaining_driving > 0 and driving_segment >= 8:
                changes.append({
                    'status': self.DUTY_STATUS['OFF_DUTY'],
                    'time': current_time.strftime('%H:%M'),
                    'location': 'Rest Area',
                    'odometer': self._calculate_odometer(day_idx, [], 250000) + distance_covered,
                    'notes': 'Mandatory 30-minute break after 8 hours driving'
                })
                
                current_time += timedelta(minutes=30)
        
        # Dropoff activities (if last day)
        if day_idx == len(daily_plan) - 1 or daily_plan.get('is_final_day', False):
            changes.append({
                'status': self.DUTY_STATUS['ON_DUTY_NOT_DRIVING'],
                'time': current_time.strftime('%H:%M'),
                'location': dropoff_loc,
                'odometer': self._calculate_odometer(day_idx, [], 250000) + total_distance,
                'notes': 'Arrived at delivery location'
            })
            
            # Dropoff time (1 hour)
            current_time += timedelta(hours=1)
            changes.append({
                'status': self.DUTY_STATUS['ON_DUTY_NOT_DRIVING'],
                'time': current_time.strftime('%H:%M'),
                'location': dropoff_loc,
                'odometer': self._calculate_odometer(day_idx, [], 250000) + total_distance,
                'notes': 'Completed delivery'
            })
        
        # Post-trip inspection and end of duty
        current_time += timedelta(minutes=15)
        changes.append({
            'status': self.DUTY_STATUS['ON_DUTY_NOT_DRIVING'],
            'time': current_time.strftime('%H:%M'),
            'location': dropoff_loc if day_idx == len(daily_plan) - 1 else 'Rest Area',
            'odometer': self._calculate_odometer(day_idx, [], 250000) + total_distance,
            'notes': 'Post-trip inspection'
        })
        
        # Off duty for required rest period
        current_time += timedelta(minutes=15)
        changes.append({
            'status': self.DUTY_STATUS['OFF_DUTY'],
            'time': current_time.strftime('%H:%M'),
            'location': dropoff_loc if day_idx == len(daily_plan) - 1 else 'Rest Area',
            'odometer': self._calculate_odometer(day_idx, [], 250000) + total_distance,
            'notes': 'Begin 10-hour off-duty period'
        })
        
        return changes
    
    def _calculate_daily_totals(self, duty_status_changes: List[Dict]) -> Dict:
        """Calculate total hours for each duty status"""
        totals = {
            'driving': 0.0,
            'on_duty_not_driving': 0.0,
            'sleeper_berth': 0.0,
            'off_duty': 0.0
        }
        
        # Simple calculation based on duty status changes
        # In a real implementation, this would calculate actual time differences
        for i, change in enumerate(duty_status_changes[:-1]):
            next_change = duty_status_changes[i + 1]
            
            # Calculate time difference (simplified)
            current_time = datetime.strptime(change['time'], '%H:%M')
            next_time = datetime.strptime(next_change['time'], '%H:%M')
            
            # Handle day rollover
            if next_time < current_time:
                next_time += timedelta(days=1)
            
            duration = (next_time - current_time).total_seconds() / 3600
            
            status = change['status']
            if status in totals:
                totals[status] += duration
        
        return totals
    
    def _check_hos_compliance(self, totals: Dict) -> bool:
        """Check if daily totals comply with HOS regulations"""
        return (totals['driving'] <= self.max_driving_daily and 
                totals['driving'] + totals['on_duty_not_driving'] <= self.max_on_duty_daily)
    
    def _check_violations(self, totals: Dict, changes: List[Dict]) -> List[str]:
        """Check for HOS violations"""
        violations = []
        
        if totals['driving'] > self.max_driving_daily:
            violations.append(f"Exceeded maximum daily driving time: {totals['driving']:.1f}h > {self.max_driving_daily}h")
        
        if totals['driving'] + totals['on_duty_not_driving'] > self.max_on_duty_daily:
            total_on_duty = totals['driving'] + totals['on_duty_not_driving']
            violations.append(f"Exceeded maximum daily on-duty time: {total_on_duty:.1f}h > {self.max_on_duty_daily}h")
        
        # Check for driving without required breaks (simplified)
        consecutive_driving = 0
        for change in changes:
            if change['status'] == self.DUTY_STATUS['DRIVING']:
                consecutive_driving += 1
            elif change['status'] in [self.DUTY_STATUS['OFF_DUTY'], self.DUTY_STATUS['SLEEPER_BERTH']]:
                consecutive_driving = 0
            
            if consecutive_driving > 16:  # Rough check for 8+ hours without break
                violations.append("Drove more than 8 hours without mandatory 30-minute break")
                break
        
        return violations
    
    def _generate_log_sheet_grid(self, duty_status_changes: List[Dict]) -> Dict:
        """Generate data for visual log sheet representation"""
        # Create 24-hour grid (15-minute intervals = 96 slots)
        grid = ['off_duty'] * 96  # Default to off-duty
        
        for i, change in enumerate(duty_status_changes):
            if i < len(duty_status_changes) - 1:
                start_time = datetime.strptime(change['time'], '%H:%M')
                end_time = datetime.strptime(duty_status_changes[i + 1]['time'], '%H:%M')
                
                # Handle day rollover
                if end_time < start_time:
                    end_time += timedelta(days=1)
                
                # Convert to 15-minute slots
                start_slot = (start_time.hour * 4) + (start_time.minute // 15)
                end_slot = min(96, (end_time.hour * 4) + (end_time.minute // 15))
                
                # Fill grid slots
                for slot in range(start_slot, end_slot):
                    if slot < 96:
                        grid[slot] = change['status']
        
        return {
            'grid': grid,
            'time_slots': [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 15, 30, 45]]
        }
    
    def _format_location(self, coords: List) -> str:
        """Format coordinates to location string"""
        if not coords or len(coords) < 2:
            return "Unknown Location"
        return f"{coords[0]:.4f}, {coords[1]:.4f}"
    
    def _interpolate_location(self, distance_covered: float, total_distance: float, 
                            start_loc: str, end_loc: str) -> str:
        """Simple location interpolation for intermediate stops"""
        if total_distance == 0:
            return start_loc
        
        progress = distance_covered / total_distance
        if progress < 0.3:
            return f"En route from {start_loc}"
        elif progress < 0.7:
            return f"Highway - {int(progress * 100)}% to destination"
        else:
            return f"Approaching {end_loc}"
    
    def _calculate_odometer(self, day_idx: int, daily_plans: List, base_odometer: int) -> int:
        """Calculate cumulative odometer reading"""
        total_distance = 0
        for i in range(day_idx):
            if i < len(daily_plans):
                total_distance += daily_plans[i].get('distance_miles', 0)
        return base_odometer + int(total_distance)

# Global instance
eld_log_generator = ELDLogGenerator()