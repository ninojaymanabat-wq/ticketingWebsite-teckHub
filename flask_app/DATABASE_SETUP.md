# Database Setup Guide

## Overview
This guide explains how to set up and manage the database, including the new Transaction table for tracking all PayMongo payments.

## Prerequisites
- Python 3.8+
- Flask installed
- SQLAlchemy installed
- All dependencies from `requirements.txt`

## Initial Setup

### 1. Install Dependencies
```bash
cd flask_app
pip install -r requirements.txt
```

### 2. Initialize Database
The database will be automatically created when you run the Flask app for the first time. However, to manually create all tables including the new Transaction table, run:

```bash
python init_db.py
```

This will create the following tables:
- **User** - User accounts and authentication
- **Movie** - Movie information
- **Cinema** - Cinema locations
- **Showtime** - Movie showtimes
- **MovieBooking** - Movie ticket bookings
- **BusRoute** - Bus routes information
- **BusSchedule** - Bus schedules
- **BusBooking** - Bus ticket bookings
- **Transaction** - Payment transactions (NEW)

## Transaction Table Schema

The Transaction table stores all payment information with the following columns:

### Core Fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key, auto-incremented |
| `user_id` | Integer | Foreign key to User table |
| `booking_type` | String | Type of booking ('movie' or 'bus') |
| `booking_id` | Integer | Reference to the specific booking |

### Payment Information
| Field | Type | Description |
|-------|------|-------------|
| `amount` | Float | Payment amount in PHP |
| `currency` | String | Currency code (default: 'PHP') |
| `payment_method` | String | Payment method used ('gcash', 'paymaya', etc.) |
| `payment_status` | String | Status: 'pending', 'completed', 'failed', 'cancelled' |

### PayMongo Integration
| Field | Type | Description |
|-------|------|-------------|
| `paymongo_source_id` | String | Unique PayMongo source ID |
| `paymongo_payment_id` | String | PayMongo payment ID after processing |
| `transaction_reference` | String | Unique transaction reference (TXN-*) |

### Error Tracking
| Field | Type | Description |
|-------|------|-------------|
| `error_message` | Text | Detailed error message if transaction failed |
| `error_code` | String | Error code from PayMongo API |

### Timestamps
| Field | Type | Description |
|-------|------|-------------|
| `created_at` | DateTime | Transaction creation timestamp |
| `updated_at` | DateTime | Last update timestamp |
| `completed_at` | DateTime | Timestamp when payment was completed |

## Database Operations

### Initialize Fresh Database
```bash
python init_db.py
```

### Drop All Tables (USE WITH CAUTION)
```bash
python init_db.py drop
```
This will prompt for confirmation before deleting all data.

### Access Database Shell (SQLite)
```bash
sqlite3 ticketing.db
```

Common SQLite commands:
```sql
-- List all tables
.tables

-- View Transaction table schema
.schema transaction

-- Count transactions
SELECT COUNT(*) FROM transaction;

-- View all transactions
SELECT * FROM transaction;

-- View completed transactions
SELECT * FROM transaction WHERE payment_status = 'completed';

-- View transactions by payment method
SELECT * FROM transaction WHERE payment_method = 'gcash';

-- View failed transactions
SELECT * FROM transaction WHERE payment_status = 'failed';

-- Calculate total revenue
SELECT SUM(amount) FROM transaction WHERE payment_status = 'completed';
```

## Transaction Lifecycle

### 1. Transaction Created (Pending)
- User initiates payment
- Transaction record is created with status `pending`
- PayMongo source ID is stored

### 2. Payment Processing
- User redirected to PayMongo checkout
- User completes payment on e-wallet

### 3. Payment Verification (Completed)
- System verifies with PayMongo
- If successful: Transaction status → `completed`
- Booking status → `completed`
- Available seats updated

### 4. Error Handling (Failed)
- If verification fails: Transaction status → `failed`
- Error message and code stored
- User redirected to retry payment

## Monitoring Transactions

### View in Admin Dashboard
```
Dashboard → Transactions → View All
```

Features:
- Filter by status (pending, completed, failed)
- Filter by payment method (GCash, PayMaya)
- Filter by date range
- View detailed transaction information
- See payment method statistics

### Programmatic Access (Python)
```python
from app import Transaction, db

# Get all transactions
all_transactions = Transaction.query.all()

# Get completed transactions
completed = Transaction.query.filter_by(payment_status='completed').all()

# Get total revenue
total = db.session.query(db.func.sum(Transaction.amount)).filter_by(payment_status='completed').scalar()

# Get transactions by user
user_txns = Transaction.query.filter_by(user_id=user_id).all()

# Get transactions for specific date
from datetime import datetime, timedelta
today = datetime.utcnow().date()
today_txns = Transaction.query.filter(
    Transaction.created_at >= today,
    Transaction.created_at < today + timedelta(days=1)
).all()
```

## Backup and Restore

### Backup SQLite Database
```bash
# Create backup
cp ticketing.db ticketing.db.backup

# Or use SQLite backup
sqlite3 ticketing.db ".backup ticketing.db.backup"
```

### Restore from Backup
```bash
cp ticketing.db.backup ticketing.db
```

## Performance Optimization

### Add Indexes (for production)
```python
# In app.py, after Transaction model definition
from flask_sqlalchemy import event
from sqlalchemy import Index

@event.listens_for(Transaction.__table__, "after_create")
def add_indexes(target, connection, **kw):
    Index('idx_transaction_user', Transaction.user_id).create(connection)
    Index('idx_transaction_status', Transaction.payment_status).create(connection)
    Index('idx_transaction_method', Transaction.payment_method).create(connection)
    Index('idx_transaction_created', Transaction.created_at).create(connection)
```

## Troubleshooting

### Issue: "Table 'transaction' already exists"
**Solution:** The table already exists. Check your database or use `python init_db.py drop` to start fresh.

### Issue: Foreign key constraint violations
**Solution:** Ensure all user IDs referenced exist in the User table. Check referential integrity.

### Issue: SQLite database locked
**Solution:** Close any other connections to the database and ensure only one process is accessing it.

### Issue: Cannot import Transaction model
**Solution:** Verify `init_db.py` is in the same directory as `app.py` and all dependencies are installed.

## Migration to PostgreSQL (Production)

For production environments, migrate to PostgreSQL:

1. Install PostgreSQL
2. Update `.env`:
   ```
   SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost/ticketing
   ```
3. Install psycopg2:
   ```bash
   pip install psycopg2-binary
   ```
4. Initialize database:
   ```bash
   python init_db.py
   ```

## Support
For issues or questions about the database setup, refer to the main documentation or contact support.
