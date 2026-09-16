# AgriLoop Backend

Digital Agricultural Residue Platform - Backend API

## Architecture

```
backend/
+-- app/
¦   +-- main.py                 # FastAPI app entry point
¦   +-- config.py               # Pydantic Settings (env vars)
¦   +-- database.py             # SQLAlchemy engine/session
¦   +-- models/                 # SQLAlchemy models
¦   +-- schemas/                # Pydantic request/response models
¦   +-- routers/                # FastAPI route handlers
¦   +-- services/               # Business logic
¦   +-- integrations/           # External service adapters
+-- tests/
+-- alembic/                    # DB migrations
+-- data/                       # Static data files
+-- requirements.txt
+-- .env.example
+-- README.md
```

## Features

- **Bale Certificate API** - Create digital certificates with QR codes
- **Pooling API** - Assign bales to regional pools based on AI risk scores
- **Weigh Event API** - Record weigh events with verification, payment, and document generation
- **Custody Tracking** - Complete lifecycle tracking with fee calculation
- **Document Generation** - E-invoice, E-way bill, Dispatch note, Payment record
- **Payment Integration** - Razorpay (test) + Mock provider
- **E-way Bill** - Mock provider with production-ready interface
- **AI Layer Integration** - Adapter pattern for AI/Data layer
- **Minimal Auth** - Phone + OTP (mock for demo)

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 14+

### Installation

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
# Edit .env with your settings
```

Required environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` - For Razorpay (optional, uses mock if not set)

### Database

```bash
# Run migrations
alembic upgrade head
```

### Running

```bash
# Development
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Bale Certificate
- `POST /api/bale-certificate` - Create bale certificate
- `GET /api/bale/{bale_id}` - Get bale details
- `GET /api/bale/verify/{bale_id}` - QR verification endpoint

### Pooling
- `POST /api/pool` - Assign bale to pool

### Weigh Event
- `POST /api/weigh-event` - Record weigh event (triggers verification, payment, documents)

### Custody
- `GET /api/custody/{bale_id}` - Get custody timeline
- `GET /api/custody/{bale_id}/fee` - Calculate custody fee

### Documents
- `GET /api/documents/{transaction_id}` - Get transaction documents

### Auth
- `POST /api/auth/send-otp` - Send mock OTP
- `POST /api/auth/verify-otp` - Verify OTP and get token

## Demo Flow

```bash
# 1. Create bale certificate
curl -X POST http://localhost:8000/api/bale-certificate \
  -H "Content-Type: application/json" \
  -d '{
    "operator_id": "OP001",
    "farmer_id": "F001",
    "crop_type": "paddy",
    "residue_type": "paddy_straw",
    "declared_quantity_kg": 500,
    "hub_id": "HUB001",
    "latitude": 12.95,
    "longitude": 80.15
  }'

# 2. Assign pool
curl -X POST http://localhost:8000/api/pool \
  -H "Content-Type: application/json" \
  -d '{"bale_id": "BAL-2026-XXXXX"}'

# 3. Record weigh event
curl -X POST http://localhost:8000/api/weigh-event \
  -H "Content-Type: application/json" \
  -d '{
    "bale_id": "BAL-2026-XXXXX",
    "measured_weight_kg": 480,
    "moisture_percentage": 14.5,
    "density": 110,
    "operator_id": "OP002"
  }'

# 4. Get documents
curl http://localhost:8000/api/documents/TXN-XXXXXX

# 5. Get custody
curl http://localhost:8000/api/custody/BAL-2026-XXXXX
```

## Demo Mode

When `DEMO_MODE=true`:
- Mock payment provider (always succeeds)
- Mock E-way bill provider
- Mock AI risk provider (reads from `data/risk_scores.json`)
- Local PDF document generation
- Mock OTP (always 123456)

## Testing

```bash
pytest tests/ -v
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database Schema

### Core Tables
- `users` - Operators, farmers, admins
- `bales` - Residue bales with certificates
- `pools` - Regional collection pools
- `weigh_events` - Physical weigh records
- `transactions` - Commercial transactions
- `payments` - Payment records
- `documents` - Generated documents
- `custody_events` - Lifecycle tracking

## Configuration

Key settings in `.env`:
- `DATABASE_URL` - PostgreSQL connection
- `DEMO_MODE` - Enable mock providers
- `PAYMENT_PROVIDER` - `mock` or `razorpay`
- `DAILY_CUSTODY_FEE_PER_BALE` - Custody fee rate
- `MAX_WEIGHT_DEVIATION_PERCENT` - Verification threshold (default 10%)
- `REFERENCE_PRICES_JSON` - Commodity pricing

## Mock Integrations

All external integrations have mock implementations:
- `MockPaymentGateway` - Always succeeds
- `MockEWayBillProvider` - Validates payload, returns mock
- `MockAIDataProvider` - Reads from `data/risk_scores.json`

Replace with production implementations by changing config:
- `PAYMENT_PROVIDER=razorpay`
- `EWAY_BILL_PROVIDER=production`
- `AI_PROVIDER=live`

## Security

- Never commit `.env` file
- Use strong `SECRET_KEY` in production
- Configure CORS origins in production
- Use HTTPS in production
- Implement proper JWT authentication for production
