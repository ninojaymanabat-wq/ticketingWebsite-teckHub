#!/usr/bin/env python
"""
Database Initialization Script
This script creates all database tables including the new Transaction table
Run this after adding new models to the app
"""

import os
import sys
from app import app, db, User, Movie, Cinema, Showtime, MovieBooking, BusRoute, BusSchedule, BusBooking, Transaction

def init_database():
    """Initialize the database and create all tables"""
    with app.app_context():
        print("Creating database tables...")
        
        # Create all tables
        db.create_all()
        
        print("✓ Database initialized successfully!")
        print("\nTables created:")
        print("  - User")
        print("  - Movie")
        print("  - Cinema")
        print("  - Showtime")
        print("  - MovieBooking")
        print("  - BusRoute")
        print("  - BusSchedule")
        print("  - BusBooking")
        print("  - Transaction (NEW)")
        
        print("\n" + "="*60)
        print("Database Setup Complete!")
        print("="*60)
        print("\nTransaction Table Schema:")
        print("  - id (Integer, Primary Key)")
        print("  - user_id (Integer, Foreign Key -> User)")
        print("  - booking_type (String) - 'movie' or 'bus'")
        print("  - booking_id (Integer) - Reference to booking")
        print("  - amount (Float) - Payment amount")
        print("  - currency (String) - Currency code (default: PHP)")
        print("  - payment_method (String) - Payment method used")
        print("  - payment_status (String) - pending/completed/failed/cancelled")
        print("  - paymongo_source_id (String) - PayMongo source ID")
        print("  - paymongo_payment_id (String) - PayMongo payment ID")
        print("  - transaction_reference (String) - Unique transaction reference")
        print("  - error_message (Text) - Error details if transaction failed")
        print("  - error_code (String) - Error code from PayMongo")
        print("  - created_at (DateTime)")
        print("  - updated_at (DateTime)")
        print("  - completed_at (DateTime)")

def drop_tables():
    """Drop all tables (use with caution)"""
    response = input("\n⚠️  WARNING: This will delete all data in the database!\nAre you sure? (type 'yes' to confirm): ")
    if response.lower() == 'yes':
        with app.app_context():
            print("Dropping all tables...")
            db.drop_all()
            print("✓ All tables dropped successfully!")
    else:
        print("Operation cancelled.")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'drop':
        drop_tables()
    else:
        init_database()
