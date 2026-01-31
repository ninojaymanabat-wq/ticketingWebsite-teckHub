# COMPLETE UPDATED CODE REFERENCE

## 1. TRANSACTION MODEL (app.py)

```python
class Transaction(db.Model):
    """Transaction table to track all payment transactions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    booking_type = db.Column(db.String(20), nullable=False)  # 'movie' or 'bus'
    booking_id = db.Column(db.Integer, nullable=False)  # Reference to MovieBooking or BusBooking
    
    # Payment details
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='PHP')
    payment_method = db.Column(db.String(50), nullable=False)  # 'gcash', 'paymaya', 'bank', etc.
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed, cancelled
    
    # PayMongo details
    paymongo_source_id = db.Column(db.String(255), unique=True)
    paymongo_payment_id = db.Column(db.String(255))
    
    # Transaction reference
    transaction_reference = db.Column(db.String(50), unique=True)
    
    # Error tracking
    error_message = db.Column(db.Text)
    error_code = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # User relationship for queries
    user = db.relationship('User', backref='transactions')
    
    def __repr__(self):
        return f'<Transaction {self.transaction_reference} - {self.payment_status}>'
```

---

## 2. CREATE PAYMONGO SOURCE ENDPOINT (app.py)

```python
@app.route('/create-paymongo-source', methods=['POST'])
@login_required
def create_paymongo_source():
    """Create a PayMongo source for e-wallet payment"""
    data = request.get_json()
    booking_type = data.get('booking_type')
    booking_id = data.get('booking_id')
    payment_method = data.get('payment_method', 'gcash')  # gcash, paymaya, etc.

    if booking_type == 'movie':
        booking = MovieBooking.query.get_or_404(booking_id)
    else:
        booking = BusBooking.query.get_or_404(booking_id)

    try:
        # Create PayMongo source for e-wallet
        auth_string = base64.b64encode(f'{PAYMONGO_SECRET_KEY}:'.encode()).decode()
        headers = {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/json'
        }
        
        # Map payment methods to PayMongo types
        source_types = {
            'gcash': 'gcash',
            'paymaya': 'paymaya'
        }
        
        source_type = source_types.get(payment_method, 'gcash')
        
        payload = {
            'data': {
                'attributes': {
                    'amount': int(booking.total_amount * 100),  # in cents
                    'currency': 'PHP',
                    'type': source_type,
                    'redirect': {
                        'success': url_for('payment_success', booking_type=booking_type, booking_id=booking_id, _external=True),
                        'failed': url_for('payment', booking_type=booking_type, booking_id=booking_id, _external=True)
                    }
                }
            }
        }
        
        response = requests.post(f'{PAYMONGO_API_URL}/sources', json=payload, headers=headers)
        
        if response.status_code != 201:
            # Create error transaction record
            trans_ref = f"TXN-{booking_type}-{booking_id}-{int(datetime.utcnow().timestamp())}"
            error_transaction = Transaction(
                user_id=current_user.id,
                booking_type=booking_type,
                booking_id=booking_id,
                amount=booking.total_amount,
                payment_method=payment_method,
                payment_status='failed',
                transaction_reference=trans_ref,
                error_message='Failed to create payment source',
                error_code=str(response.status_code)
            )
            db.session.add(error_transaction)
            db.session.commit()
            return jsonify({'error': 'Failed to create payment source'}), 400
        
        source_data = response.json()['data']
        source_id = source_data['id']
        
        # Store payment reference in booking
        booking.payment_method = payment_method
        booking.payment_reference = source_id
        
        # Create pending transaction record
        trans_ref = f"TXN-{booking_type}-{booking_id}-{int(datetime.utcnow().timestamp())}"
        transaction = Transaction(
            user_id=current_user.id,
            booking_type=booking_type,
            booking_id=booking_id,
            amount=booking.total_amount,
            currency='PHP',
            payment_method=payment_method,
            payment_status='pending',
            paymongo_source_id=source_id,
            transaction_reference=trans_ref
        )
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'sourceId': source_id,
            'redirectUrl': source_data['attributes']['redirect']['checkout_url']
        })
        
    except Exception as e:
        # Create error transaction record
        trans_ref = f"TXN-{booking_type}-{booking_id}-{int(datetime.utcnow().timestamp())}"
        error_transaction = Transaction(
            user_id=current_user.id,
            booking_type=booking_type,
            booking_id=booking_id,
            amount=booking.total_amount,
            payment_method=payment_method,
            payment_status='failed',
            transaction_reference=trans_ref,
            error_message=str(e)
        )
        db.session.add(error_transaction)
        db.session.commit()
        return jsonify({'error': str(e)}), 400
```

