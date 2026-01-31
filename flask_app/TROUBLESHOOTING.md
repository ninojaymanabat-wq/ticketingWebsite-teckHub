# 🔧 Troubleshooting Guide - PayMongo Payment System

## Quick Diagnosis

If you're experiencing issues, follow these steps:

1. **Check .env file** - Verify PayMongo keys are correct
2. **Check logs** - Look for error messages
3. **Check browser console** - Look for JavaScript errors
4. **Check database** - Verify bookings were created
5. **Check PayMongo dashboard** - Verify transactions

---

## Common Issues & Solutions

### 1. Payment Page Won't Load

**Problem**: `/payment` page shows error or blank page

**Possible Causes:**
- Booking doesn't exist
- User not logged in
- Database issue
- Template file missing

**Solutions:**
```bash
# 1. Verify booking exists
python
>>> from app import app, db, MovieBooking
>>> with app.app_context():
...     booking = MovieBooking.query.get(1)
...     print(booking)

# 2. Check template file exists
ls -la templates/payment/checkout.html

# 3. Check Flask is running with no errors
python run.py
```

**Error Messages to Look For:**
- `TemplateNotFound: payment/checkout.html`
- `404 Not Found`
- `Unauthorized`

---

### 2. "PayMongo Source Creation Failed"

**Problem**: Click "Proceed to Payment" → Error message

**Possible Causes:**
- Invalid API keys
- Network connectivity issue
- PayMongo API down
- Invalid request data

**Solutions:**
```bash
# 1. Verify API keys in .env
cat .env | grep PAYMONGO

# 2. Test API connectivity
curl https://api.paymongo.com/v1/

# 3. Check network connectivity
ping api.paymongo.com

# 4. Verify booking data
python
>>> from app import app, MovieBooking
>>> with app.app_context():
...     b = MovieBooking.query.get(1)
...     print(f"Amount: {b.total_amount}")
...     print(f"Status: {b.payment_status}")
```

**Fix:**
- Verify API keys are correct (no extra spaces)
- Check .env file encoding is UTF-8
- Restart Flask: `python run.py`

---

### 3. Payment Method Buttons Don't Work

**Problem**: Clicking GCash/PayMaya does nothing

**Possible Causes:**
- JavaScript error
- Missing payment section HTML
- Browser cache issue

**Solutions:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for red error messages
4. Copy error and search online

**Common JS Errors:**
- `Cannot read property 'addEventListener' of null`
  - Fix: Refresh page and clear cache
  
- `fetch is not defined`
  - Fix: Use modern browser (Chrome, Firefox, Edge)

- `Unexpected token in JSON`
  - Fix: Check .env file is valid JSON

**Quick Fix:**
```javascript
// In browser console, test if payment works:
proceedToPayment('gcash')
```

---

### 4. Redirected to PayMongo But Payment Fails

**Problem**: Redirected to PayMongo but can't complete payment

**Possible Causes:**
- PayMongo test mode issue
- Browser cookies/cache
- Payment amount issue
- Session timeout

**Solutions:**
1. Try different browser
2. Clear cookies: Settings → Privacy → Clear Cookies
3. Try PayMaya instead of GCash
4. Check if amount is valid (> ₱1.00)

---

### 5. Payment Successful But Booking Not Confirmed

**Problem**: PayMongo says success, but booking still pending

**Possible Causes:**
- Payment status verification failed
- Database transaction failed
- Booking ID mismatch

**Solutions:**
```bash
# 1. Check booking status in database
python
>>> from app import app, MovieBooking
>>> with app.app_context():
...     b = MovieBooking.query.get(1)
...     print(f"Status: {b.payment_status}")
...     print(f"Method: {b.payment_method}")
...     print(f"Reference: {b.payment_reference}")

# 2. Manually verify with PayMongo
curl -u sk_test_XXX: https://api.paymongo.com/v1/sources/src_test_XXXX

# 3. Check available seats decreased
>>> showtime = b.showtime
>>> print(f"Available seats: {showtime.available_seats}")
```

**Fix:**
- Restart Flask app
- Clear browser cache
- Try booking again

---

