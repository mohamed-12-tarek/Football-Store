<div align="center">

<img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white" />
<img src="https://img.shields.io/badge/SQL_Server-2022-CC2927?style=for-the-badge&logo=microsoftsqlserver&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge" />

<br>
<br>

# ⚽ Football Store

### Full-Stack E-Commerce Platform for Football Merchandise & Match Tickets

*A modern web application for browsing football products, managing orders, and purchasing match tickets.*

<br>

[![Features](https://img.shields.io/badge/Explore-Features-2563eb?style=flat-square)](#features)
[![Tech Stack](https://img.shields.io/badge/View-Tech%20Stack-7c3aed?style=flat-square)](#tech-stack)
[![Getting Started](https://img.shields.io/badge/Setup-Getting%20Started-16a34a?style=flat-square)](#getting-started)
[![API](https://img.shields.io/badge/API-Reference-f97316?style=flat-square)](#api-reference)

</div>

---

## Overview

Football Store is a production-ready e-commerce solution built with Flask and SQL Server. It supports product browsing, match ticket booking, cart management, coupon codes, multi-currency display, product reviews, and a full-featured admin dashboard.

---

## Features

### Storefront
| Feature | Details |
|---|---|
| Product Catalog | Category filtering, search, low-stock badges, image galleries |
| Match Tickets | Upcoming matches with date, stadium, seat info |
| Shopping Cart | Session-based cart with quantity updates |
| Coupon Codes | Percentage & fixed discounts, expiry, usage limits |
| Checkout | Shipping form, order summary, order number generation |
| Reviews | Star ratings, moderation workflow (Pending → Approved) |
| Contact Form | Message inbox with admin reply & email notification |

### Admin Dashboard
| Feature | Details |
|---|---|
| Product Manager | Add/edit products, multi-image upload & reorder (up to 6 images) |
| Ticket Manager | Create match entries with seat/price info |
| Order Tracker | Recent orders table with status badges |
| Coupon Manager | Create, activate/deactivate, set limits & expiry |
| Currency Manager | Add currencies, set exchange rates, designate base currency |
| Review Moderation | Approve / reject / delete customer reviews |
| Messages Inbox | View & reply to contact form submissions |

### Security
- CSRF protection on all forms
- Passwords hashed with `bcrypt` (Werkzeug)
- Parameterized SQL queries (no raw string interpolation)
- Admin routes gated by session flag
- Secret key via environment variable (raises on missing)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | Flask 3.x |
| Database | SQL Server 2022 (pyodbc) |
| Templating | Jinja2 |
| Auth | Werkzeug password hashing |
| Email | Flask-Mail (SMTP/SSL) |
| Icons | Font Awesome 6 |
| Frontend | Vanilla JS, CSS3 (no build step) |

---

## Getting Started

### Prerequisites

- Python 3.11+
- SQL Server 2022 (or Express edition)
- [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/mohamed-12-tarek/football-store-.git
cd football-store-
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**
```bash
cp .env.example .env
```

Open `.env` and fill in your values (see [Environment Variables](#environment-variables) below).

**5. Initialise the database**

Run the provided SQL scripts against your SQL Server instance:

```bash
sqlcmd -S localhost -E -i db_scripts/currencies.sql
sqlcmd -S localhost -E -i db_scripts/user_messages.sql
```

> The app auto-detects the existing schema on first boot and will create the admin user defined in your `.env`.

**6. Start the development server**
```bash
python app.py
```

Visit **http://127.0.0.1:5000**

---

## Environment Variables

Copy `.env.example` to `.env` and populate every required field.

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | — | Flask session secret (any long random string) |
| `DB_SERVER` | ✅ | `localhost` | SQL Server hostname or IP |
| `DB_DATABASE` | ✅ | `FootballStoreDB` | Target database name |
| `DB_USERNAME` | ✅ | — | SQL Server login (leave blank for Windows Auth) |
| `DB_PASSWORD` | ✅ | — | SQL Server password |
| `ADMIN_EMAIL` | ✅ | `admin@example.com` | Admin account email |
| `ADMIN_PASSWORD` | ✅ | `changeme` | Admin account password — **change in production** |
| `DB_DRIVER` | ❌ | `{ODBC Driver 17 for SQL Server}` | pyodbc driver string |
| `FLASK_DEBUG` | ❌ | `false` | Set `true` for hot-reload during development |
| `MAIL_SERVER` | ❌ | `smtp.gmail.com` | SMTP hostname |
| `MAIL_PORT` | ❌ | `465` | SMTP port |
| `MAIL_USE_SSL` | ❌ | `true` | Use SSL (set `false` if using STARTTLS) |
| `MAIL_USE_TLS` | ❌ | `false` | Use STARTTLS instead of SSL |
| `MAIL_USERNAME` | ❌ | — | SMTP login |
| `MAIL_PASSWORD` | ❌ | — | SMTP password / app password |
| `MAIL_DEFAULT_SENDER` | ❌ | — | From-address for outgoing emails |

> Email features degrade gracefully — orders still complete even if SMTP is not configured.

---

## Project Structure

```
football-store/
│
├── app.py                        # Flask application entry point
│
├── config/
│   └── config.py                 # Environment-based configuration class
│
├── models/
│   ├── db.py                     # Connection factory & schema initialisation
│   ├── db_coupons.py             # Coupon CRUD (Marketing schema)
│   ├── db_currencies.py          # Currency CRUD & exchange-rate helpers
│   ├── db_messages.py            # Contact message CRUD (Users schema)
│   └── db_reviews.py             # Product review CRUD (Products schema)
│
├── routes/
│   ├── contact_routes.py         # /contact  &  /admin/messages  blueprints
│   └── currency_routes.py        # /admin/currencies  blueprint
│
├── utils/
│   ├── csrf.py                   # Token generation & validation decorators
│   ├── currency_service.py       # Conversion, formatting, cart totals
│   └── email_utils.py            # SMTP send helper (Flask-independent)
│
├── templates/
│   ├── layout.html               # Base layout (navbar, flash, footer)
│   ├── index.html                # Homepage
│   ├── products.html             # Product listing + sidebar filters
│   ├── product_detail.html       # Product detail, gallery, reviews
│   ├── tickets.html              # Match ticket listing
│   ├── cart.html                 # Shopping cart
│   ├── checkout.html             # Checkout + coupon
│   ├── login.html                # Login form
│   ├── register.html             # Registration form
│   ├── contact.html              # Contact form
│   ├── admin.html                # Admin dashboard
│   └── admin/
│       ├── coupons.html          # Coupon manager
│       ├── currencies.html       # Currency manager
│       ├── currency_form.html    # Add/Edit currency form
│       ├── reviews.html          # Review moderation
│       ├── messages.html         # Message inbox
│       └── message_detail.html   # Message detail + reply
│
├── static/
│   ├── css/
│   │   ├── styles.css            # Global stylesheet (CSS variables, components)
│   │   └── contact.css           # Contact page overrides
│   ├── js/
│   │   └── main.js               # Cart, notifications, scroll effects
│   ├── images/                   # Static image assets
│   └── uploads/
│       └── products/             # Admin-uploaded product images (runtime)
│
├── db_scripts/
│   ├── currencies.sql            # currencies table DDL + seed data (EGP base)
│   └── user_messages.sql         # user_messages table DDL
│
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
├── .gitignore
└── LICENSE
```

---

## Database Schema

The application uses SQL Server with the following schemas:

| Schema | Tables |
|---|---|
| `Products` | `products`, `categories`, `brands`, `product_images`, `product_reviews` |
| `Tickets` | `tickets`, `matches` |
| `Orders` | `orders`, `order_items` |
| `Users` | `users`, `user_messages` |
| `Core` | `addresses` |
| `Marketing` | `coupons` |
| `dbo` | `currencies` |

---

## API Reference

### Public Routes

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Homepage (featured products, upcoming matches) |
| `GET` | `/products` | Product listing with category & search filters |
| `GET` | `/product/<id>` | Product detail, gallery, reviews |
| `GET` | `/tickets` | Upcoming match tickets |
| `GET` | `/cart` | Shopping cart |
| `GET/POST` | `/checkout` | Checkout page / place order |
| `GET/POST` | `/login` | User login |
| `GET/POST` | `/register` | User registration |
| `GET` | `/logout` | Clear session |
| `GET/POST` | `/contact` | Contact form |

### JSON API

| Method | Route | Description |
|---|---|---|
| `POST` | `/add-to-cart` | Add product or ticket to cart |
| `POST` | `/update-cart` | Update item quantity |
| `GET` | `/remove-from-cart/<key>` | Remove item from cart |
| `POST` | `/apply-coupon` | Validate & apply coupon code |
| `POST` | `/remove-coupon` | Remove applied coupon |
| `POST` | `/place-order` | Submit order (requires login) |
| `POST` | `/product/<id>/reviews` | Submit product review |
| `GET` | `/api/currencies` | List active currencies |
| `POST` | `/api/currencies/convert` | Convert amount between currencies |

### Admin Routes (login + `is_admin` required)

| Method | Route | Description |
|---|---|---|
| `GET` | `/admin` | Dashboard — stats, recent orders, media manager |
| `POST` | `/admin/add-product` | Create product |
| `POST` | `/admin/add-ticket` | Create match ticket |
| `GET/POST` | `/admin/coupons` | List coupons / create coupon |
| `POST` | `/admin/coupons/<id>` | Update coupon |
| `GET` | `/admin/reviews` | Review list (filterable by status) |
| `POST` | `/admin/reviews/<id>/status` | Update review status |
| `DELETE` | `/admin/reviews/<id>` | Delete review |
| `GET/POST/DELETE` | `/admin/products/<id>/images` | Get / upload / delete product images |
| `POST` | `/admin/products/<id>/images/reorder` | Reorder product images |
| `GET/POST` | `/admin/currencies/` | List / add currencies |
| `GET/POST` | `/admin/currencies/edit/<id>` | Edit currency |
| `POST` | `/admin/currencies/delete/<id>` | Delete currency |
| `POST` | `/admin/currencies/set-base/<id>` | Set base currency |
| `GET` | `/admin/messages` | Contact message inbox |
| `GET/POST` | `/admin/messages/<id>` | View message / send reply |
| `GET` | `/admin/test-db` | Database connectivity diagnostic |

---

## Currency System

All prices are **stored and processed in EGP (Egyptian Pound)** as the base currency. Additional currencies are display-only and converted using rates maintained in the admin panel.

Supported out of the box:

| Currency | Code | Default Rate |
|---|---|---|
| Egyptian Pound | EGP | 1.000000 (base) |
| US Dollar | USD | 0.032000 |
| Euro | EUR | 0.027000 |
| British Pound | GBP | 0.023000 |
| Saudi Riyal | SAR | 0.008500 |
| UAE Dirham | AED | 0.008700 |

Exchange rates can be updated anytime at `/admin/currencies/`.

---

## Git Workflow

| Branch | Purpose | Owner |
|---|---|---|
| `main` | Stable, production-ready code | @mohamed-12-tarek |
| `frontend` | Frontend development | @ahmed12345678996542 |
| `backend` | Backend development | @mohamed-12-tarek |

**Frontend contributors:**
```bash
git checkout frontend
git pull origin main
# work inside templates/ and static/
git add . && git commit -m "feat: <description>"
git push origin frontend
# open Pull Request: frontend → main
```

**Backend contributors:**
```bash
git checkout backend
git pull origin main
# work inside models/, routes/, utils/, app.py
git add . && git commit -m "feat: <description>"
git push origin backend
# open Pull Request: backend → main
```

---

## Default Admin Credentials

| Field | Value |
|---|---|
| Email | set via `ADMIN_EMAIL` env var |
| Password | set via `ADMIN_PASSWORD` env var |
| Fallback | `admin@example.com` / `changeme` |

> ⚠️ Always override the fallback credentials via environment variables before deploying.

---

## Contributors

<table align="center">
  <tr>
    <td align="center">
      <a href="https://github.com/mohamed-12-tarek">
        <img src="https://github.com/mohamed-12-tarek.png" width="150" style="border-radius:50%"/><br/>
        <sub>mohamed-12-tarek</sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/ahmed12345678996542">
        <img src="https://github.com/ahmed12345678996542.png" width="150" style="border-radius:50%"/><br/>
        <sub>Mo-Bassem</sub>
      </a>
    </td>
  </tr>
</table>

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for full terms.

---

<div align="center">

Built with ❤️ for football fans · © 2024 EROR404 Team

</div>