---

## 3. PAYMENT SUCCESS ENDPOINT (app.py)

```python
@app.route('/payment-success/<booking_type>/<int:booking_id>')
@login_required
def payment_success(booking_type, booking_id):
    source_id = request.args.get('source_id')
    
    if booking_type == 'movie':
        booking = MovieBooking.query.get_or_404(booking_id)
    else:
        booking = BusBooking.query.get_or_404(booking_id)
    
    # Find or update the transaction record
    transaction = Transaction.query.filter_by(paymongo_source_id=source_id).first() if source_id else None
    
    # Verify payment with PayMongo if source_id is provided
    if source_id:
        try:
            auth_string = base64.b64encode(f'{PAYMONGO_SECRET_KEY}:'.encode()).decode()
            headers = {
                'Authorization': f'Basic {auth_string}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f'{PAYMONGO_API_URL}/sources/{source_id}', headers=headers)
            
            if response.status_code == 200:
                source_data = response.json()['data']
                if source_data['attributes']['status'] == 'chargeable':
                    booking.payment_status = 'completed'
                    if transaction:
                        transaction.payment_status = 'completed'
                        transaction.completed_at = datetime.utcnow()
                        transaction.paymongo_payment_id = source_data.get('id')
                else:
                    booking.payment_status = 'pending'
                    if transaction:
                        transaction.payment_status = 'pending'
            else:
                booking.payment_status = 'pending'
                if transaction:
                    transaction.payment_status = 'pending'
                    transaction.error_code = str(response.status_code)
        except Exception as e:
            booking.payment_status = 'pending'
            if transaction:
                transaction.payment_status = 'pending'
                transaction.error_message = str(e)
    else:
        booking.payment_status = 'completed'
        if transaction:
            transaction.payment_status = 'completed'
            transaction.completed_at = datetime.utcnow()
    
    # Update available seats only if payment is completed
    if booking.payment_status == 'completed':
        if booking_type == 'movie':
            showtime = booking.showtime
            showtime.available_seats -= booking.num_tickets
        else:
            schedule = booking.schedule
            schedule.available_seats -= booking.num_tickets
    
    db.session.commit()
    
    return render_template('payment/success.html', booking=booking, booking_type=booking_type)
```

---

## 4. .ENV CONFIGURATION FILE

```
# ==================== PAYMONGO E-WALLET PAYMENT CONFIGURATION ====================
PAYMONGO_SECRET_KEY=sk_test_boUkkKYfbPnRVZMrVE13moQo
PAYMONGO_PUBLIC_KEY=pk_test_PA4RzhxD9BadaUFoTkaaTLbf

# ==================== FLASK CONFIGURATION ====================
SECRET_KEY=your-secret-key-change-in-production
FLASK_ENV=development
DEBUG=False

# ==================== DATABASE CONFIGURATION ====================
# Database URI - SQLite for development, PostgreSQL for production
SQLALCHEMY_DATABASE_URI=sqlite:///ticketing.db
SQLALCHEMY_TRACK_MODIFICATIONS=False

# ==================== GOOGLE AI CONFIGURATION ====================
# Get your API key from: https://ai.google.dev/
GOOGLE_API_KEY=AIzaSyBDlPAFKwK7D3x7g99r0emxNjbqm1m1INY

# ==================== EMAIL CONFIGURATION ====================
# Gmail SMTP Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Default sender for system emails
MAIL_DEFAULT_SENDER=noreply@tickethub.com

# ==================== APPLICATION SETTINGS ====================
# Maximum file upload size (in bytes) - 16MB
MAX_UPLOAD_SIZE=16777216

# Session timeout (in minutes)
SESSION_TIMEOUT=30

# ==================== PAYMENT SETTINGS ====================
# Payment currency - PHP for Philippine Peso
PAYMENT_CURRENCY=PHP

# Supported payment methods (comma-separated)
SUPPORTED_PAYMENT_METHODS=gcash,paymaya

# ==================== TRANSACTION SETTINGS ====================
# Transaction reference prefix
TRANSACTION_PREFIX=TXN

# Transaction expiry time (in hours)
TRANSACTION_EXPIRY_HOURS=24

# ==================== SECURITY SETTINGS ====================
# CORS allowed origins (for production)
CORS_ORIGINS=*

# Password hashing rounds
PASSWORD_HASH_ROUNDS=12

# ==================== DEVELOPMENT SETTINGS ====================
# Set to False in production
TESTING=False
PROPAGATE_EXCEPTIONS=True
```

