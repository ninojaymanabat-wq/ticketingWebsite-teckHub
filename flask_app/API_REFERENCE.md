# TicketHub Payment API Reference

## Base URL
```
http://localhost:5000
https://yourdomain.com (production)
```

## Authentication
All endpoints require the user to be logged in (Flask-Login session).

---

## Payment Endpoints

### 1. Payment Page
**GET** `/payment/<booking_type>/<booking_id>`

Displays the payment checkout page.

**Parameters:**
- `booking_type` (string): 'movie' or 'bus'
- `booking_id` (integer): ID of the booking

**Response:**
- Returns HTML payment checkout page
- Status: 200 OK
- Status: 404 if booking not found
- Status: 302 redirect to login if not authenticated

**Example:**
```
GET /payment/movie/42
GET /payment/bus/15
```

---

### 2. Create PayMongo Source
**POST** `/create-paymongo-source`

Creates a PayMongo payment source for e-wallet payments.

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "booking_type": "movie",
  "booking_id": 42,
  "payment_method": "gcash"
}
```

**Parameters:**
- `booking_type` (string, required): 'movie' or 'bus'
- `booking_id` (integer, required): Booking ID
- `payment_method` (string, required): 'gcash' or 'paymaya'

**Response Success (201):**
```json
{
  "sourceId": "src_test_1234567890",
  "redirectUrl": "https://checkout.paymongo.com/source/src_test_1234567890"
}
```

**Response Error (400):**
```json
{
  "error": "Failed to create payment source"
}
```

**Status Codes:**
- `200`: Success - source created, redirect URL provided
- `400`: Bad request - invalid payment method or missing parameters
- `403`: Forbidden - user doesn't own this booking
- `404`: Not found - booking doesn't exist

**Example Request:**
```bash
curl -X POST http://localhost:5000/create-paymongo-source \
  -H "Content-Type: application/json" \
  -d '{
    "booking_type": "movie",
    "booking_id": 42,
    "payment_method": "gcash"
  }'
```

**Example Response:**
```json
{
  "sourceId": "src_test_abcd1234",
  "redirectUrl": "https://checkout.paymongo.com/source/src_test_abcd1234"
}
```

---

### 3. Payment Success Page
**GET** `/payment-success/<booking_type>/<booking_id>`

Displays receipt and confirms payment completion.

**Parameters:**
- `booking_type` (string): 'movie' or 'bus'
- `booking_id` (integer): ID of the booking
- `source_id` (string, optional): PayMongo source ID for verification

**Query Parameters:**
```
?source_id=src_test_1234567890
```

**Response:**
- Returns HTML receipt page
- Status: 200 OK
- Updates payment status in database
- Decreases available seats if payment successful

**Database Changes:**
- Sets `payment_status` to 'completed' or 'pending'
- Records `payment_method` ('gcash' or 'paymaya')
- Records `payment_reference` (source ID)
- Decreases `available_seats` on booking's event

**Example:**
```
GET /payment-success/movie/42?source_id=src_test_1234567890
GET /payment-success/bus/15
```

---

### 4. Get Booked Seats (Movie)
**POST** `/get-booked-seats`

Returns list of already booked seats for a movie showtime.

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "showtime_id": 123
}
```

**Parameters:**
- `showtime_id` (integer, required): Movie showtime ID

**Response:**
```json
{
  "booked_seats": ["A1", "A2", "A5", "B1", "B3"]
}
```

**Status Codes:**
- `200`: Success - returns booked seats array

**Example:**
```bash
curl -X POST http://localhost:5000/get-booked-seats \
  -H "Content-Type: application/json" \
  -d '{"showtime_id": 123}'
```

---

### 5. Get Booked Seats (Bus)
**POST** `/get-booked-bus-seats`

Returns list of already booked seats for a bus schedule.

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "schedule_id": 456
}
```

**Parameters:**
- `schedule_id` (integer, required): Bus schedule ID

**Response:**
```json
{
  "booked_seats": ["1", "2", "5", "8", "10"]
}
```

**Status Codes:**
- `200`: Success - returns booked seats array

---

### 6. Payment E-Wallet Pending
**POST** `/payment-ewallet-pending`

Records pending e-wallet payment (legacy/fallback).

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "booking_type": "movie",
  "booking_id": 42,
  "payment_method": "gcash",
  "reference_number": "GCASH-260125-1234"
}
```

**Parameters:**
- `booking_type` (string): 'movie' or 'bus'
- `booking_id` (integer): Booking ID
- `payment_method` (string): 'gcash' or 'paymaya'
- `reference_number` (string, optional): User's transaction reference

**Response:**
```json
{
  "success": true,
  "reference_number": "GCASH-260125-1234"
}
```

**Status Codes:**
- `200`: Payment recorded as pending
- `403`: Unauthorized - user doesn't own booking
- `404`: Booking not found

---

## PayMongo API Integration (Backend)

### Authentication
All PayMongo API calls use Basic Auth:
```
Authorization: Basic {base64_encode(SECRET_KEY + ':')}
```

### Create Source Request
**Endpoint:** `https://api.paymongo.com/v1/sources`

**Method:** POST

