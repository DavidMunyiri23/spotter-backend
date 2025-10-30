#!/usr/bin/env python
"""Test MongoDB connection directly"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hos_api.settings')

import django
django.setup()

from trips.mongodb_manager import mongodb_manager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    print("🔍 Direct MongoDB Connection Test")
    print("=" * 50)
    
    # Show environment variables
    username = os.getenv('MONGO_USERNAME', 'NOT_SET')
    password = os.getenv('MONGO_PASSWORD', 'NOT_SET')
    
    print(f"📋 Environment Variables:")
    print(f"   MONGO_USERNAME: {username}")
    print(f"   MONGO_PASSWORD: {'*' * len(password) if password != 'NOT_SET' else 'NOT_SET'}")
    print()
    
    # Show the connection string being used
    from pymongo import MongoClient
    connection_string = f'mongodb+srv://{username}:{password}@spotterai.filnzzr.mongodb.net/?appName=spotterai'
    print(f"🔗 Connection String: mongodb+srv://{username}:***@spotterai.filnzzr.mongodb.net/?appName=spotterai")
    print()
    
    # Test direct connection
    try:
        print("🔄 Testing direct connection...")
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        
        # Test connection
        client.admin.command('ping')
        print("✅ Direct connection successful!")
        
        # Test database access
        db = client['hos_tracker_db']
        collections = db.list_collection_names()
        print(f"📚 Available collections: {collections}")
        
        # Test a simple operation
        test_collection = db['test_connection']
        test_doc = {'test': 'connection', 'timestamp': 'now'}
        result = test_collection.insert_one(test_doc)
        print(f"✅ Test document inserted with ID: {result.inserted_id}")
        
        # Clean up test document
        test_collection.delete_one({'_id': result.inserted_id})
        print("✅ Test document cleaned up")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    print("=" * 50)

if __name__ == "__main__":
    test_connection()