### 6. "ModuleNotFoundError: No module named 'requests'"

**Problem**: `ImportError: No module named 'requests'`

**Cause**: requests library not installed

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt

# Verify requests is installed
pip show requests

# Should show:
# Name: requests
# Version: 2.31.0
```

---

### 7. API Authentication Errors

**Problem**: 401 Unauthorized from PayMongo API

**Cause**: Invalid or malformed API keys

**Solution:**
```bash
# 1. Check API keys in .env
echo $PAYMONGO_SECRET_KEY

# 2. Verify base64 encoding
python
>>> import base64
>>> key = 'sk_test_boUkkKYfbPnRVZMrVE13moQo'
>>> encoded = base64.b64encode(f'{key}:'.encode()).decode()
>>> print(f'Authorization: Basic {encoded}')

# 3. Test API call manually
curl -H 'Authorization: Basic {encoded_key}' \
  https://api.paymongo.com/v1/sources
```

---

### 8. Database Errors

**Problem**: "Error: table booking has no column named payment_method"

**Cause**: Old database schema, columns not added

**Solution:**
```bash
# 1. Backup database
cp instance/ticketing.db instance/ticketing.db.bak

# 2. Delete old database (CAREFUL!)
rm instance/ticketing.db

# 3. Reinitialize database
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()

# 4. Restart Flask
python run.py
```

**Note:** This will delete existing data. Use backup if needed.

---

### 9. Email Notifications Not Working

**Problem**: Users don't receive booking confirmation emails

**Causes:**
- SMTP settings incorrect
- Email credentials wrong
- Flask-Mail not configured

**Solutions:**
```bash
# 1. Verify email settings in .env
cat .env | grep MAIL

# 2. Test email sending
python
>>> from app import app, mail, Message
>>> with app.app_context():
...     msg = Message('Test', recipients=['your@email.com'])
...     mail.send(msg)

# 3. Check application logs for errors
python run.py 2>&1 | grep -i mail
```

**Common Issues:**
- Gmail requires "App Passwords" (not regular password)
- SMTP port 587 is correct (not 465 for TLS)
- Less secure apps need to be enabled in Gmail

---

### 10. Seats Not Updating After Payment

**Problem**: Available seats don't decrease after successful payment

**Possible Causes:**
- Payment not verified as completed
- Database transaction failed
- Booking ID mismatch

**Solution:**
```bash
# 1. Check showtime available_seats
python
>>> from app import app, Showtime
>>> with app.app_context():
...     show = Showtime.query.get(1)
...     print(f"Available: {show.available_seats}")

# 2. Manually test seat update
>>> show.available_seats -= 2
>>> from app import db
>>> db.session.commit()

# 3. Verify booking has completed status
>>> from app import MovieBooking
>>> b = MovieBooking.query.get(1)
>>> print(f"Payment status: {b.payment_status}")
```

---

### 11. Page Styling Broken

**Problem**: Payment page looks ugly or layout broken

**Possible Causes:**
- CSS file not loaded
- Browser cache issue
- Incompatible browser

**Solutions:**
1. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
2. Clear browser cache: Settings → Privacy → Clear Cache
3. Check CSS is loading: F12 → Network tab → Check status
4. Try different browser

---

### 12. Mobile Payment Issues

**Problem**: Payment doesn't work on mobile phone

**Possible Causes:**
- Mobile browser doesn't support fetch API
- Network timeout
- Screen size issue

**Solutions:**
```bash
# 1. Use modern mobile browser
# - Chrome Mobile
# - Firefox Mobile
# - Safari iOS

# 2. Test on desktop first to isolate issue

# 3. Check network connectivity
# - Use WiFi instead of mobile data
# - Check signal strength
```

---

## Performance Issues

### Payment Page Slow

**Causes & Solutions:**
- Large images → Compress images
- Many bookings → Add pagination
- Database slow → Add indexes
- API calls slow → Check network

```bash
# Add database index for faster queries
python
>>> from app import app, db
>>> with app.app_context():
...     db.engine.execute('CREATE INDEX idx_booking_user ON movie_booking(user_id)')

