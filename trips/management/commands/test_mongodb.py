from django.core.management.base import BaseCommand
from trips.mongodb_manager import mongodb_manager
import os


class Command(BaseCommand):
    help = 'Test MongoDB connection and display connection details'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Testing MongoDB Connection'))
        self.stdout.write('=' * 50)
        
        # Display environment variables
        username = os.getenv('MONGO_USERNAME', 'NOT_SET')
        password = os.getenv('MONGO_PASSWORD', 'NOT_SET')
        
        self.stdout.write(f'📋 Environment Variables:')
        self.stdout.write(f'   MONGO_USERNAME: {username}')
        self.stdout.write(f'   MONGO_PASSWORD: {"*" * len(password) if password != "NOT_SET" else "NOT_SET"}')
        self.stdout.write('')
        
        # Test connection
        self.stdout.write('🔗 Testing connection...')
        
        if mongodb_manager.is_connected():
            self.stdout.write(self.style.SUCCESS('✅ MongoDB connection successful!'))
            
            # Test operations
            try:
                # Test trip operations
                test_trip = {
                    'current_location': 'Test Location',
                    'pickup_location': 'Test Pickup',
                    'dropoff_location': 'Test Dropoff',
                    'current_cycle_used': 0.0,
                    'distance': 0.0,
                    'route_data': {}
                }
                
                created_trip = mongodb_manager.create_trip(test_trip)
                if created_trip:
                    self.stdout.write(self.style.SUCCESS('✅ Trip creation test successful'))
                    
                    # Clean up test data
                    if mongodb_manager.delete_trip(created_trip['_id']):
                        self.stdout.write(self.style.SUCCESS('✅ Trip deletion test successful'))
                    
                trips_count = len(mongodb_manager.get_trips(limit=1))
                self.stdout.write(f'📊 Current trips in database: {trips_count}')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Database operations failed: {e}'))
                
        else:
            self.stdout.write(self.style.ERROR('❌ MongoDB connection failed'))
            self.stdout.write('')
            self.stdout.write('🛠️ Troubleshooting steps:')
            self.stdout.write('   1. Check your internet connection')
            self.stdout.write('   2. Verify MongoDB credentials in .env file')
            self.stdout.write('   3. Ensure MongoDB Atlas cluster is running')
            self.stdout.write('   4. Check firewall/network restrictions')
        
        self.stdout.write('=' * 50)