**Headers:**
```json
{
  "Authorization": "Basic {auth_string}",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "data": {
    "attributes": {
      "amount": 42000,
      "currency": "PHP",
      "type": "gcash",
      "redirect": {
        "success": "http://localhost:5000/payment-success/movie/42",
        "failed": "http://localhost:5000/payment/movie/42"
      }
    }
  }
}
```

**Response:**
```json
{
  "data": {
    "id": "src_test_abcd1234",
    "type": "source",
    "attributes": {
      "amount": 42000,
      "currency": "PHP",
      "type": "gcash",
      "status": "pending",
      "redirect": {
        "checkout_url": "https://checkout.paymongo.com/source/src_test_abcd1234",
        "success": "http://localhost:5000/payment-success/movie/42",
        "failed": "http://localhost:5000/payment/movie/42"
      }
    }
  }
}
```

### Verify Source Status
**Endpoint:** `https://api.paymongo.com/v1/sources/{source_id}`

**Method:** GET

**Headers:**
```json
{
  "Authorization": "Basic {auth_string}"
}
```

**Response:**
```json
{
  "data": {
    "id": "src_test_abcd1234",
    "attributes": {
      "status": "chargeable",
      "amount": 42000,
      "type": "gcash"
    }
  }
}
```

**Status Values:**
- `chargeable` - Payment successful, ready to charge
- `pending` - Payment in progress
- `failed` - Payment failed or cancelled

---

## Error Handling

### Common Error Responses

**401 Unauthorized**
```json
{
  "error": "Login required"
}
```

**403 Forbidden**
```json
{
  "error": "Unauthorized"
}
```

**404 Not Found**
```json
{
  "error": "Booking not found"
}
```

**400 Bad Request**
```json
{
  "error": "Failed to create payment source"
}
```

**500 Server Error**
```json
{
  "error": "Internal server error"
}
```

---

## Data Models

### Booking Object (Movie)

```python
{
  "id": 42,
  "user_id": 1,
  "showtime_id": 5,
  "num_tickets": 2,
  "seat_numbers": "A1,A2",
  "total_amount": 420.00,
  "payment_status": "completed",
  "payment_method": "gcash",
  "payment_reference": "src_test_abcd1234",
  "booking_reference": "ABC1234XYZ",
  "created_at": "2026-01-25T10:30:00"
}
```

### Booking Object (Bus)

```python
{
  "id": 15,
  "user_id": 1,
  "schedule_id": 3,
  "num_tickets": 1,
  "seat_numbers": "5",
  "passenger_names": "John Doe",
  "total_amount": 500.00,
  "payment_status": "completed",
  "payment_method": "paymaya",
  "payment_reference": "src_test_xyz9876",
  "booking_reference": "BUS1234ABC",
  "created_at": "2026-01-25T11:45:00"
}
```

### Showtime Object

```python
{
  "id": 5,
  "movie_id": 1,
  "cinema_id": 2,
  "show_date": "2026-02-15",
  "show_time": "19:00",
  "price": 210.00,
  "available_seats": 45
}
```

### Bus Schedule Object

```python
{
  "id": 3,
  "route_id": 2,
  "travel_date": "2026-02-20",
  "available_seats": 35
}
```

---

## Payment Flow

### Complete Payment Flow Diagram

```
1. User selects booking
   ↓
2. User visits /payment/movie/42
   ↓ (Displays checkout page)
   ↓
3. User selects payment method (GCash/PayMaya)
   ↓
4. User clicks "Proceed to Payment"
   ↓
5. Frontend calls POST /create-paymongo-source
   ↓
6. Backend creates PayMongo source
   ↓
7. Backend returns redirectUrl
   ↓
8. Frontend redirects user to PayMongo checkout
   ↓
9. User completes payment at PayMongo
   ↓
10. PayMongo redirects to /payment-success/movie/42
    ↓
11. Backend verifies payment status with PayMongo
    ↓
12. Backend updates database:
    - payment_status = 'completed'
    - available_seats decreased
    ↓
13. User sees receipt page
    ↓
14. User can download/print receipt
```

---

## Integration Examples

### JavaScript (Frontend)

```javascript
async function createPayment() {
  const response = await fetch('/create-paymongo-source', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      booking_type: 'movie',
      booking_id: 42,
      payment_method: 'gcash'
    })
  });
  
  const data = await response.json();
  
  if (data.redirectUrl) {
    window.location.href = data.redirectUrl;
  } else {
    alert('Error: ' + data.error);
  }
}
```

### Python (Backend Webhook - Future)

```python
@app.route('/paymongo-webhook', methods=['POST'])
def paymongo_webhook():
    payload = request.get_json()
    source_id = payload.get('data', {}).get('id')
    status = payload.get('data', {}).get('attributes', {}).get('status')
    
    # Update booking based on status
    if status == 'chargeable':
        # Mark payment as completed
        pass
    
    return jsonify({'success': True})
```

---

## Rate Limiting

- No built-in rate limiting (implement as needed)
- PayMongo API rate limits: 100 requests/second

---

## Pagination

Not applicable for payment endpoints (no list endpoints).

---

## Versioning

**Current API Version:** 1.0  
**PayMongo API Version:** v1  
**Last Updated:** January 2026

---

## Support

For PayMongo API documentation:
https://www.paymongo.com/docs

For this API documentation:
- Create GitHub issue
- Email: support@tickethub.com

---

**Status:** Production Ready ✅
