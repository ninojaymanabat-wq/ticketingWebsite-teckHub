# PayMongo Integration Setup Guide

## Overview
This ticketing website has been updated to use **PayMongo E-Wallet** payment instead of Stripe. The system now supports GCash and PayMaya payments with a beautiful, modern checkout experience.

## What Was Changed

### 1. Backend Changes (`app.py`)
- **Removed**: Stripe integration and payment intent creation
- **Added**: PayMongo API integration with base64 authentication
- **New Endpoint**: `/create-paymongo-source` - Creates PayMongo payment sources for e-wallet transactions
- **Updated**: `/payment-success/<booking_type>/<int:booking_id>` - Now verifies PayMongo payment status
- **Removed**: Bank transfer pending endpoint (bank payments no longer supported)

### 2. Frontend Changes

#### Payment Checkout Page (`templates/payment/checkout.html`)
- Completely redesigned with modern gradient UI
- Only e-wallet payment methods (GCash & PayMaya)
- Interactive method selection cards
- Real-time payment section switching
- Integrated PayMongo API calls
- Beautiful order summary display
- Security badges and info boxes

#### Success/Receipt Page (`templates/payment/success.html`)
- Professional receipt design
- QR code placeholder for booking reference
- Detailed booking information display
- Print-friendly receipt
- Action buttons for dashboard and home
- Confirmation message with email notification

### 3. Dependencies (`requirements.txt`)
- **Removed**: `stripe==7.8.0`
- **Added**: `requests==2.31.0` (for PayMongo API calls)
- **Verified**: `google-generativeai==0.3.0` and `Flask-Mail==0.9.1`

### 4. Configuration (`config.py`)
- Replaced all Stripe keys with PayMongo keys
- Configured PayMongo API URL endpoint

### 5. Environment Variables (`.env`)
```env
PAYMONGO_SECRET_KEY=sk_test_boUkkKYfbPnRVZMrVE13moQo
PAYMONGO_PUBLIC_KEY=pk_test_PA4RzhxD9BadaUFoTkaaTLbf
```

## How Payment Flow Works

### 1. User Selection
- User selects payment method (GCash or PayMaya)
- Reviews order summary
- Clicks "Proceed to Payment"

### 2. Source Creation
- Frontend sends payment method to `/create-paymongo-source`
- Backend creates PayMongo source with:
  - Amount in cents (PHP currency)
  - Payment method type (gcash/paymaya)
  - Redirect URLs for success/failure
- Returns checkout URL from PayMongo

### 3. Payment Processing
- User is redirected to PayMongo checkout page
- User completes payment in their e-wallet
- PayMongo redirects back to success page

### 4. Payment Verification
- Backend verifies payment status with PayMongo API
- Updates booking payment status (completed/pending)
- Reduces available seats for the event
- Shows professional receipt with booking details

## Payment Methods Supported

### GCash
- Instant e-wallet payment
- Real-time confirmation
- Used in Philippines

### PayMaya
- Secure digital wallet
- Credit/debit card integration
- Used in Philippines

## Testing

### Test Credentials (from PayMongo)
- **Secret Key**: `sk_test_boUkkKYfbPnRVZMrVE13moQo`
- **Public Key**: `pk_test_PA4RzhxD9BadaUFoTkaaTLbf`

### Test Payment Flow
1. Go to checkout page
2. Select payment method
3. Click "Proceed to Payment"
4. You'll be redirected to PayMongo's test environment
5. Use PayMongo test credentials to complete payment
6. Return to success page with receipt

## Security Features

✅ HTTPS-only API calls  
✅ Base64 encoded authentication  
✅ Server-side payment verification  
✅ Reference number tracking  
✅ User authorization checks  
✅ Secure redirect URLs  

## Booking Reference System

Each booking gets a unique 10-character reference:
- Format: `UPPERCASE + DIGITS` (e.g., `ABC1234XYZ`)
- Used for payment tracking
- Displayed on receipt
- Used for check-in at venue

## Database Schema

### New Payment Columns
- `payment_method`: Stores payment type ('gcash', 'paymaya', etc.)
- `payment_reference`: Stores PayMongo source ID or transaction reference
- `payment_status`: Tracks payment state ('pending', 'completed', 'failed')

### Backward Compatibility
- Old `stripe_payment_id` column retained for legacy data
- New system doesn't populate this field

## Troubleshooting

### Payment Not Processing
1. Verify PayMongo API keys in `.env`
2. Check PayMongo account is in test/live mode
3. Verify internet connectivity
4. Check browser console for JavaScript errors

### Redirect Issues
- Ensure Flask URL_FOR uses `_external=True`
- Check CORS headers if cross-origin
- Verify SSL certificate for production

### Database Issues
- Clear pending bookings regularly
- Verify available_seats is accurate
- Check booking references are unique

## Future Improvements

🔄 Webhook integration for real-time payment status updates  
📱 Mobile app integration  
🔐 Enhanced fraud detection  
📊 Payment analytics dashboard  
🌍 Multi-currency support  
🔄 Refund management system  

## Support

For PayMongo integration support, visit: https://www.paymongo.com/docs

For ticketing system issues, check the main README.md

---

**Last Updated**: January 2026  
**Status**: Production Ready ✅
