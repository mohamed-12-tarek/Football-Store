# Football Store Backend API

> The backend API for the Football Store e-commerce platform built with Flask and SQL Server.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-2022-CC2927?style=flat&logo=microsoft-sql-server&logoColor=white)](https://www.microsoft.com/en-us/sql-server)

---

## Overview

This is the **backend API** for Football Store. It provides:

- **REST API**: JSON endpoints for frontend communication
- **Authentication**: User login/registration with session management
- **Database**: SQL Server with pyodbc driver
- **Security**: CSRF protection, password hashing, input validation
- **Business Logic**: Cart, orders, coupons, currencies
- **Admin Panel**: Full admin dashboard with reports

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | Flask 3.x |
| **Database** | SQL Server 2022 |
| **Driver** | pyodbc |
| **Templates** | Jinja2 |
| **Security** | CSRF tokens, password hashing |
| **Utilities** | Flask-WTF, email-utils |

---

## Project Structure

```
backend/
├── app.py                 # Main Flask application
├── config/
│   └── config.py          # Environment configuration
├── models/
│   ├── db.py              # Database connection
│   ├── db_coupons.py       # Coupon management
│   ├── db_currencies.py    # Currency rates
│   ├── db_messages.py      # User messages
│   └── db_reviews.py       # Product reviews
├── routes/
│   ├── contact_routes.py   # Contact form API
│   └── currency_routes.py  # Currency API
├── utils/
│   ├── currency_service.py # Currency formatting
│   ├── csrf.py             # CSRF utilities
│   └── email_utils.py      # Email sending
├── db_scripts/
│   ├── currencies.sql      # Currency schema
│   └── schema.sql          # Database schema
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- SQL Server 2022 (or Express)
- Database credentials

### Installation

1. **Clone this repository**
```bash
git clone https://github.com/YOUR_USERNAME/football-store-backend.git
cd football-store-backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Set up database**
```bash
# Run SQL scripts in db_scripts/ folder
sqlcmd -S localhost -E -i db_scripts/schema.sql
sqlcmd -S localhost -E -i db_scripts/currencies.sql
```

6. **Run the server**
```bash
python app.py
```

Server runs at `http://127.0.0.1:5000`

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_SERVER` | SQL Server hostname | `localhost` |
| `DB_USERNAME` | Database username | `sa` |
| `DB_PASSWORD` | Database password | `YourPassword123` |
| `DB_NAME` | Database name | `football_store` |
| `ADMIN_EMAIL` | Admin login email | `admin@footballstore.com` |
| `ADMIN_PASSWORD` | Admin password | `changeme` |
| `SECRET_KEY` | Flask secret key | `your-secret-key` |

---

## API Endpoints

### Public Routes
| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Homepage |
| `/products` | GET | Product listing |
| `/product/<id>` | GET | Product details |
| `/tickets` | GET | Match tickets |
| `/cart` | GET | Shopping cart |
| `/checkout` | GET/POST | Checkout |
| `/login` | GET/POST | User login |
| `/register` | GET/POST | User registration |
| `/contact` | GET/POST | Contact form |

### API Routes
| Route | Method | Description |
|-------|--------|-------------|
| `/api/currencies` | GET | List currencies |
| `/api/currencies/convert` | POST | Convert amount |
| `/api/contact` | POST | Submit message |

### Admin Routes
| Route | Description |
|-------|-------------|
| `/admin/` | Admin dashboard |
| `/admin/products/` | Manage products |
| `/admin/tickets/` | Manage tickets |
| `/admin/orders/` | View orders |
| `/admin/reviews/` | Moderate reviews |
| `/admin/coupons/` | Manage coupons |
| `/admin/currencies/` | Currency manager |
| `/admin/messages/` | User messages |

---

## Related Projects

| Repository | Description |
|------------|-------------|
| [football-store-frontend](https://github.com/YOUR_USERNAME/football-store-frontend) | React frontend client |

---

## License

MIT License - See [LICENSE](../LICENSE)
