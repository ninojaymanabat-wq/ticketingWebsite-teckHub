# ✅ Validation Checklist - PayMongo Integration

Use this checklist to verify that the PayMongo integration is working correctly.

---

## Pre-Deployment Validation

### 1. Environment Setup
- [ ] `.env` file exists in `flask_app/` directory
- [ ] `PAYMONGO_SECRET_KEY` is set (sk_test_boUkkKYfbPnRVZMrVE13moQo)
- [ ] `PAYMONGO_PUBLIC_KEY` is set (pk_test_PA4RzhxD9BadaUFoTkaaTLbf)
- [ ] `SECRET_KEY` is configured
- [ ] `GOOGLE_API_KEY` is set (optional but recommended)

### 2. Dependencies
- [ ] Run `pip install -r requirements.txt`
- [ ] Verify `stripe` package is NOT installed (run `pip show stripe` - should not exist)
- [ ] Verify `requests` package is installed (run `pip show requests`)
- [ ] All other dependencies installed successfully

### 3. Code Files
- [ ] `app.py` contains PayMongo imports (requests, base64)
- [ ] `app.py` does NOT contain Stripe imports
- [ ] `config.py` has PayMongo keys configured
- [ ] `requirements.txt` has requests==2.31.0
- [ ] `requirements.txt` does NOT have stripe

### 4. Template Files
- [ ] `templates/payment/checkout.html` exists and is updated
- [ ] `templates/payment/success.html` exists and is updated
- [ ] Both files are properly formatted (no syntax errors)

### 5. Documentation
- [ ] `PAYMONGO_SETUP.md` exists
- [ ] `QUICKSTART.md` exists
- [ ] `CHANGELOG.md` exists
- [ ] `API_REFERENCE.md` exists
- [ ] `PAYMENT_IMPLEMENTATION_SUMMARY.md` exists

---

## Runtime Validation

### 1. Application Startup
```bash
# In flask_app directory
python run.py
```

- [ ] No import errors
- [ ] No syntax errors
- [ ] Application starts successfully
- [ ] "Running on http://127.0.0.1:5000" appears
- [ ] No warnings about Stripe

### 2. Database
- [ ] Database initializes without errors
- [ ] Can view existing tables
- [ ] `payment_method` column exists in bookings table
- [ ] `payment_reference` column exists
- [ ] `payment_status` column exists

### 3. User Authentication
- [ ] Can register new user
- [ ] Can login with valid credentials
- [ ] Can logout successfully
- [ ] Session management works

---

## Payment Flow Validation

### 1. Movie Booking Test

**Step 1: Browse Movies**
- [ ] Go to `/movies`
- [ ] Can see movie list
- [ ] Can click on a movie

**Step 2: Select Showtime**
- [ ] Movie detail page loads
- [ ] Can see available showtimes
- [ ] Can click "Book Now"

**Step 3: Book Tickets**
- [ ] Seat selection UI works
- [ ] Can select number of tickets
- [ ] Can select specific seats
- [ ] Booking preview shows correct details
- [ ] Click "Proceed to Checkout"

**Step 4: Payment Page**
- [ ] Payment page loads properly
- [ ] Can see two payment method buttons (GCash, PayMaya)
- [ ] Can click to select GCash
- [ ] Can click to select PayMaya
- [ ] Order summary displays correctly
- [ ] Amount shown is correct
- [ ] Security badge visible

**Step 5: Create Payment Source**
- [ ] Click "Proceed to GCash Payment"
- [ ] Loading spinner shows briefly
- [ ] No JavaScript errors in console
- [ ] System should redirect (or show error if test environment)

### 2. Bus Booking Test

**Step 1: Search Bus**
- [ ] Go to `/bus/search`
- [ ] Enter origin, destination, date
- [ ] Click search
- [ ] Results display

**Step 2: Book Bus**
- [ ] Click "Book Now" on a route
- [ ] Can select seats
- [ ] Can enter passenger names
- [ ] Click "Proceed to Payment"

