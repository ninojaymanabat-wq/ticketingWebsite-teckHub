# TicketHub - Quick Start Guide

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/ninojaymanabat-wq/ticketingWebsite-teckHub.git
cd flask_app
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Create a `.env` file in `flask_app/` directory with:
```env
SECRET_KEY=your-secret-key-here
PAYMONGO_SECRET_KEY=sk_test_boUkkKYfbPnRVZMrVE13moQo
PAYMONGO_PUBLIC_KEY=pk_test_PA4RzhxD9BadaUFoTkaaTLbf
GOOGLE_API_KEY=your-google-api-key
```

### 5. Initialize Database
```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### 6. Run the Application
```bash
python run.py
```

Visit `http://localhost:5000` in your browser.

---

## User Features

### 🎬 Movie Booking
1. Browse available movies
2. Select a showtime
3. Choose seats and ticket quantity
4. Proceed to checkout
5. Complete payment via GCash or PayMaya
6. Receive instant confirmation

### 🚌 Bus Booking
1. Search for bus routes
2. Select travel date and bus
3. Choose seats and passengers
4. Proceed to checkout
5. Complete payment via GCash or PayMaya
6. Receive booking reference

### 💳 Payment Methods
- **GCash**: Instant e-wallet payment
- **PayMaya**: Secure digital wallet
- Both methods redirect to PayMongo for secure processing

### 📱 Dashboard
- View all your bookings
- Check booking status
- Download/print tickets
- Track payment history

---

## Admin Features

### 🎥 Movie Management
- Add new movies with posters
- Create showtimes and set prices
- Manage available seats
- Track bookings

### 🚌 Bus Management
- Add bus routes
- Configure schedules
- Set pricing
- Manage seat availability

### 📊 Dashboard
- View booking statistics
- Monitor revenue
- Track payment status
- See user activity

---

## Payment Testing

### Test Flow
1. Register/Login to the system
2. Create a booking (movie or bus)
3. Proceed to checkout
4. Select payment method (GCash or PayMaya)
5. Click "Proceed to Payment"
6. Use PayMongo test credentials
7. Complete payment
8. View receipt and booking confirmation

### Test Payment Details
- **Status**: Test/Sandbox mode
- **Currency**: PHP (Philippine Peso)
- **Methods**: GCash, PayMaya
- **No real money charged**: This is test mode

---

## Features Overview

✅ User Registration & Authentication  
✅ Movie & Bus Booking System  
✅ Seat Selection & Management  
✅ GCash & PayMaya E-Wallet Payments  
✅ Instant Booking Confirmation  
✅ Receipt & Ticket Generation  
✅ Admin Dashboard & Management  
✅ Responsive Design (Mobile & Desktop)  
✅ Security: SSL, HTTPS, Secure Payment  
✅ Email Notifications (optional)  

---

## Troubleshooting

### Can't login?
- Verify email/password are correct
- Check if account is registered
- Try creating a new account

### Payment failing?
- Ensure internet connection is stable
- Try different payment method
- Check PayMongo service status
- Verify correct API keys in .env

### Seats not showing?
- Refresh the page
- Clear browser cache
- Check database connectivity
- Verify showtime/schedule exists

### Email notifications not working?
- Verify SMTP settings in .env
- Check email account has 2FA disabled
- Ensure app password is used (not regular password)
- Check spam folder

---

## File Structure

```
flask_app/
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables
├── static/
│   ├── css/                       # Stylesheets
│   ├── js/                        # JavaScript files
│   ├── images/                    # Image assets
│   └── uploads/                   # User uploaded files
├── templates/
│   ├── base.html                 # Base template
│   ├── index.html                # Homepage
│   ├── auth/                     # Auth pages
│   ├── movies/                   # Movie pages
│   ├── bus/                      # Bus pages
│   ├── payment/                  # Payment pages
│   ├── admin/                    # Admin pages
│   └── dashboard/                # User dashboard
└── instance/
    └── ticketing.db              # SQLite database
```

---

## Security Best Practices

🔒 Always use HTTPS in production  
🔒 Keep API keys secure (never commit .env)  
🔒 Use strong SECRET_KEY  
🔒 Enable database backups  
🔒 Regular security updates  
🔒 Input validation on all forms  
🔒 SQL injection prevention (SQLAlchemy ORM)  
🔒 CSRF protection enabled  

---

## Performance Tips

⚡ Cache frequently accessed pages  
⚡ Optimize database queries  
⚡ Compress static assets  
⚡ Use CDN for images  
⚡ Enable browser caching  
⚡ Monitor server resources  

---

## Support & Documentation

- **PayMongo Docs**: https://www.paymongo.com/docs
- **Flask Docs**: https://flask.palletsprojects.com
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org
- **Issues**: Open GitHub issue with detailed description

---

## Version Info

- **Python**: 3.8+
- **Flask**: 3.0.0
- **Database**: SQLite (development) / PostgreSQL (production)
- **Payment**: PayMongo API v1
- **Status**: Production Ready ✅

---

**Last Updated**: January 2026  
**Maintainer**: TicketHub Development Team