# Restart Flask
python run.py
```

---

## Security Issues

### Suspicious Payment Activity

**Check for:**
1. Duplicate bookings same user
2. Rapid payment attempts
3. Invalid amounts
4. Geographic anomalies

**Response:**
```bash
# 1. Check recent bookings
python
>>> from app import app, MovieBooking
>>> with app.app_context():
...     recent = MovieBooking.query.filter_by(payment_status='completed').order_by(MovieBooking.created_at.desc()).limit(10).all()
...     for b in recent:
...         print(f"{b.user_id}: ₱{b.total_amount} at {b.created_at}")

# 2. Check PayMongo dashboard for suspicious activity

# 3. Contact user if needed
```

---

## Debugging Tips

### Enable Debug Mode
```python
# In app.py
app.config['DEBUG'] = True

# Or in environment
export FLASK_ENV=development
python run.py
```

### View SQL Queries
```python
# In Python shell
>>> from app import app
>>> app.config['SQLALCHEMY_ECHO'] = True
>>> # Now all SQL queries will print to console
```

### Check API Calls
```bash
# Use curl to test API endpoints
curl -X GET http://localhost:5000/payment/movie/1 -H "Cookie: session=YOUR_SESSION"

# Check response status and headers
curl -I http://localhost:5000/payment/movie/1
```

### View Application Logs
```bash
# Redirect stdout to file
python run.py > app.log 2>&1

# View logs
tail -f app.log
```

---

## Escalation Path

### Level 1 - Self Help
1. Check this troubleshooting guide
2. Check PAYMONGO_SETUP.md
3. Clear browser cache
4. Restart Flask app

### Level 2 - Basic Debugging
1. Check browser console errors
2. Check application logs
3. Verify database schema
4. Test API manually with curl

### Level 3 - Advanced Debugging
1. Enable debug mode
2. Review SQL queries
3. Check network tab
4. Verify PayMongo settings

### Level 4 - Escalation
1. Check PayMongo status page
2. Contact PayMongo support
3. Review application code
4. Consider system redesign

---

## Getting Help

### Where to Find Answers

1. **This file** - Troubleshooting guide
2. **PAYMONGO_SETUP.md** - Integration details
3. **API_REFERENCE.md** - API details
4. **Browser Console** - JavaScript errors (F12)
5. **Application Logs** - Server errors
6. **PayMongo Dashboard** - Payment history

### Useful Commands

```bash
# Check Python version
python --version

# Check Flask version
pip show flask

# List all packages
pip list

# Check .env file
cat flask_app/.env

# View database tables
python
>>> from app import db, app
>>> with app.app_context():
...     print(db.metadata.tables.keys())

# Check PayMongo connectivity
python
>>> import requests
>>> r = requests.get('https://api.paymongo.com/v1/')
>>> print(r.status_code)
```

---

## Before Contacting Support

Please provide:
1. **Error message** (exact text)
2. **Screenshots** (of error)
3. **Steps to reproduce** (exact steps that caused issue)
4. **Browser/Device info** (Chrome, Firefox, etc.)
5. **Logs** (from app.log or console)
6. **Database state** (booking records)
7. **API keys** (DO NOT send actual keys!)
8. **Booking ID** (to look up transaction)

**Contact:**
- GitHub Issues: [Your repo]
- Email: support@tickethub.com
- PayMongo Support: https://www.paymongo.com/contact

---

## Known Limitations

⚠️ Test mode only - use provided test keys  
⚠️ No webhook integration yet - real-time updates not available  
⚠️ Single currency (PHP) - no multi-currency support  
⚠️ No refund management - refunds handled manually  
⚠️ Email optional - ensure SMTP configured for notifications  

---

## Future Improvements

🔄 Webhook integration for real-time updates  
🔄 Automated refund system  
🔄 Multi-currency support  
🔄 Advanced analytics  
🔄 Mobile app integration  
🔄 Automated fraud detection  

---

**Last Updated**: January 2026  
**Status**: Complete ✅  
**Questions**: Check documentation or contact support

---

*Remember: Most issues can be solved by:*
1. Checking .env file
2. Restarting Flask app
3. Clearing browser cache
4. Reading the documentation

**Good luck! 🚀**
