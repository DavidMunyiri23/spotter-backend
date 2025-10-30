from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import Trip, DailyLog
from .serializers import TripSerializer, DailyLogSerializer
from .mongodb_manager import mongodb_manager
from .route_service import route_service
from .eld_log_generator import eld_log_generator
from datetime import datetime
import json


@api_view(['GET'])
def mongodb_status(request):
    """Check MongoDB connection status"""
    try:
        if mongodb_manager.is_connected():
            # Get some basic stats
            trips_count = len(mongodb_manager.get_trips(limit=1000))  # Get actual count
            logs_count = len(mongodb_manager.get_all_logs(limit=1000))
            
            return Response({
                'status': 'connected',
                'database': 'hos_tracker_db',
                'trips_count': trips_count,
                'logs_count': logs_count,
                'message': 'MongoDB connection successful'
            })
        else:
            return Response({
                'status': 'disconnected',
                'message': 'MongoDB connection failed',
                'suggestion': 'Check credentials and network connection'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def calculate_route(request):
    """Calculate route and generate HOS-compliant trip plan"""
    try:
        data = request.data
        current_location = data.get('current_location', '')
        pickup_location = data.get('pickup_location', '')
        dropoff_location = data.get('dropoff_location', '')
        current_cycle_used = float(data.get('current_cycle_used', 0))
        
        if not all([current_location, pickup_location, dropoff_location]):
            return Response({
                'success': False,
                'error': 'All location fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get complete trip plan
        trip_plan = route_service.get_trip_plan(
            current_location, pickup_location, dropoff_location, current_cycle_used
        )
        
        return Response(trip_plan)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Route calculation failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def generate_eld_logs(request):
    """Generate ELD logs from trip plan"""
    try:
        data = request.data
        trip_plan = data.get('trip_plan')
        start_date = data.get('start_date')
        
        if not trip_plan:
            return Response({
                'success': False,
                'error': 'Trip plan is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate daily logs
        daily_logs = eld_log_generator.generate_daily_logs(trip_plan, start_date)
            
        return Response({
            'success': True,
            'daily_logs': daily_logs,
            'total_days': len(daily_logs)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'ELD log generation failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def save_trip_with_eld_logs(request):
    """Save trip with route data and ELD logs to database"""
    try:
        data = request.data
        
        # Create trip in MongoDB
        trip_data = {
            'current_location': data.get('current_location', ''),
            'pickup_location': data.get('pickup_location', ''),
            'dropoff_location': data.get('dropoff_location', ''),
            'current_cycle_used': float(data.get('current_cycle_used', 0)),
            'route_data': data.get('route_data', {}),
            'eld_logs': data.get('eld_logs', [])
        }
        
        # Save to MongoDB
        saved_trip = mongodb_manager.create_trip(trip_data)
        
        if saved_trip:
            return Response({
                'success': True,
                'trip': saved_trip
            })
        else:
            # Fallback to Django ORM
            trip = Trip.objects.create(
                current_location=trip_data['current_location'],
                pickup_location=trip_data['pickup_location'],
                dropoff_location=trip_data['dropoff_location'],
                current_cycle_used=trip_data['current_cycle_used']
            )
            
            serializer = TripSerializer(trip)
            return Response({
                'success': True,
                'trip': serializer.data
            })
            
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to save trip: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_trip_eld_logs(request, trip_id):
    """Get ELD logs for a specific trip"""
    try:
        # Try to get from MongoDB first
        trip = mongodb_manager.get_trip_by_id(trip_id)
        
        if trip and 'eld_logs' in trip:
            return Response({
                'success': True,
                'eld_logs': trip['eld_logs']
            })
        else:
            return Response({
                'success': False,
                'error': 'No ELD logs found for this trip'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to retrieve ELD logs: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all().order_by('-created_at')
    serializer_class = TripSerializer
    pagination_class = StandardResultsSetPagination

    def list(self, request):
        """List trips from MongoDB, with SQLite fallback"""
        try:
            if mongodb_manager.is_connected():
                trips = mongodb_manager.get_trips(limit=20)
                # Convert MongoDB format to Django model format
                django_trips = []
                for trip in trips:
                    django_trip = {
                        'id': trip['_id'],
                        'current_location': trip.get('current_location', ''),
                        'pickup_location': trip.get('pickup_location', ''),
                        'dropoff_location': trip.get('dropoff_location', ''),
                        'current_cycle_used': trip.get('current_cycle_used', 0),
                        'distance': trip.get('distance', 0),
                        'route_data': trip.get('route_data', {}),
                        'created_at': trip.get('created_at', datetime.now()).isoformat(),
                        'logs': []  # Will be populated separately if needed
                    }
                    django_trips.append(django_trip)
                return Response({'results': django_trips, 'data_source': 'mongodb'})
            else:
                # Fallback to SQLite/Django ORM
                print("⚠️ MongoDB not connected, using SQLite fallback")
                return super().list(request)
        except Exception as e:
            print(f"Error in trip list: {e}")
            # Fallback to Django models on any MongoDB error
            print("⚠️ MongoDB error, falling back to SQLite")
            return super().list(request)

    def create(self, request):
        """Create trip in MongoDB, with SQLite fallback"""
        try:
            if mongodb_manager.is_connected():
                trip_data = {
                    'current_location': request.data.get('current_location', ''),
                    'pickup_location': request.data.get('pickup_location', ''),
                    'dropoff_location': request.data.get('dropoff_location', ''),
                    'current_cycle_used': float(request.data.get('current_cycle_used', 0)),
                    'distance': float(request.data.get('distance', 0)),
                    'route_data': request.data.get('route_data', {}),
                }
                
                created_trip = mongodb_manager.create_trip(trip_data)
                if created_trip:
                    response_data = {
                        'id': created_trip['_id'],
                        'current_location': created_trip['current_location'],
                        'pickup_location': created_trip['pickup_location'],
                        'dropoff_location': created_trip['dropoff_location'],
                        'current_cycle_used': created_trip['current_cycle_used'],
                        'distance': created_trip['distance'],
                        'route_data': created_trip['route_data'],
                        'created_at': created_trip['created_at'].isoformat(),
                        'logs': [],
                        'data_source': 'mongodb'
                    }
                    return Response(response_data, status=status.HTTP_201_CREATED)
            
            # Fallback to SQLite/Django ORM
            print("⚠️ MongoDB not connected, using SQLite fallback")
            return super().create(request)
        except Exception as e:
            print(f"Error creating trip in MongoDB: {e}")
            # Fallback to Django models on any MongoDB error
            print("⚠️ MongoDB error, falling back to SQLite")
            return super().create(request)

    def retrieve(self, request, pk=None):
        """Get single trip from MongoDB"""
        try:
            trip = mongodb_manager.get_trip_by_id(pk)
            if trip:
                # Get logs for this trip
                logs = mongodb_manager.get_logs_by_trip(pk)
                trip['logs'] = logs
                trip['id'] = trip['_id']
                return Response(trip)
            else:
                return Response({'error': 'Trip not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error retrieving trip: {e}")
            return Response({'error': 'Failed to retrieve trip', 'details': str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get all logs for a specific trip"""
        try:
            logs = mongodb_manager.get_logs_by_trip(pk)
            return Response(logs)
        except Exception as e:
            print(f"Error getting trip logs: {e}")
            return Response({'error': 'Failed to get logs', 'details': str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DailyLogViewSet(viewsets.ModelViewSet):
    queryset = DailyLog.objects.all()
    serializer_class = DailyLogSerializer
    pagination_class = StandardResultsSetPagination

    def list(self, request):
        """List logs from MongoDB, with SQLite fallback"""
        try:
            if mongodb_manager.is_connected():
                trip_id = request.query_params.get('trip', None)
                
                if trip_id:
                    logs = mongodb_manager.get_logs_by_trip(trip_id)
                else:
                    logs = mongodb_manager.get_all_logs(limit=50)
                
                # Convert MongoDB format to Django format
                django_logs = []
                for log in logs:
                    django_log = {
                        'id': log['_id'],
                        'trip': log.get('trip_id', ''),
                        'date': log.get('date', ''),
                        'driving_hours': log.get('driving_hours', 0),
                        'on_duty_hours': log.get('on_duty_hours', 0),
                        'sleeper_berth_hours': log.get('sleeper_berth_hours', 0),
                        'off_duty_hours': log.get('off_duty_hours', 0),
                        'log_image_url': log.get('log_image_url', ''),
                        'created_at': log.get('created_at', datetime.now()).isoformat(),
                    }
                    django_logs.append(django_log)
                
                return Response({'results': django_logs, 'data_source': 'mongodb'})
            else:
                # Fallback to SQLite/Django ORM
                print("⚠️ MongoDB not connected, using SQLite fallback")
                return super().list(request)
        except Exception as e:
            print(f"Error in logs list: {e}")
            # Fallback to Django models on any MongoDB error
            print("⚠️ MongoDB error, falling back to SQLite")
            return super().list(request)

    def create(self, request):
        """Create daily log in MongoDB, with SQLite fallback"""
        try:
            if mongodb_manager.is_connected():
                log_data = {
                    'trip_id': request.data.get('trip', ''),
                    'date': request.data.get('date', ''),
                    'driving_hours': float(request.data.get('driving_hours', 0)),
                    'on_duty_hours': float(request.data.get('on_duty_hours', 0)),
                    'sleeper_berth_hours': float(request.data.get('sleeper_berth_hours', 0)),
                    'off_duty_hours': float(request.data.get('off_duty_hours', 0)),
                    'log_image_url': request.data.get('log_image_url', ''),
                }
                
                created_log = mongodb_manager.create_daily_log(log_data)
                if created_log:
                    response_data = {
                        'id': created_log['_id'],
                        'trip': created_log['trip_id'],
                        'date': created_log['date'],
                        'driving_hours': created_log['driving_hours'],
                        'on_duty_hours': created_log['on_duty_hours'],
                        'sleeper_berth_hours': created_log['sleeper_berth_hours'],
                        'off_duty_hours': created_log['off_duty_hours'],
                        'log_image_url': created_log['log_image_url'],
                        'created_at': created_log['created_at'].isoformat(),
                        'data_source': 'mongodb'
                    }
                    return Response(response_data, status=status.HTTP_201_CREATED)
            
            # Fallback to SQLite/Django ORM
            print("⚠️ MongoDB not connected, using SQLite fallback")
            return super().create(request)
        except Exception as e:
            print(f"Error creating log in MongoDB: {e}")
            # Fallback to Django models on any MongoDB error
            print("⚠️ MongoDB error, falling back to SQLite")
            return super().create(request)