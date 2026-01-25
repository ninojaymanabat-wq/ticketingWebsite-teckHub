# Movie + Bus Ticketing System

A full-stack Flask application for booking movie and bus tickets with Stripe payment integration.

## Features

### User Features
- User registration and authentication
- Browse movies with details (poster, description, cast, etc.)
- Book movie tickets with seat selection
- Search and book bus tickets
- View booking history
- Secure Stripe payment integration

### Admin Features
- Dashboard with statistics
- Add/Edit/Delete movies with poster upload
- Manage cinemas and showtimes
- Add/Edit/Delete bus routes
- View all bookings

## Tech Stack

- **Backend:** Python Flask
- **Database:** SQLite with SQLAlchemy ORM
- **Authentication:** Flask-Login
- **Payments:** Stripe
- **Frontend:** Jinja2 Templates, Tailwind CSS
- **File Upload:** Pillow for image processing

## Installation

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Step 1: Clone and Setup

```bash
cd flask_app
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env file with your settings
# Important: Add your Stripe API keys
```

### Step 5: Initialize Database and Run

```bash
# This will create the database, admin user, and start the server
python run.py
```

### Step 6 (Optional): Seed Sample Data

```bash
python seed_data.py
```

## Usage

### Access Points

- **Main Site:** http://127.0.0.1:5000
- **Admin Panel:** http://127.0.0.1:5000/admin

### Default Admin Credentials

- **Email:** admin@ticketing.com
- **Password:** admin123

> ⚠️ **Important:** Change these credentials in production!

## Stripe Configuration

1. Create a Stripe account at https://stripe.com
2. Get your API keys from https://dashboard.stripe.com/test/apikeys
3. Add keys to your `.env` file:
   ```
   STRIPE_PUBLIC_KEY=pk_test_...
   STRIPE_SECRET_KEY=sk_test_...
   ```

### Testing Payments

Use Stripe test card numbers:
- **Success:** 4242 4242 4242 4242
- **Declined:** 4000 0000 0000 0002
- **Any expiry date** in the future
- **Any 3-digit CVC**

## Project Structure

```
flask_app/
├── app.py              # Main application with routes and models
├── config.py           # Configuration settings
├── run.py              # Application entry point
├── seed_data.py        # Sample data seeder
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── static/
│   └── uploads/        # Uploaded movie posters
└── templates/
    ├── base.html       # Base template
    ├── index.html      # Homepage
    ├── auth/           # Login/Register templates
    ├── movies/         # Movie listing and booking
    ├── bus/            # Bus search and booking
    ├── payment/        # Checkout and success pages
    ├── dashboard/      # User dashboard
    └── admin/          # Admin panel templates
```

## API Endpoints

### Public Routes
- `GET /` - Homepage
- `GET /movies` - Movie listings
- `GET /movies/<id>` - Movie details
- `GET /bus` - Bus search
- `GET /bus/search` - Bus search results

### Auth Routes
- `GET/POST /login` - User login
- `GET/POST /register` - User registration
- `GET /logout` - User logout

### Booking Routes (Login Required)
- `GET/POST /movies/<id>/book` - Book movie tickets
- `GET/POST /bus/<id>/book` - Book bus tickets
- `GET/POST /checkout/<booking_id>` - Payment checkout
- `GET /payment/success` - Payment success page
- `GET /dashboard` - User dashboard

### Admin Routes (Admin Only)
- `GET /admin` - Admin dashboard
- `GET/POST /admin/movies/add` - Add movie
- `GET/POST /admin/movies/edit/<id>` - Edit movie
- `POST /admin/movies/delete/<id>` - Delete movie
- Similar routes for cinemas, showtimes, and buses

## Security Features

- Password hashing with Werkzeug
- CSRF protection with Flask-WTF
- Secure session management
- Admin-only route protection
- Input validation and sanitization

## License

MIT License
