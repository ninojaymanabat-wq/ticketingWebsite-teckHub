# Database Schema Reference

## Transaction Table - Complete Schema

### SQL Definition
```sql
CREATE TABLE transaction (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    booking_type VARCHAR(20) NOT NULL,
    booking_id INTEGER NOT NULL,
    amount FLOAT NOT NULL,
    currency VARCHAR(10) DEFAULT 'PHP',
    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending',
    paymongo_source_id VARCHAR(255),
    paymongo_payment_id VARCHAR(255),
    transaction_reference VARCHAR(50),
    error_message TEXT,
    error_code VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES user(id),
    UNIQUE (paymongo_source_id),
    UNIQUE (transaction_reference)
);
```

### Column Definitions

| # | Column Name | Type | Size | Constraints | Description |
|---|-------------|------|------|-------------|-------------|
| 1 | `id` | INTEGER | - | PRIMARY KEY, AUTOINCREMENT | Unique transaction identifier |
| 2 | `user_id` | INTEGER | - | NOT NULL, FOREIGN KEY | Reference to User table |
| 3 | `booking_type` | VARCHAR | 20 | NOT NULL | Type: 'movie' or 'bus' |
| 4 | `booking_id` | INTEGER | - | NOT NULL | Reference to booking (MovieBooking or BusBooking) |
| 5 | `amount` | FLOAT | - | NOT NULL | Payment amount in PHP |
| 6 | `currency` | VARCHAR | 10 | DEFAULT 'PHP' | Currency code (ISO 4217) |
| 7 | `payment_method` | VARCHAR | 50 | NOT NULL | Method: 'gcash', 'paymaya' |
| 8 | `payment_status` | VARCHAR | 20 | DEFAULT 'pending' | Status: pending/completed/failed/cancelled |
| 9 | `paymongo_source_id` | VARCHAR | 255 | UNIQUE | PayMongo source/payment source ID |
| 10 | `paymongo_payment_id` | VARCHAR | 255 | - | PayMongo payment ID after processing |
| 11 | `transaction_reference` | VARCHAR | 50 | UNIQUE | TXN-{type}-{id}-{timestamp} format |
| 12 | `error_message` | TEXT | - | - | Error details if transaction failed |
| 13 | `error_code` | VARCHAR | 50 | - | Error code from PayMongo API |
| 14 | `created_at` | DATETIME | - | DEFAULT NOW | When transaction was created |
| 15 | `updated_at` | DATETIME | - | DEFAULT NOW | When transaction was last updated |
| 16 | `completed_at` | DATETIME | - | NULLABLE | When payment was completed |

### Indexes
```sql
CREATE INDEX idx_user_id ON transaction(user_id);
CREATE INDEX idx_booking_type ON transaction(booking_type);
CREATE INDEX idx_payment_status ON transaction(payment_status);
CREATE INDEX idx_created_at ON transaction(created_at);
CREATE INDEX idx_payment_method ON transaction(payment_method);
CREATE UNIQUE INDEX idx_transaction_reference ON transaction(transaction_reference);
CREATE UNIQUE INDEX idx_paymongo_source_id ON transaction(paymongo_source_id);
```

---

## Data Types Reference

### VARCHAR(size)
- Used for: Variable-length text
- Examples: payment_method, currency, booking_type
- Maximum size specified in parentheses

### INTEGER
- Used for: Whole numbers
- Examples: id, user_id, booking_id, amount (in cents)
- Range: -2,147,483,648 to 2,147,483,647

### FLOAT
- Used for: Decimal numbers
- Examples: amount (in PHP)
- Supports: 6-7 significant digits

### TEXT
- Used for: Large text fields
- Examples: error_message
- Maximum: 1,000,000,000 bytes in SQLite

### DATETIME
- Used for: Date and time
- Format: YYYY-MM-DD HH:MM:SS
- Stored as: TEXT in SQLite

---

## Relationships

### Transaction → User
```
transaction.user_id → user.id (Foreign Key)
```
- One user can have many transactions
- Every transaction must belong to a user
- User deletion cascades to transactions

