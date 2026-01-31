# SETUP GUIDE - PAYMONGO PAYMENT INTEGRATION

## Quick Setup (5 Minutes)

### 1. Install Dependencies
```bash
cd flask_app
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python init_db.py
```

This creates all tables including:
- User
- Movie, Cinema, Showtime, MovieBooking
- BusRoute, BusSchedule, BusBooking
- **Transaction (NEW)**

### 3. Verify .env Configuration
Check that `/flask_app/.env` contains:
```
PAYMONGO_SECRET_KEY=sk_test_boUkkKYfbPnRVZMrVE13moQo
PAYMONGO_PUBLIC_KEY=pk_test_PA4RzhxD9BadaUFoTkaaTLbf
```

### 4. Run Application
```bash
python run.py
```

Visit: `http://localhost:5000`

---

## File Structure

```
flask_app/
├── app.py                          # Main Flask app with Transaction model
├── config.py                       # PayMongo configuration
├── requirements.txt                # Updated with requests, removed stripe
├── .env                            # Environment variables
├── init_db.py                      # Database initialization script
├── templates/
│   ├── payment/
│   │   ├── checkout.html          # PayMongo e-wallet payment page
│   │   └── success.html           # Receipt page
│   └── admin/
│       ├── transactions.html      # Admin transaction list
│       └── transaction_details.html # Transaction details
└── run.py                          # Application entry point
```

---

## What's New

### Transaction Model (app.py: lines 192-225)
Tracks all payment transactions with:
- Payment details (amount, method, status)
- PayMongo IDs (source_id, payment_id)
- Error tracking (message, code)
- Audit timestamps (created, updated, completed)

### Updated Endpoints
1. **`/create-paymongo-source`** - Creates e-wallet payment source
2. **`/payment-success`** - Handles payment completion & verification

### Payment Tracking
Every payment creates a `Transaction` record:
- Created when payment initiated (status: pending)
- Updated when payment completed (status: completed)
- Tracks all errors and PayMongo details

---

## Testing

### Test Scenario 1: GCash Payment
1. Click "Book Movie" → Select seats → "Checkout"
2. Choose "GCash" payment method
3. Click "Pay Now"
4. Redirected to PayMongo checkout
5. Complete test payment
6. Success page shows receipt
7. Check database: Transaction record status = 'completed'

### Test Scenario 2: PayMaya Payment
Same as GCash but select "PayMaya" option

### Verify Transaction Table
```bash
python
>>> from app import app, Transaction
>>> with app.app_context():
...     transactions = Transaction.query.all()
...     for t in transactions:
...         print(f"{t.transaction_reference} - {t.payment_status}")
```

---

## Admin Dashboard

Access transaction reports at:
- `/admin/transactions` - List all transactions
- `/admin/transactions/<id>` - View transaction details

Features:
- Filter by status, date, payment method
- View error details for failed transactions
- Export transaction reports
- Real-time statistics

---

## Troubleshooting

### Issue: "Database is locked"
**Solution:** Delete `ticketing.db` and run `python init_db.py` again

### Issue: PayMongo API errors
**Solution:** 
1. Verify API keys in .env
2. Check network connection
3. Review error_message in Transaction record

### Issue: Payment not updating
**Solution:**
1. Check transaction status in database
2. Verify redirect URL is correct
3. Check PayMongo webhook settings

---

## Database Schema

### Transaction Table

| Column | Type | Example |
|--------|------|---------|
| id | Integer | 1 |
| user_id | Integer | 5 |
| booking_type | String | 'movie' |
| booking_id | Integer | 12 |
| amount | Float | 599.00 |
| currency | String | 'PHP' |
| payment_method | String | 'gcash' |
| payment_status | String | 'completed' |
| paymongo_source_id | String | 'src_...' |
| paymongo_payment_id | String | 'pay_...' |
| transaction_reference | String | 'TXN-movie-12-1704067200' |
| error_message | Text | NULL or error text |
| error_code | String | NULL or error code |
| created_at | DateTime | 2024-01-01 10:00:00 |
| updated_at | DateTime | 2024-01-01 10:05:00 |
| completed_at | DateTime | 2024-01-01 10:05:00 |

---

## Environment Variables

### Required
- `PAYMONGO_SECRET_KEY` - PayMongo API secret
- `PAYMONGO_PUBLIC_KEY` - PayMongo API public key

### Recommended
- `SECRET_KEY` - Change in production
- `FLASK_ENV` - Set to 'production' in production
- `DEBUG` - Set to False in production

### Optional
- `MAIL_SERVER` - For email notifications
- `MAIL_USERNAME` - Email sender
- `MAIL_PASSWORD` - Email password

---

## Common Tasks

### Query All Transactions for User
```python
user_id = 5
transactions = Transaction.query.filter_by(user_id=user_id).all()
```

### Query Completed Transactions
```python
completed = Transaction.query.filter_by(payment_status='completed').all()
```

### Query Failed Transactions with Errors
```python
failed = Transaction.query.filter(
    Transaction.payment_status == 'failed'
).filter(
    Transaction.error_message.isnot(None)
).all()
```

### Calculate Total Revenue
```python
from sqlalchemy import func
total = db.session.query(
    func.sum(Transaction.amount)
).filter_by(payment_status='completed').scalar()
```

---

## Production Deployment

Before going live:

1. Change `SECRET_KEY` in .env
2. Set `DEBUG=False` in .env
3. Set `FLASK_ENV=production` in .env
4. Use PostgreSQL instead of SQLite:
   ```
   SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost/ticketdb
   ```
5. Enable HTTPS/SSL
6. Set up backup strategy for database
7. Monitor transaction logs regularly
8. Set up error alerts

---

## Support

For issues or questions:
1. Check `/flask_app/TROUBLESHOOTING.md`
2. Review transaction error messages in database
3. Check PayMongo API documentation
4. Review application logs

---

## Next Steps

1. Test all payment flows
2. Set up admin dashboard
3. Configure email notifications
4. Set up database backups
5. Monitor transactions in production