**Step 3: Payment Page**
- [ ] Payment page loads
- [ ] GCash and PayMaya buttons visible
- [ ] Order summary shows bus details
- [ ] Amount is correct
- [ ] Can proceed with payment

### 3. Success Page Test

**After Successful Payment:**
- [ ] Redirected to success page
- [ ] Page shows "✓ Payment Successful!"
- [ ] Booking reference displayed
- [ ] Status shows "Confirmed"
- [ ] Payment amount shown
- [ ] "View My Bookings" button works
- [ ] "Back to Home" button works
- [ ] Print button works

---

## API Endpoint Validation

### 1. Payment Page Endpoint
```bash
curl http://localhost:5000/payment/movie/1
```
- [ ] Returns 200 (page loads)
- [ ] Returns 404 if booking doesn't exist
- [ ] Returns 302 redirect if not logged in

### 2. Create PayMongo Source
```bash
curl -X POST http://localhost:5000/create-paymongo-source \
  -H "Content-Type: application/json" \
  -d '{"booking_type":"movie","booking_id":1,"payment_method":"gcash"}'
```
- [ ] Returns sourceId
- [ ] Returns redirectUrl
- [ ] redirectUrl starts with https://checkout.paymongo.com
- [ ] No Stripe references in response

### 3. Booked Seats Endpoint
```bash
curl -X POST http://localhost:5000/get-booked-seats \
  -H "Content-Type: application/json" \
  -d '{"showtime_id":1}'
```
- [ ] Returns booked_seats array
- [ ] Array contains seat identifiers
- [ ] Works for completed bookings only

---

## UI/UX Validation

### 1. Checkout Page Design
- [ ] Page has gradient background (dark theme)
- [ ] Payment methods show as cards
- [ ] Cards have hover effects
- [ ] Method selection switches sections correctly
- [ ] Order summary displays nicely
- [ ] Colors are consistent
- [ ] Text is readable
- [ ] Responsive on mobile

### 2. Receipt Page Design
- [ ] Success header has checkmark icon
- [ ] Green success theme
- [ ] Booking details laid out clearly
- [ ] Payment summary shows correctly
- [ ] QR code area visible
- [ ] Buttons are clickable
- [ ] Print layout is professional
- [ ] Mobile friendly

### 3. Error Messages
- [ ] Error displays when payment fails
- [ ] Error is readable and helpful
- [ ] User can retry payment
- [ ] No console errors

---

## Security Validation

### 1. Authentication
- [ ] Cannot access payment page without login
- [ ] Cannot access another user's booking
- [ ] Session timeout works
- [ ] Logout clears session

### 2. API Security
- [ ] API calls use POST method
- [ ] Request headers include Content-Type
- [ ] No sensitive keys in frontend code
- [ ] PayMongo API calls use base64 auth
- [ ] User authorization checked server-side

### 3. Payment Security
- [ ] No card information stored
- [ ] Redirect to PayMongo is secure (HTTPS)
- [ ] Return from PayMongo verified
- [ ] Payment status verified before confirming

---

## Database Validation

### 1. Booking Records
```sql
SELECT * FROM movie_booking WHERE payment_status='completed' LIMIT 1;
SELECT * FROM bus_booking WHERE payment_status='completed' LIMIT 1;
```
- [ ] `payment_method` shows 'gcash' or 'paymaya'
- [ ] `payment_reference` has PayMongo source ID
- [ ] `payment_status` is 'completed'
- [ ] No `stripe_payment_id` values set (except old records)

### 2. Available Seats
```sql
SELECT available_seats FROM showtime WHERE id=1;
SELECT available_seats FROM bus_schedule WHERE id=1;
```
- [ ] Seats decreased after successful payment
- [ ] Seats NOT decreased for pending payments
- [ ] Seats NOT decreased for failed payments

### 3. Booking References
```sql
SELECT booking_reference FROM movie_booking LIMIT 5;
```
- [ ] All booking references are unique
- [ ] Format is 10 characters (uppercase + digits)
- [ ] No NULL values

---

## Error Handling Validation

