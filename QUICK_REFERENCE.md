# Quick Reference: Transaction Table & .env Setup

## ⚡ TL;DR - Get Started in 3 Steps

### Step 1: Initialize Database
```bash
cd flask_app
python init_db.py
```

### Step 2: Verify .env Configuration
Check that `flask_app/.env` contains:
```env
PAYMONGO_SECRET_KEY=sk_test_boUkkKYfbPnRVZMrVE13moQo
PAYMONGO_PUBLIC_KEY=pk_test_PA4RzhxD9BadaUFoTkaaTLbf
```

### Step 3: Run Application
```bash
python run.py
```

---

## 📊 Transaction Table Overview

### Quick Stats
- **Table Name:** `transaction`
- **Total Columns:** 14
- **Primary Key:** `id`
- **Foreign Keys:** `user_id`
- **Unique Fields:** `transaction_reference`, `paymongo_source_id`

### Column Quick Reference

| Column | Type | Purpose |
|--------|------|---------|
| `id` | INT | Primary key |
| `user_id` | INT | Who made the payment |
| `booking_type` | STR | movie or bus |
| `booking_id` | INT | Which booking |
| `amount` | FLOAT | Payment amount |
| `currency` | STR | Always PHP |
| `payment_method` | STR | gcash or paymaya |
| `payment_status` | STR | pending/completed/failed |
| `paymongo_source_id` | STR | PayMongo reference |
| `paymongo_payment_id` | STR | PayMongo payment ID |
| `transaction_reference` | STR | TXN-* unique reference |
| `error_message` | TEXT | If failed, why |
| `error_code` | STR | PayMongo error code |
| `created_at` | DT | When created |

---

## 🔧 .env Configuration

### Required (Must Have)
```env
PAYMONGO_SECRET_KEY=sk_test_boUkkKYfbPnRVZMrVE13moQo
PAYMONGO_PUBLIC_KEY=pk_test_PA4RzhxD9BadaUFoTkaaTLbf
SECRET_KEY=your-secret-key-change-in-production
```

### Optional (Nice to Have)
```env
GOOGLE_API_KEY=your-google-api-key
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Environment Variables
```env
FLASK_ENV=development
DEBUG=False (change to True for debugging)
PAYMENT_CURRENCY=PHP
```

---

## 📱 Transaction Statuses

| Status | Meaning | Color |
|--------|---------|-------|
| pending | Waiting for user to complete payment | 🟡 Yellow |
| completed | Payment successful | 🟢 Green |
| failed | Payment failed or error occurred | 🔴 Red |
| cancelled | User cancelled payment | ⚪ Gray |

---

## 💳 Payment Methods

### Supported
- **gcash** - GCash (Philippine e-wallet)
- **paymaya** - PayMaya (Digital wallet)

### Not Supported (Removed)
- ~~Stripe card payments~~ (Replaced with e-wallet only)
- ~~Bank transfer~~ (Not available with PayMongo)

---

## 📊 Admin Dashboard Access

### View Transactions
1. Login as admin
2. Go to **Dashboard** → **Transactions**
3. See all transactions with stats

### Features
- ✓ Filter by status
- ✓ Filter by payment method
- ✓ Filter by date range
- ✓ View transaction details
- ✓ Statistics (total, completed, pending, failed)

---

## 🔍 Useful Queries

### Get all completed transactions
```python
completed = Transaction.query.filter_by(payment_status='completed').all()
```

### Calculate total revenue
```python
from sqlalchemy import func
total = db.session.query(func.sum(Transaction.amount))\
    .filter_by(payment_status='completed').scalar()
```

### Get user's transactions
```python
user_txns = Transaction.query.filter_by(user_id=user_id).all()
```

### Get transactions for today
```python
from datetime import datetime, date
today_txns = Transaction.query.filter(
    Transaction.created_at >= date.today()
).all()
```

---

## 🚀 Payment Flow

```
User Initiates Payment
         ↓
Payment Creation Endpoint
  ├─ Creates Transaction (pending)
  ├─ Calls PayMongo API
  └─ Returns checkout URL
         ↓
User Goes to PayMongo Checkout
         ↓
User Completes E-wallet Payment
         ↓
Success Callback to Your App
  ├─ Verifies with PayMongo
  ├─ Updates Transaction (completed)
  ├─ Updates Booking (completed)
  └─ Updates Seat Availability
         ↓
Receipt Displayed
```

---

## 📁 New/Modified Files

### Created
- ✨ `flask_app/init_db.py` - Database initialization
- ✨ `flask_app/templates/admin/transactions.html` - Transaction dashboard
- ✨ `flask_app/templates/admin/transaction_details.html` - Transaction details
- ✨ `flask_app/DATABASE_SETUP.md` - Database documentation
- ✨ `TRANSACTION_TABLE_IMPLEMENTATION.md` - Implementation guide

### Modified
- 📝 `flask_app/app.py` - Added Transaction model & updated endpoints
- 📝 `flask_app/.env` - Added comprehensive configuration
- 📝 `flask_app/requirements.txt` - Updated dependencies

---

## ⚠️ Important Changes from Previous Version

### Removed
- ❌ Stripe card payments
- ❌ Bank transfer option
- ❌ `@app.route('/payment-bank-pending')`
- ❌ `stripe` import and configuration

### Added
- ✅ Transaction table with full audit trail
- ✅ Transaction history dashboard
- ✅ PayMongo e-wallet integration
- ✅ Error tracking and logging
- ✅ Payment verification system

---

## 🔒 Security Reminders

1. **Never commit .env file** - Add to `.gitignore`
2. **Protect API keys** - Use environment variables
3. **Validate all inputs** - Don't trust user data
4. **Use HTTPS in production** - Secure all payments
5. **Regular backups** - Backup database frequently
6. **Monitor transactions** - Watch for suspicious activity

---

## 🐛 Common Issues & Fixes

### "Table transaction doesn't exist"
**Solution:** Run `python init_db.py`

### "PAYMONGO_SECRET_KEY not set"
**Solution:** Check `.env` file exists and contains the key

### "ImportError: cannot import name Transaction"
**Solution:** Make sure app.py has been updated with Transaction model

### "Payment fails with no error message"
**Solution:** Check PayMongo API credentials in .env

### "Database is locked"
**Solution:** Close all other connections and try again

---

## 📞 Support Resources

| Resource | Location |
|----------|----------|
| Database Setup Guide | `flask_app/DATABASE_SETUP.md` |
| PayMongo Setup Guide | `flask_app/PAYMONGO_SETUP.md` |
| Troubleshooting Guide | `flask_app/TROUBLESHOOTING.md` |
| Full Implementation | `TRANSACTION_TABLE_IMPLEMENTATION.md` |
| API Reference | `flask_app/API_REFERENCE.md` |

---

## ✅ Verification Checklist

- [ ] Ran `python init_db.py`
- [ ] Verified `.env` contains PayMongo keys
- [ ] Can see transactions table in database
- [ ] Can access admin transactions dashboard
- [ ] Can view transaction details
- [ ] Payment flow works end-to-end
- [ ] Transactions are being logged
- [ ] Can filter transactions by status
- [ ] Can filter transactions by date

---

## 🎯 Next Steps

1. ✓ Initialize database with transaction table
2. ✓ Test the payment flow
3. ✓ Monitor transactions in admin dashboard
4. ✓ Set up automated backups
5. ✓ Deploy to production when ready

---

**You're all set! The transaction table is ready to track all your PayMongo payments.**

For more details, see the full documentation in `TRANSACTION_TABLE_IMPLEMENTATION.md`