### Transaction → Booking
```
transaction.booking_id → (moviebooking.id OR busbooking.id)
booking_type indicates which table to reference
```
- Transaction references either MovieBooking or BusBooking
- No direct foreign key (handled in application logic)
- Booking must exist before transaction

---

## Sample Data

### Example Transaction - Completed
```json
{
  "id": 1,
  "user_id": 5,
  "booking_type": "movie",
  "booking_id": 42,
  "amount": 250.00,
  "currency": "PHP",
  "payment_method": "gcash",
  "payment_status": "completed",
  "paymongo_source_id": "src_test_abc123def456",
  "paymongo_payment_id": "pay_test_xyz789",
  "transaction_reference": "TXN-movie-42-1698765432",
  "error_message": null,
  "error_code": null,
  "created_at": "2024-01-15 10:30:45",
  "updated_at": "2024-01-15 10:35:20",
  "completed_at": "2024-01-15 10:35:15"
}
```

### Example Transaction - Failed
```json
{
  "id": 2,
  "user_id": 8,
  "booking_type": "bus",
  "booking_id": 15,
  "amount": 500.00,
  "currency": "PHP",
  "payment_method": "paymaya",
  "payment_status": "failed",
  "paymongo_source_id": "src_test_def789ghi012",
  "paymongo_payment_id": null,
  "transaction_reference": "TXN-bus-15-1698765600",
  "error_message": "Insufficient funds in wallet",
  "error_code": "payment_declined",
  "created_at": "2024-01-15 11:20:30",
  "updated_at": "2024-01-15 11:25:45",
  "completed_at": null
}
```

---

## Related Tables

### User Table
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### MovieBooking Table
```sql
CREATE TABLE movie_booking (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    showtime_id INTEGER NOT NULL,
    num_tickets INTEGER NOT NULL,
    seat_numbers VARCHAR(200),
    total_amount FLOAT NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(20),
    payment_reference VARCHAR(255),
    booking_reference VARCHAR(20) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (showtime_id) REFERENCES showtime(id)
);
```

### BusBooking Table
```sql
CREATE TABLE bus_booking (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    schedule_id INTEGER NOT NULL,
    num_tickets INTEGER NOT NULL,
    seat_numbers VARCHAR(200),
    passenger_names TEXT,
    total_amount FLOAT NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(20),
    payment_reference VARCHAR(255),
    booking_reference VARCHAR(20) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (schedule_id) REFERENCES bus_schedule(id)
);
```

---

## Transaction Status Workflow

```
START
  ↓
CREATE (status: pending)
  ├─ Transaction created
  ├─ PayMongo source ID stored
  └─ Awaiting user action
  ↓
PROCESS
  ├─ User goes to PayMongo checkout
  └─ User completes e-wallet payment
  ↓
VERIFY
  ├─ System calls PayMongo API
  ├─ Checks payment status
  └─ Updates transaction
  ↓
COMPLETED (status: completed)
  ├─ Payment confirmed
  ├─ Booking confirmed
  └─ Seats updated
  ↓
  OR
  ↓
FAILED (status: failed)
  ├─ Payment declined
  ├─ Error logged
  └─ Booking remains pending
  ↓
END
```

---

## Query Examples

### Get All Transactions
```sql
SELECT * FROM transaction ORDER BY created_at DESC;
```

### Get Transactions for Specific User
```sql
SELECT * FROM transaction WHERE user_id = ? ORDER BY created_at DESC;
```

### Get Completed Transactions
```sql
SELECT * FROM transaction 
WHERE payment_status = 'completed' 
ORDER BY completed_at DESC;
```

### Get Failed Transactions
```sql
SELECT * FROM transaction 
WHERE payment_status = 'failed' 
ORDER BY created_at DESC;
```

### Get Pending Transactions
```sql
SELECT * FROM transaction 
WHERE payment_status = 'pending' 
ORDER BY created_at DESC;
```

### Calculate Total Revenue
```sql
SELECT SUM(amount) as total_revenue 
FROM transaction 
WHERE payment_status = 'completed';
```

### Revenue by Payment Method
```sql
SELECT payment_method, SUM(amount) as total, COUNT(*) as count
FROM transaction 
WHERE payment_status = 'completed' 
GROUP BY payment_method;
```

