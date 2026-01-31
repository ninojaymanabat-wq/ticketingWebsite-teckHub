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

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ticketing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# PayMongo configuration
PAYMONGO_SECRET_KEY = os.environ.get('PAYMONGO_SECRET_KEY', 'sk_test_boUkkKYfbPnRVZMrVE13moQo')
PAYMONGO_PUBLIC_KEY = os.environ.get('PAYMONGO_PUBLIC_KEY', 'pk_test_PA4RzhxD9BadaUFoTkaaTLbf')
PAYMONGO_API_URL = 'https://api.paymongo.com/v1'

# Google Generative AI configuration
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', 'AIzaSyBDlPAFKwK7D3x7g99r0emxNjbqm1m1INY')
genai.configure(api_key=GOOGLE_API_KEY)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configure Flask-Mail (update with your SMTP settings)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', '')
mail = Mail(app)

# Serializer for password reset tokens
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== DATABASE MODELS ====================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    movie_bookings = db.relationship('MovieBooking', backref='user', lazy=True)
    bus_bookings = db.relationship('BusBooking', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    genre = db.Column(db.String(100))
    duration = db.Column(db.Integer)  # in minutes
    rating = db.Column(db.String(10))  # PG, PG-13, R, etc.
    poster_image = db.Column(db.String(255))
    trailer_url = db.Column(db.String(255))
    release_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    showtimes = db.relationship('Showtime', backref='movie', lazy=True, cascade='all, delete-orphan')


class Cinema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    total_seats = db.Column(db.Integer, default=100)
    
    showtimes = db.relationship('Showtime', backref='cinema', lazy=True)


class Showtime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    cinema_id = db.Column(db.Integer, db.ForeignKey('cinema.id'), nullable=False)
    show_date = db.Column(db.Date, nullable=False)
    show_time = db.Column(db.Time, nullable=False)
    price = db.Column(db.Float, nullable=False)
    available_seats = db.Column(db.Integer)
    
    bookings = db.relationship('MovieBooking', backref='showtime', lazy=True)


class MovieBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    showtime_id = db.Column(db.Integer, db.ForeignKey('showtime.id'), nullable=False)
    num_tickets = db.Column(db.Integer, nullable=False)
    seat_numbers = db.Column(db.String(200))
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed

    # New columns
    payment_method = db.Column(db.String(20))     # 'card', 'ewallet', 'bank', 'online'
    payment_reference = db.Column(db.String(255)) # stripe/payment intent id or e-wallet/bank reference

    # Retain for backward compatibility (optional)
    stripe_payment_id = db.Column(db.String(100))

    booking_reference = db.Column(db.String(20), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BusRoute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    bus_operator = db.Column(db.String(100))
    bus_type = db.Column(db.String(50))  # AC, Non-AC, Sleeper, etc.
    departure_time = db.Column(db.Time, nullable=False)
    arrival_time = db.Column(db.Time, nullable=False)
    duration = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    total_seats = db.Column(db.Integer, default=40)
    amenities = db.Column(db.String(255))  # WiFi, Charging, etc.
    is_active = db.Column(db.Boolean, default=True)
    
    schedules = db.relationship('BusSchedule', backref='route', lazy=True)


class BusSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('bus_route.id'), nullable=False)
    travel_date = db.Column(db.Date, nullable=False)
    available_seats = db.Column(db.Integer)
    
    bookings = db.relationship('BusBooking', backref='schedule', lazy=True)


class BusBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('bus_schedule.id'), nullable=False)
    num_tickets = db.Column(db.Integer, nullable=False)
    seat_numbers = db.Column(db.String(200))
    passenger_names = db.Column(db.Text)
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')

    # New columns
    payment_method = db.Column(db.String(20))     # 'card', 'ewallet', 'bank', 'online'
    payment_reference = db.Column(db.String(255)) # stripe/payment intent id or e-wallet/bank reference

    # Retain for backward compatibility (optional)
    stripe_payment_id = db.Column(db.String(100))

    booking_reference = db.Column(db.String(20), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== HELPER FUNCTIONS ====================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need admin access for this action.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def generate_booking_reference():
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


# ==================== ROUTES - MAIN ====================

@app.route('/')
def index():
    movies = Movie.query.filter_by(is_active=True).order_by(Movie.release_date.desc()).limit(6).all()
    routes = BusRoute.query.filter_by(is_active=True).limit(6).all()
    return render_template('index.html', movies=movies, routes=routes)


# ==================== ROUTES - AUTHENTICATION ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))
        
        user = User(email=email, name=name, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash('Welcome back!', 'success')
            return redirect(next_page or url_for('index'))
        
        flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ==================== ROUTES - MOVIES ====================

@app.route('/movies')
def movies():
    movies = Movie.query.filter_by(is_active=True).order_by(Movie.release_date.desc()).all()
    return render_template('movies/list.html', movies=movies)


@app.route('/movies/<int:movie_id>')
def movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    showtimes = Showtime.query.filter(
        Showtime.movie_id == movie_id,
        Showtime.show_date >= datetime.now().date()
    ).order_by(Showtime.show_date, Showtime.show_time).all()
    return render_template('movies/detail.html', movie=movie, showtimes=showtimes)


@app.route('/movies/book/<int:showtime_id>', methods=['GET', 'POST'])
@login_required
def book_movie(showtime_id):
    showtime = Showtime.query.get_or_404(showtime_id)
    
    if request.method == 'POST':
        num_tickets = int(request.form.get('num_tickets', 1))
        seat_numbers = request.form.get('seat_numbers', '')
        
        if num_tickets > showtime.available_seats:
            flash('Not enough seats available.', 'error')
            return redirect(url_for('book_movie', showtime_id=showtime_id))
        
        total_amount = num_tickets * showtime.price
        booking_ref = generate_booking_reference()
        
        booking = MovieBooking(
            user_id=current_user.id,
            showtime_id=showtime_id,
            num_tickets=num_tickets,
            seat_numbers=seat_numbers,
            total_amount=total_amount,
            booking_reference=booking_ref
        )
        db.session.add(booking)
        db.session.commit()
        
        return redirect(url_for('payment', booking_type='movie', booking_id=booking.id))
    
    return render_template('movies/book.html', showtime=showtime)


# ==================== ROUTES - BUS ====================

@app.route('/bus')
def bus_routes():
    routes = BusRoute.query.filter_by(is_active=True).all()
    return render_template('bus/list.html', routes=routes)


@app.route('/bus/search', methods=['GET', 'POST'])
def search_bus():
    if request.method == 'POST':
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        travel_date = request.form.get('travel_date')
        
        routes = BusRoute.query.filter(
            BusRoute.origin.ilike(f'%{origin}%'),
            BusRoute.destination.ilike(f'%{destination}%'),
            BusRoute.is_active == True
        ).all()
        
        return render_template('bus/search_results.html', 
                             routes=routes, 
                             origin=origin, 
                             destination=destination,
                             travel_date=travel_date)
    
    return render_template('bus/search.html')


@app.route('/bus/book/<int:route_id>', methods=['GET', 'POST'])
@login_required
def book_bus(route_id):
    route = BusRoute.query.get_or_404(route_id)
    travel_date = request.args.get('date', datetime.now().date().isoformat())
    
    # Get or create schedule for the date
    schedule = BusSchedule.query.filter_by(
        route_id=route_id,
        travel_date=datetime.strptime(travel_date, '%Y-%m-%d').date()
    ).first()
    
    if not schedule:
        schedule = BusSchedule(
            route_id=route_id,
            travel_date=datetime.strptime(travel_date, '%Y-%m-%d').date(),
            available_seats=route.total_seats
        )
        db.session.add(schedule)
        db.session.commit()
    
    if request.method == 'POST':
        num_tickets = int(request.form.get('num_tickets', 1))
        seat_numbers = request.form.get('seat_numbers', '')
        passenger_names = request.form.get('passenger_names', '')
        
        if num_tickets > schedule.available_seats:
            flash('Not enough seats available.', 'error')
            return redirect(url_for('book_bus', route_id=route_id, date=travel_date))
        
        total_amount = num_tickets * route.price
        booking_ref = generate_booking_reference()
        
        booking = BusBooking(
            user_id=current_user.id,
            schedule_id=schedule.id,
            num_tickets=num_tickets,
            seat_numbers=seat_numbers,
            passenger_names=passenger_names,
            total_amount=total_amount,
            booking_reference=booking_ref
        )
        db.session.add(booking)
        db.session.commit()
        
        return redirect(url_for('payment', booking_type='bus', booking_id=booking.id))
    
    return render_template('bus/book.html', route=route, schedule=schedule, travel_date=travel_date)


# ==================== ROUTES - PAYMENT ====================

@app.route('/payment/<booking_type>/<int:booking_id>')
@login_required
def payment(booking_type, booking_id):
    if booking_type == 'movie':
        booking = MovieBooking.query.get_or_404(booking_id)
    else:
        booking = BusBooking.query.get_or_404(booking_id)
    
    if booking.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('index'))
    
    return render_template('payment/checkout.html', 
                         booking=booking, 
                         booking_type=booking_type,
                         paymongo_public_key=PAYMONGO_PUBLIC_KEY)


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
            return jsonify({'error': 'Failed to create payment source'}), 400
        
        source_data = response.json()['data']
        source_id = source_data['id']
        
        # Store payment reference
        booking.payment_method = payment_method
        booking.payment_reference = source_id
        db.session.commit()
        
        return jsonify({
            'sourceId': source_id,
            'redirectUrl': source_data['attributes']['redirect']['checkout_url']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/payment-success/<booking_type>/<int:booking_id>')
@login_required
def payment_success(booking_type, booking_id):
    source_id = request.args.get('source_id')
    
    if booking_type == 'movie':
        booking = MovieBooking.query.get_or_404(booking_id)
    else:
        booking = BusBooking.query.get_or_404(booking_id)
    
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
                else:
                    booking.payment_status = 'pending'
            else:
                booking.payment_status = 'pending'
        except Exception as e:
            booking.payment_status = 'pending'
    else:
        booking.payment_status = 'completed'
    
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





@app.route('/get-booked-seats', methods=['POST'])
def get_booked_seats():
    data = request.get_json()
    showtime_id = data.get('showtime_id')
    
    # Get all completed bookings for this showtime
    bookings = MovieBooking.query.filter_by(showtime_id=showtime_id, payment_status='completed').all()
    
    booked_seats = []
    for booking in bookings:
        if booking.seat_numbers:
            seats = booking.seat_numbers.split(',')
            booked_seats.extend(seats)
    
    return jsonify({'booked_seats': booked_seats})


@app.route('/get-booked-bus-seats', methods=['POST'])
def get_booked_bus_seats():
    data = request.get_json()
    schedule_id = data.get('schedule_id')
    
    # Get all completed bookings for this bus schedule
    bookings = BusBooking.query.filter_by(schedule_id=schedule_id, payment_status='completed').all()
    
    booked_seats = []
    for booking in bookings:
        if booking.seat_numbers:
            seats = booking.seat_numbers.split(',')
            booked_seats.extend(seats)
    
    return jsonify({'booked_seats': booked_seats})




# Replace the existing /payment-ewallet-pending route with this updated version
@app.route('/payment-ewallet-pending', methods=['POST'])
@login_required
def payment_ewallet_pending():
    data = request.get_json()
    booking_type = data.get('booking_type')
    booking_id = data.get('booking_id')
    ewallet_method = data.get('payment_method')  # expected values: 'gcash' or 'paymaya'
    reference_number = data.get('reference_number')

    if booking_type == 'movie':
        booking = MovieBooking.query.get_or_404(booking_id)
    else:
        booking = BusBooking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # If the client didn't provide a reference number, generate one server-side
    if not reference_number:
        reference_number = generate_booking_reference()

    # Mark as pending e-wallet transfer and store method/reference
    booking.payment_status = 'pending'
    booking.payment_method = 'ewallet'
    booking.payment_reference = reference_number
    booking.stripe_payment_id = f'{ewallet_method.upper()}_TRANSFER_{booking_id}_{reference_number}'  # optional/back-compat

    db.session.commit()

    method_name = 'GCash' if ewallet_method == 'gcash' else 'PayMaya' if ewallet_method == 'paymaya' else ewallet_method.upper()
    flash(f'{method_name} payment recorded. Your booking will be confirmed once payment is verified.', 'info')

    # Return the reference number so the client can display/confirm it
    return jsonify({'success': True, 'reference_number': reference_number})

# @app.route('/payment-ewallet-pending', methods=['POST'])
# @login_required
# def payment_ewallet():
#     """
#     Create a PayMongo Payment Intent for GCash or PayMaya
#     """
#     data = request.get_json()
#     booking_type = data.get("booking_type")
#     booking_id = data.get("booking_id")
#     payment_method = data.get("payment_method")  # 'gcash' or 'paymaya'

#     if booking_type == 'movie':
#         booking = MovieBooking.query.get_or_404(booking_id)
#     else:
#         booking = BusBooking.query.get_or_404(booking_id)

#     if booking.user_id != current_user.id:
#         return jsonify({"error": "Unauthorized"}), 403

#     amount = int(booking.total_amount * 100)  # PayMongo expects cents

#     payload = {
#         "data": {
#             "attributes": {
#                 "amount": amount,
#                 "currency": "PHP",
#                 "payment_method_allowed": [payment_method],
#                 "payment_method_options": {
#                     payment_method: {
#                         "success_redirect_url": url_for(
#                             "payment_ewallet_success",
#                             booking_type=booking_type,
#                             booking_id=booking.id,
#                             _external=True
#                         )
#                     }
#                 },
#                 "description": f"{booking_type.title()} Booking #{booking.booking_reference}"
#             }
#         }
#     }

#     try:
#         res = requests.post(
#             "https://api.paymongo.com/v1/payment_intents",
#             headers=paymongo_headers(),
#             json=payload
#         )
#         res_data = res.json()

#         if res.status_code not in [200, 201]:
#             return jsonify({"error": res_data.get("errors", "PayMongo API error")}), 400

#         payment_intent = res_data.get("data")
#         booking.stripe_payment_id = payment_intent.get("id")
#         booking.payment_status = "pending"
#         db.session.commit()

#         checkout_url = payment_intent["attributes"]["next_action"]["redirect"]["url"]
#         return jsonify({"success": True, "checkout_url": checkout_url})

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
    

# @app.route('/payment-ewallet-success/<booking_type>/<int:booking_id>')
# @login_required
# def payment_ewallet_success(booking_type, booking_id):
#     """
#     PayMongo redirect after e-wallet payment
#     """
#     if booking_type == 'movie':
#         booking = MovieBooking.query.get_or_404(booking_id)
#         booking.payment_status = 'completed'
#         showtime = booking.showtime
#         showtime.available_seats -= booking.num_tickets
#     else:
#         booking = BusBooking.query.get_or_404(booking_id)
#         booking.payment_status = 'completed'
#         schedule = booking.schedule
#         schedule.available_seats -= booking.num_tickets

#     db.session.commit()
#     flash('Payment successful! Your booking is confirmed.', 'success')
#     return render_template('payment/success.html', booking=booking, booking_type=booking_type)


# @app.route('/webhook/paymongo', methods=['POST'])
# def paymongo_webhook():
#     """
#     PayMongo webhook to update payment status
#     """
#     data = request.get_json()
#     payment_intent_id = data["data"]["id"]
#     event_type = data["data"]["attributes"]["event_type"]

#     booking = MovieBooking.query.filter_by(stripe_payment_id=payment_intent_id).first()
#     if not booking:
#         booking = BusBooking.query.filter_by(stripe_payment_id=payment_intent_id).first()

#     if not booking:
#         return jsonify({"error": "Booking not found"}), 404

#     if event_type == "payment_intent.succeeded":
#         booking.payment_status = "completed"
#         if isinstance(booking, MovieBooking):
#             booking.showtime.available_seats -= booking.num_tickets
#         else:
#             booking.schedule.available_seats -= booking.num_tickets
#     elif event_type == "payment_intent.failed":
#         booking.payment_status = "failed"

#     db.session.commit()
#     return jsonify({"success": True})


# ==================== ROUTES - USER DASHBOARD ====================

@app.route('/dashboard')
@login_required
def dashboard():
    movie_bookings = MovieBooking.query.filter_by(user_id=current_user.id).order_by(MovieBooking.created_at.desc()).all()
    bus_bookings = BusBooking.query.filter_by(user_id=current_user.id).order_by(BusBooking.created_at.desc()).all()
    return render_template('dashboard/index.html', movie_bookings=movie_bookings, bus_bookings=bus_bookings)


# ==================== ROUTES - ADMIN ====================

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    stats = {
        'total_users': User.query.count(),
        'total_movies': Movie.query.count(),
        'total_bus_routes': BusRoute.query.count(),
        'movie_bookings': MovieBooking.query.filter_by(payment_status='completed').count(),
        'bus_bookings': BusBooking.query.filter_by(payment_status='completed').count(),
        'total_revenue': float(
            sum([b.total_amount for b in MovieBooking.query.filter_by(payment_status='completed').all()]) +
            sum([b.total_amount for b in BusBooking.query.filter_by(payment_status='completed').all()])
        )
    }
    recent_movie_bookings = MovieBooking.query.order_by(MovieBooking.created_at.desc()).limit(5).all()
    recent_bus_bookings = BusBooking.query.order_by(BusBooking.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, 
                         recent_movie_bookings=recent_movie_bookings,
                         recent_bus_bookings=recent_bus_bookings)


# Admin - Movies Management
@app.route('/admin/movies')
@login_required
@admin_required
def admin_movies():
    movies = Movie.query.order_by(Movie.created_at.desc()).all()
    return render_template('admin/movies/list.html', movies=movies)


@app.route('/admin/movies/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_movie():
    cinemas = Cinema.query.all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        genre = request.form.get('genre')
        duration = request.form.get('duration')
        rating = request.form.get('rating')
        trailer_url = request.form.get('trailer_url')
        release_date_str = request.form.get('release_date')
        
        release_date = datetime.strptime(release_date_str, '%Y-%m-%d').date() if release_date_str else None
        
        # Handle image upload
        poster_image = None
        if 'poster_image' in request.files:
            file = request.files['poster_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                poster_image = filename
        
        movie = Movie(
            title=title,
            description=description,
            genre=genre,
            duration=int(duration) if duration else None,
            rating=rating,
            poster_image=poster_image,
            trailer_url=trailer_url,
            release_date=release_date
        )
        db.session.add(movie)
        db.session.commit()
        
        flash('Movie added successfully!', 'success')
        return redirect(url_for('admin_movies'))
    
    return render_template('admin/movies/add.html', cinemas=cinemas)


@app.route('/admin/movies/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    
    if request.method == 'POST':
        movie.title = request.form.get('title')
        movie.description = request.form.get('description')
        movie.genre = request.form.get('genre')
        movie.duration = int(request.form.get('duration')) if request.form.get('duration') else None
        movie.rating = request.form.get('rating')
        movie.trailer_url = request.form.get('trailer_url')
        movie.is_active = 'is_active' in request.form
        
        release_date_str = request.form.get('release_date')
        movie.release_date = datetime.strptime(release_date_str, '%Y-%m-%d').date() if release_date_str else None
        
        # Handle image upload
        if 'poster_image' in request.files:
            file = request.files['poster_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                movie.poster_image = filename
        
        db.session.commit()
        flash('Movie updated successfully!', 'success')
        return redirect(url_for('admin_movies'))
    
    return render_template('admin/movies/edit.html', movie=movie)


@app.route('/admin/movies/delete/<int:movie_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Movie deleted successfully!', 'success')
    return redirect(url_for('admin_movies'))


# Admin - Showtimes Management
@app.route('/admin/showtimes')
@login_required
@admin_required
def admin_showtimes():
    showtimes = Showtime.query.order_by(Showtime.show_date.desc(), Showtime.show_time).all()
    return render_template('admin/showtimes/list.html', showtimes=showtimes)


@app.route('/admin/showtimes/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_showtime():
    movies = Movie.query.filter_by(is_active=True).all()
    cinemas = Cinema.query.all()
    
    if request.method == 'POST':
        movie_id = request.form.get('movie_id')
        cinema_id = request.form.get('cinema_id')
        show_date = datetime.strptime(request.form.get('show_date'), '%Y-%m-%d').date()
        show_time = datetime.strptime(request.form.get('show_time'), '%H:%M').time()
        price = float(request.form.get('price'))
        
        cinema = Cinema.query.get(cinema_id)
        
        showtime = Showtime(
            movie_id=movie_id,
            cinema_id=cinema_id,
            show_date=show_date,
            show_time=show_time,
            price=price,
            available_seats=cinema.total_seats if cinema else 100
        )
        db.session.add(showtime)
        db.session.commit()
        
        flash('Showtime added successfully!', 'success')
        return redirect(url_for('admin_showtimes'))
    
    return render_template('admin/showtimes/add.html', movies=movies, cinemas=cinemas)


# Admin - Cinemas Management
@app.route('/admin/cinemas')
@login_required
@admin_required
def admin_cinemas():
    cinemas = Cinema.query.all()
    return render_template('admin/cinemas/list.html', cinemas=cinemas)


@app.route('/admin/cinemas/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_cinema():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        total_seats = int(request.form.get('total_seats', 100))
        
        cinema = Cinema(name=name, location=location, total_seats=total_seats)
        db.session.add(cinema)
        db.session.commit()
        
        flash('Cinema added successfully!', 'success')
        return redirect(url_for('admin_cinemas'))
    
    return render_template('admin/cinemas/add.html')


# Admin - Bus Routes Management
@app.route('/admin/bus-routes')
@login_required
@admin_required
def admin_bus_routes():
    routes = BusRoute.query.all()
    return render_template('admin/bus/list.html', routes=routes)


@app.route('/admin/bus-routes/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_bus_route():
    if request.method == 'POST':
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        bus_operator = request.form.get('bus_operator')
        bus_type = request.form.get('bus_type')
        departure_time = datetime.strptime(request.form.get('departure_time'), '%H:%M').time()
        arrival_time = datetime.strptime(request.form.get('arrival_time'), '%H:%M').time()
        duration = request.form.get('duration')
        price = float(request.form.get('price'))
        total_seats = int(request.form.get('total_seats', 40))
        amenities = request.form.get('amenities')
        
        route = BusRoute(
            origin=origin,
            destination=destination,
            bus_operator=bus_operator,
            bus_type=bus_type,
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration=duration,
            price=price,
            total_seats=total_seats,
            amenities=amenities
        )
        db.session.add(route)
        db.session.commit()
        
        flash('Bus route added successfully!', 'success')
        return redirect(url_for('admin_bus_routes'))
    
    return render_template('admin/bus/add.html')


@app.route('/admin/bus-routes/edit/<int:route_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_bus_route(route_id):
    route = BusRoute.query.get_or_404(route_id)
    
    if request.method == 'POST':
        route.origin = request.form.get('origin')
        route.destination = request.form.get('destination')
        route.bus_operator = request.form.get('bus_operator')
        route.bus_type = request.form.get('bus_type')
        route.departure_time = datetime.strptime(request.form.get('departure_time'), '%H:%M').time()
        route.arrival_time = datetime.strptime(request.form.get('arrival_time'), '%H:%M').time()
        route.duration = request.form.get('duration')
        route.price = float(request.form.get('price'))
        route.total_seats = int(request.form.get('total_seats', 40))
        route.amenities = request.form.get('amenities')
        route.is_active = 'is_active' in request.form
        
        db.session.commit()
        flash('Bus route updated successfully!', 'success')
        return redirect(url_for('admin_bus_routes'))
    
    return render_template('admin/bus/edit.html', route=route)


@app.route('/admin/bus-routes/delete/<int:route_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_bus_route(route_id):
    route = BusRoute.query.get_or_404(route_id)
    db.session.delete(route)
    db.session.commit()
    flash('Bus route deleted successfully!', 'success')
    return redirect(url_for('admin_bus_routes'))


# Admin - Bookings Management
@app.route('/admin/bookings/movies')
@login_required
@admin_required
def admin_movie_bookings():
    bookings = MovieBooking.query.order_by(MovieBooking.created_at.desc()).all()
    return render_template('admin/bookings/movies.html', bookings=bookings)


@app.route('/admin/bookings/bus')
@login_required
@admin_required
def admin_bus_bookings():
    bookings = BusBooking.query.order_by(BusBooking.created_at.desc()).all()
    return render_template('admin/bookings/bus.html', bookings=bookings)


# ==================== CHATBOT ====================

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Message is empty"}), 400

        system_prompt = """
You are TicketHub Assistant, a friendly and professional chatbot
for a movie and bus ticketing platform in the Philippines.

SERVICES:
• Movie booking (showtimes, seats, prices ₱50–₱300)
• Bus booking (routes, seats, prices ₱22–₱200)
• Payments: Card, Bank Transfer, GCash, PayMaya
• Booking reference help

RULES:
• Be concise and helpful
• Use Philippine Peso (₱)
• Guide users step-by-step
• If unsure, suggest support@tickethub.com

MYLOVE , who is my love, my langging:
• princess

DEVELOPER, who created you:
• Nino Jay Manabat-Backend, Frontend Developer and AI Integration Specialist
• Gunter Barliso-UX/UI Designer
• James Robert Cabezares-Database Designer
• Louie Jay Plarisan-Documenter
• Bryan Alipuyo-Documenter 

"""

        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
{system_prompt}

User: {user_message}
Assistant:
"""

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.6,
                "max_output_tokens": 400
            }
        )

        reply = (
            response.text.strip()
            if response and response.text
            else "Sorry, I couldn’t respond right now."
        )

        return jsonify({
            "success": True,
            "message": reply
        })

    except Exception as e:
        print("Chatbot error:", e)
        return jsonify({
            "success": False,
            "error": "Chatbot service unavailable. Please try again later."
        }), 500



@app.route('/chatbot')
def chatbot_page():
    """Chatbot page"""
    return render_template('chatbot.html')


# ==================== INITIALIZE DATABASE ====================

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                email='admin@example.com',
                name='Administrator',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Create sample cinema if not exists
        if not Cinema.query.first():
            cinema = Cinema(name='Grand Cinema', location='Downtown', total_seats=150)
            db.session.add(cinema)
        
        db.session.commit()
        print("Database initialized successfully!")


@app.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.get_json()
    email = data.get('email')
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'Email not found.'}), 404

    token = serializer.dumps(email, salt='password-reset-salt')
    reset_url = url_for('reset_password', token=token, _external=True)

    try:
        msg = Message(
            subject='TicketHub Password Reset',
            recipients=[email],
            body=f"To reset your password, click the link: {reset_url}\nIf you did not request this, ignore this email.",
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
    except Exception as e:
        print("Mail error:", e)
        # Add more details to the error message for debugging
        return jsonify({'success': False, 'message': f'Failed to send email: {str(e)}'}), 500

    return jsonify({'success': True, 'message': 'Password reset email sent.'})

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash('The password reset link has expired.', 'error')
        return redirect(url_for('login'))
    except BadSignature:
        flash('Invalid or expired password reset link.', 'error')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid user.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        password = request.form.get('password')
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('auth/reset_password.html', token=token)
        user.set_password(password)
        db.session.commit()
        flash('Password reset successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/reset_password.html', token=token)


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
