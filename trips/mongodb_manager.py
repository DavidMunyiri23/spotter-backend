from pymongo import MongoClient
from django.conf import settings
import os
from datetime import datetime

class MongoDBManager:
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self.connect()
    
    def connect(self):
        try:
            mongo_settings = getattr(settings, 'MONGODB_SETTINGS', {})
            host = mongo_settings.get('host')
            db_name = mongo_settings.get('db_name', 'hos_tracker_db')
            
            if not host:
                # Use environment variables with the correct SpotterAI connection string format
                username = os.getenv('MONGO_USERNAME', 'davidmunyiri2019_db_user')
                password = os.getenv('MONGO_PASSWORD', 'Zq8kwCsEH7f7M8Ox')
                
                # Use the correct SpotterAI MongoDB connection string format
                host = f'mongodb+srv://{username}:{password}@spotterai.filnzzr.mongodb.net/?appName=spotterai'
            
            print(f"🔗 Attempting to connect to MongoDB...")
            print(f"📍 Database: {db_name}")
            
            # Create client with timeout settings
            self._client = MongoClient(
                host,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            self._db = self._client[db_name]
            
            # Test connection
            self._client.admin.command('ping')
            print(f"✅ Successfully connected to MongoDB: {db_name}")
            
            # Test collections access
            collections = self._db.list_collection_names()
            print(f"📚 Available collections: {collections}")
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            print(f"🔍 Connection details - Host: mongodb+srv://***:***@cluster0.mongodb.net/{db_name}")
            self._client = None
            self._db = None
    
    @property
    def db(self):
        if self._db is None:
            self.connect()
        return self._db
    
    @property
    def client(self):
        if self._client is None:
            self.connect()
        return self._client
    
    def is_connected(self):
        if self._client is None:
            return False
        try:
            # Test the actual connection
            self._client.admin.command('ping')
            return True
        except Exception:
            return False
    
    # Collections
    @property
    def trips(self):
        if self._db is not None:
            return self._db.trips
        return None
    
    @property
    def daily_logs(self):
        if self._db is not None:
            return self._db.daily_logs
        return None
    
    # Helper methods for Trip operations
    def create_trip(self, trip_data):
        if self.trips is None:
            return None
        
        trip_data['created_at'] = datetime.utcnow()
        result = self.trips.insert_one(trip_data)
        trip_data['_id'] = str(result.inserted_id)
        return trip_data
    
    def get_trips(self, limit=20, skip=0):
        if self.trips is None:
            return []
        
        trips = list(self.trips.find().sort('created_at', -1).skip(skip).limit(limit))
        for trip in trips:
            trip['_id'] = str(trip['_id'])
        return trips
    
    def get_trip_by_id(self, trip_id):
        if self.trips is None:
            return None
        
        from bson import ObjectId
        try:
            trip = self.trips.find_one({'_id': ObjectId(trip_id)})
            if trip:
                trip['_id'] = str(trip['_id'])
            return trip
        except:
            return None
    
    def update_trip(self, trip_id, update_data):
        if self.trips is None:
            return None
        
        from bson import ObjectId
        try:
            result = self.trips.update_one(
                {'_id': ObjectId(trip_id)}, 
                {'$set': update_data}
            )
            return result.modified_count > 0
        except:
            return False
    
    def delete_trip(self, trip_id):
        if self.trips is None:
            return False
        
        from bson import ObjectId
        try:
            result = self.trips.delete_one({'_id': ObjectId(trip_id)})
            return result.deleted_count > 0
        except:
            return False
    
    # Helper methods for Daily Log operations
    def create_daily_log(self, log_data):
        if self.daily_logs is None:
            return None
        
        log_data['created_at'] = datetime.utcnow()
        result = self.daily_logs.insert_one(log_data)
        log_data['_id'] = str(result.inserted_id)
        return log_data
    
    def get_logs_by_trip(self, trip_id):
        if self.daily_logs is None:
            return []
        
        logs = list(self.daily_logs.find({'trip_id': trip_id}).sort('date', -1))
        for log in logs:
            log['_id'] = str(log['_id'])
        return logs
    
    def get_all_logs(self, limit=50, skip=0):
        if self.daily_logs is None:
            return []
        
        logs = list(self.daily_logs.find().sort('created_at', -1).skip(skip).limit(limit))
        for log in logs:
            log['_id'] = str(log['_id'])
        return logs

# Global instance
mongodb_manager = MongoDBManager()