### Revenue by Booking Type
```sql
SELECT booking_type, SUM(amount) as total, COUNT(*) as count
FROM transaction 
WHERE payment_status = 'completed' 
GROUP BY booking_type;
```

### Daily Revenue
```sql
SELECT DATE(created_at) as date, SUM(amount) as daily_total, COUNT(*) as count
FROM transaction 
WHERE payment_status = 'completed' 
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Failed Transactions with Errors
```sql
SELECT transaction_reference, error_code, error_message, created_at
FROM transaction 
WHERE payment_status = 'failed' 
ORDER BY created_at DESC;
```

### Transaction Statistics
```sql
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN payment_status = 'completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN payment_status = 'pending' THEN 1 ELSE 0 END) as pending,
    SUM(CASE WHEN payment_status = 'failed' THEN 1 ELSE 0 END) as failed,
    SUM(CASE WHEN payment_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
FROM transaction;
```

### Top Users by Transaction Amount
```sql
SELECT user_id, COUNT(*) as transaction_count, SUM(amount) as total_spent
FROM transaction 
WHERE payment_status = 'completed' 
GROUP BY user_id
ORDER BY total_spent DESC 
LIMIT 10;
```

---

## Default Values

| Column | Default Value | Notes |
|--------|---------------|-------|
| `currency` | 'PHP' | Philippine Peso |
| `payment_status` | 'pending' | Initial status |
| `created_at` | CURRENT_TIMESTAMP | Server time on creation |
| `updated_at` | CURRENT_TIMESTAMP | Server time on creation |
| `completed_at` | NULL | Only set when payment completes |

---

## Constraints

### Primary Key
- Column: `id`
- Auto-increments starting from 1
- Ensures unique transaction identification

### Foreign Key
- Column: `user_id`
- References: `user(id)`
- Ensures referential integrity

### Unique Constraints
- `paymongo_source_id` - PayMongo source must be unique
- `transaction_reference` - Transaction reference must be unique

### Not Null
- `user_id` - Every transaction must have a user
- `booking_type` - Must specify movie or bus
- `booking_id` - Must reference a booking
- `amount` - Amount must be specified
- `payment_method` - Payment method is required

---

## Performance Considerations

### Recommended Indexes (Already Created)
```sql
-- For finding transactions by user
CREATE INDEX idx_user_id ON transaction(user_id);

-- For filtering by status
CREATE INDEX idx_payment_status ON transaction(payment_status);

-- For filtering by method
CREATE INDEX idx_payment_method ON transaction(payment_method);

-- For time-based queries
CREATE INDEX idx_created_at ON transaction(created_at);

-- For booking type filtering
CREATE INDEX idx_booking_type ON transaction(booking_type);
```

### Query Optimization Tips
1. Always filter by `payment_status` when calculating revenue
2. Use `created_at` or `updated_at` for date filtering
3. Combine filters to reduce result set
4. Use `LIMIT` for pagination

---

## Migration Notes

### From SQLite to PostgreSQL
Change data types:
- AUTOINCREMENT → SERIAL
- TEXT (for timestamps) → TIMESTAMP
- Use native DATETIME type

### Backup Before Migration
```bash
# SQLite backup
cp ticketing.db ticketing.db.backup

# Export to SQL
sqlite3 ticketing.db ".dump transaction" > transaction_backup.sql
```

---

## Data Validation Rules

### Payment Method
- Must be one of: 'gcash', 'paymaya'
- Case-sensitive
- Required field

### Booking Type
- Must be one of: 'movie', 'bus'
- Case-sensitive
- Required field

### Payment Status
- Must be one of: 'pending', 'completed', 'failed', 'cancelled'
- Case-sensitive
- Default: 'pending'

### Currency
- Must be valid ISO 4217 code
- Default: 'PHP'
- Recommended to keep as 'PHP'

### Amount
- Must be positive number
- Can include decimals (e.g., 250.50)
- Represents PHP currency

---

**Database Schema Reference Complete!**

For operational documentation, see:
- `DATABASE_SETUP.md` - Database operations
- `TRANSACTION_TABLE_IMPLEMENTATION.md` - Implementation details
- `QUICK_REFERENCE.md` - Quick lookup