---

## 5. DATABASE INITIALIZATION SCRIPT (init_db.py)

```python
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
```

---

## 6. REQUIREMENTS.TXT UPDATE

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
Werkzeug==3.0.1
requests==2.31.0
python-dotenv==1.0.0
email-validator==2.1.0
Pillow==10.1.0
google-generativeai==0.3.0
Flask-Mail==0.9.1
```

---

## 7. APP.PY IMPORTS (Updated)

```python
"""
Movie + Bus Ticketing Platform
Flask Application with SQLAlchemy, PayMongo E-Wallet Payments, and Admin Panel
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from functools import wraps
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Mail, Message
import base64
```

---

## 8. PAYMONGO CONFIGURATION (app.py)

```python
# PayMongo configuration
PAYMONGO_SECRET_KEY = os.environ.get('PAYMONGO_SECRET_KEY', 'sk_test_boUkkKYfbPnRVZMrVE13moQo')
PAYMONGO_PUBLIC_KEY = os.environ.get('PAYMONGO_PUBLIC_KEY', 'pk_test_PA4RzhxD9BadaUFoTkaaTLbf')
PAYMONGO_API_URL = 'https://api.paymongo.com/v1'
```

---

## INSTALLATION & SETUP INSTRUCTIONS

### Step 1: Update Requirements
```bash
cd flask_app
pip install -r requirements.txt
```

### Step 2: Initialize Database
```bash
python init_db.py
```

### Step 3: Configure Environment
Ensure your `.env` file has the PayMongo keys configured:
- `PAYMONGO_SECRET_KEY=sk_test_boUkkKYfbPnRVZMrVE13moQo`
- `PAYMONGO_PUBLIC_KEY=pk_test_PA4RzhxD9BadaUFoTkaaTLbf`

### Step 4: Run Application
```bash
python run.py
```

---

## TRANSACTION TABLE COLUMNS

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| user_id | Integer | Foreign Key to User |
| booking_type | String | 'movie' or 'bus' |
| booking_id | Integer | Reference to booking |
| amount | Float | Payment amount |
| currency | String | Default: 'PHP' |
| payment_method | String | 'gcash', 'paymaya' |
| payment_status | String | pending/completed/failed/cancelled |
| paymongo_source_id | String | Unique PayMongo ID |
| paymongo_payment_id | String | PayMongo payment ID |
| transaction_reference | String | Unique transaction ref |
| error_message | Text | Error details |
| error_code | String | Error code |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| completed_at | DateTime | Payment completion time |

---

## PAYMENT FLOW

1. User clicks "Pay Now" on booking page
2. Frontend calls `/create-paymongo-source` endpoint
3. Backend creates Transaction record (status: pending)
4. PayMongo source created, returns redirect URL
5. User redirected to PayMongo e-wallet page
6. User completes payment (GCash or PayMaya)
7. User redirected to `/payment-success` endpoint
8. Backend verifies payment with PayMongo
9. Transaction record updated (status: completed/failed)
10. Receipt displayed to user

---

## KEY FEATURES

✓ Complete Transaction Audit Trail
✓ Real-time Payment Status Tracking
✓ Error Logging & Recovery
✓ Multiple E-Wallet Support (GCash, PayMaya)
✓ Automatic Seat Availability Updates
✓ User-Friendly Payment Interface
✓ Professional Receipt Generation
✓ Admin Dashboard for Transaction Monitoring