### 1. Missing Payment Method
- [ ] Try submitting without selecting method
- [ ] Error message displays
- [ ] User can retry

### 2. Invalid Booking
- [ ] Try accessing `/payment/movie/999999`
- [ ] Shows 404 error or redirects appropriately
- [ ] No system crash

### 3. Network Error Simulation
- [ ] Simulate network failure
- [ ] Error message shows to user
- [ ] No sensitive info in error
- [ ] User can retry

### 4. Invalid API Response
- [ ] If PayMongo returns error, handle gracefully
- [ ] Error message appropriate
- [ ] No system crash
- [ ] User can retry

---

## Performance Validation

### 1. Load Times
- [ ] Payment page loads in < 2 seconds
- [ ] Success page loads in < 1 second
- [ ] API calls complete in < 3 seconds
- [ ] No timeouts

### 2. Responsiveness
- [ ] Page works on desktop (1920x1080)
- [ ] Page works on tablet (768x1024)
- [ ] Page works on mobile (375x667)
- [ ] Images scale properly
- [ ] Text readable on all sizes

### 3. Browser Compatibility
- [ ] Chrome ✅
- [ ] Firefox ✅
- [ ] Safari ✅
- [ ] Edge ✅
- [ ] Mobile browsers ✅

---

## Data Integrity Validation

### 1. Booking Consistency
- [ ] User can only see own bookings
- [ ] Booking details are accurate
- [ ] Payment status consistent with reality
- [ ] Seat selections recorded correctly

### 2. Transaction Integrity
- [ ] Each booking has unique reference
- [ ] Payment recorded once (no duplicates)
- [ ] Amount matches original booking
- [ ] Status updates are atomic

### 3. Audit Trail
- [ ] Created_at timestamp recorded
- [ ] Payment method recorded
- [ ] Payment reference stored
- [ ] All changes logged

---

## Production Readiness Validation

### Pre-Production Checklist
- [ ] All tests passing
- [ ] No deprecated warnings
- [ ] Error handling complete
- [ ] Security review passed
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Backup plan ready
- [ ] Support contact available

### Production Deployment
- [ ] Use production PayMongo keys
- [ ] Enable HTTPS
- [ ] Set DEBUG = False
- [ ] Configure logging
- [ ] Set up monitoring
- [ ] Configure alerts
- [ ] Plan rollback procedure
- [ ] Document production URLs

---

## Post-Deployment Validation

### 1. Monitor Transactions
- [ ] Check PayMongo dashboard
- [ ] Verify transactions appearing
- [ ] Check payment amounts
- [ ] Review payment methods used

### 2. Check Logs
- [ ] No errors in application logs
- [ ] No Stripe references in logs
- [ ] PayMongo API calls successful
- [ ] Database operations normal

### 3. User Reports
- [ ] Users can complete bookings
- [ ] Users can see receipts
- [ ] Users receive confirmations
- [ ] No complaints about payments

### 4. System Health
- [ ] Database healthy
- [ ] API responding normally
- [ ] Seat availability accurate
- [ ] Email notifications working

---

## Rollback Procedure (If Needed)

- [ ] Keep previous Flask app backup
- [ ] Keep previous .env backup
- [ ] Document current state
- [ ] Test rollback locally first
- [ ] Have rollback command ready
- [ ] Notify users if rolling back
- [ ] Monitor system post-rollback

---

## Sign-Off

**Validation Date**: _______________  
**Validated By**: _______________  
**Status**: ☐ PASS  ☐ FAIL  

**Signature**: _____________________________  

---

## Notes

Use this space to document any issues found or resolved:

```
Issue: ___________________
Resolution: _______________

Issue: ___________________
Resolution: _______________
```

---

## Additional Resources

- PAYMONGO_SETUP.md - Technical integration details
- QUICKSTART.md - Installation guide
- API_REFERENCE.md - API documentation
- CHANGELOG.md - Version history
- PayMongo Docs - https://www.paymongo.com/docs

---

**Last Updated**: January 2026  
**Status**: Ready for Production ✅
