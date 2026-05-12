# Football Store E-commerce

> Full-stack football merchandise and match tickets e-commerce platform built with Flask and SQL Server.

---

## Overview

Football Store is a complete e-commerce solution for selling football merchandise (jerseys, accessories, equipment) and match tickets. The platform features a responsive frontend, secure backend API, and admin dashboard for management.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | HTML5, CSS3, JavaScript, Jinja2 Templates |
| **Backend** | Python 3.11+, Flask 3.x |
| **Database** | SQL Server 2022 |
| **Database Driver** | pyodbc |
| **UI Icons** | Font Awesome 6 |
| **Security** | CSRF Protection, Password Hashing, Input Validation |

---

## Project Structure

```
football-store/
|
|-- frontend/                    # Frontend contributor (@ahmed12345678996542)
|   |-- templates/              # Jinja2 HTML templates
|   |   |-- admin/              # Admin panel templates
|   |   |-- layout.html         # Base layout
|   |   |-- index.html          # Homepage
|   |   |-- products.html       # Product listing
|   |   |-- product_detail.html # Product details
|   |   |-- tickets.html        # Match tickets
|   |   |-- cart.html           # Shopping cart
|   |   |-- checkout.html       # Checkout page
|   |   |-- login.html          # User login
|   |   |-- register.html       # User registration
|   |   |-- contact.html        # Contact form
|   |   |-- admin.html          # Admin dashboard
|   |   |-- admin/coupons.html  # Coupon management
|   |   |-- admin/currencies.html # Currency management
|   |   |-- admin/reviews.html  # Review moderation
|   |   |-- admin/messages.html # User messages
|   |
|   |-- static/
|       |-- css/
|           |-- styles.css      # Main stylesheet
|           |-- contact.css     # Contact page styles
|       |-- js/
|           |-- main.js         # Client-side JavaScript
|       |-- images/             # Product images
|
|-- backend/                     # Backend contributor (@mohamed-12-tarek)
|   |-- config/
|       |-- config.py           # Environment configuration
|   |-- models/
|       |-- db.py               # Database connection
|       |-- db_coupons.py       # Coupon model
|       |-- db_currencies.py    # Currency model
|       |-- db_messages.py      # Messages model
|       |-- db_reviews.py       # Reviews model
|   |-- routes/
|       |-- contact_routes.py   # Contact form API
|       |-- currency_routes.py  # Currency API
|   |-- utils/
|       |-- currency_service.py # Currency formatting (EGP)
|       |-- csrf.py             # CSRF utilities
|       |-- email_utils.py      # Email sending
|   |-- app.py                  # Main Flask application
|
|-- templates/                   # Development (Jinja2 served by Flask)
|-- static/                      # Development (CSS, JS, images)
|-- app.py                       # Development (Flask entry point)
|-- config/                      # Development (Configuration)
|-- models/                      # Development (Database models)
|-- routes/                      # Development (API routes)
|-- utils/                       # Development (Utilities)
|
|-- db_scripts/
|   |-- currencies.sql          # Currency table schema + seed data
|   |-- user_messages.sql       # User messages table schema
|
|-- requirements.txt             # Python dependencies
|-- .env.example                # Environment variables template
|-- LICENSE                     # MIT License
|-- .gitignore                  # Git ignore rules
|-- README.md                   # This file
```

---

## Features

### Public Features
- Product catalog with category filtering
- Product detail pages with image gallery
- Match tickets listing
- Shopping cart with quantity management
- Coupon code application
- Checkout process
- User registration and login
- Contact form
- Product reviews and ratings

### Admin Features
- Dashboard with statistics
- Product management
- Ticket management
- Order tracking
- Coupon management
- Currency management (multi-currency support)
- Review moderation
- User messages inbox

### Security Features
- CSRF protection on all forms
- Password hashing (bcrypt)
- SQL injection prevention (parameterized queries)
- Input validation and sanitization
- Environment variable configuration for secrets

---

## Installation

### Prerequisites
- Python 3.11+
- SQL Server 2022 (or Express)
- pyodbc driver installed

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/mohamed-12-tarek/football-store-.git
cd football-store-
```

2. **Create virtual environment**
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Set up database**
```bash
# Run SQL scripts in SQL Server Management Studio or sqlcmd
sqlcmd -S localhost -E -i db_scripts/currencies.sql
sqlcmd -S localhost -E -i db_scripts/user_messages.sql
```

6. **Run the application**
```bash
python app.py
```

Access at: `http://127.0.0.1:5000`

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DB_SERVER` | SQL Server hostname | Yes |
| `DB_NAME` | Database name | Yes |
| `DB_USERNAME` | Database username | Yes |
| `DB_PASSWORD` | Database password | Yes |
| `ADMIN_EMAIL` | Admin login email | Yes |
| `ADMIN_PASSWORD` | Admin password | Yes |
| `SECRET_KEY` | Flask secret key | Yes |
| `DEBUG` | Debug mode (True/False) | No |
| `SMTP_SERVER` | Email SMTP server | No |
| `SMTP_PORT` | Email SMTP port | No |
| `SMTP_USERNAME` | Email username | No |
| `SMTP_PASSWORD` | Email password | No |

---

## Database Schema

### Main Tables
- `products` - Product catalog
- `tickets` - Match tickets
- `orders` - Customer orders
- `order_items` - Order line items
- `users` - User accounts
- `cart_items` - Shopping cart
- `coupons` - Discount codes
- `currencies` - Currency rates
- `user_messages` - Contact form messages
- `reviews` - Product reviews

---

## API Routes

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

### API Endpoints
| Route | Method | Description |
|-------|--------|-------------|
| `/api/currencies` | GET | List currencies |
| `/api/currencies/convert` | POST | Convert currency |
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
| `/admin/currencies/` | Currency management |
| `/admin/messages/` | User messages |

---

## Currency Support

The system uses **EGP (Egyptian Pound)** as the base currency. Additional currencies supported:
- EGP (Egyptian Pound)
- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)
- SAR (Saudi Riyal)
- AED (UAE Dirham)

Currency rates can be managed via the Admin panel at `/admin/currencies/`

---

## Default Credentials

### Admin Account
- **Email**: Configured via `ADMIN_EMAIL` env var
- **Password**: Configured via `ADMIN_PASSWORD` env var
- **Default**: `admin@gmail.com` / `changeme` (change in production!)

---

## Git Workflow

### Branches
| Branch | Purpose | Owner |
|--------|---------|-------|
| `main` | Stable code | mohamed-12-tarek |
| `frontend` | Frontend development | ahmed12345678996542 |
| `backend` | Backend development | mohamed-12-tarek |

### Frontend Contributor Workflow
```bash
git checkout frontend
git pull origin main
# Make changes in frontend/ folder
git add .
git commit -m "Updated frontend component"
git push origin frontend
# Create Pull Request on GitHub: frontend → main
```

### Backend Contributor Workflow
```bash
git checkout backend
git pull origin main
# Make changes in backend/ folder
git add .
git commit -m "Updated backend API"
git push origin backend
# Create Pull Request on GitHub: backend → main
```

---

## Contributors

| Role | Contributor |
|------|-------------|
| Frontend Developer | [@ahmed12345678996542](https://github.com/ahmed12345678996542) |
| Backend Developer | [@mohamed-12-tarek](https://github.com/mohamed-12-tarek) |

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

<div align="center">

Built with passion for football fans

</div>
