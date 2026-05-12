# ⚽ Football Store - Frontend

> The frontend client for the Football Store e-commerce platform built with HTML5, CSS3, and Vanilla JavaScript.

[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

---

## 📖 Overview

This is the **frontend client** for Football Store. It communicates with the backend API to provide:

- **Product Catalog**: Browse merchandise with category filtering
- **Match Tickets**: View and purchase tickets
- **Shopping Cart**: Full cart management
- **User Authentication**: Login and registration
- **Admin Dashboard**: Manage products, tickets, and orders
- **Reviews System**: Product ratings and reviews
- **Responsive Design**: Mobile-friendly interface

---

## 🎨 Tech Stack

| Technology | Purpose |
|-----------|---------|
| **HTML5** | Semantic markup |
| **CSS3** | Styling with custom properties |
| **Vanilla JavaScript** | Client-side interactivity |
| **Jinja2** | Template engine |
| **Font Awesome 6** | Icon library |
| **Flask** | Backend server (required) |

---

## 📁 Project Structure

```
frontend/
├── templates/              # HTML templates (Jinja2)
│   ├── layout.html         # Base layout
│   ├── index.html         # Homepage
│   ├── products.html      # Product listing
│   ├── product_detail.html # Product details
│   ├── tickets.html       # Match tickets
│   ├── cart.html          # Shopping cart
│   ├── checkout.html      # Checkout
│   ├── login.html         # Login
│   ├── register.html      # Registration
│   ├── contact.html       # Contact
│   ├── admin.html         # Admin dashboard
│   └── admin/             # Admin sub-pages
├── static/                # Static assets
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript
│   └── images/            # Images
└── README.md              # This file
```

---

## 🚀 Getting Started

### Prerequisites

- **Backend Server**: This frontend requires the backend server to be running
- **Web Browser**: Any modern browser

### Installation

1. **Clone this repository**
```bash
git clone https://github.com/YOUR_USERNAME/football-store-frontend.git
cd football-store-frontend
```

2. **Configure Backend URL**

In `static/js/main.js`, update the API base URL if needed:
```javascript
const API_BASE_URL = 'http://localhost:5000';
```

3. **No additional dependencies needed** - Pure static frontend!

### Running with Backend

1. Start the backend server (see [football-store-backend](https://github.com/YOUR_USERNAME/football-store-backend))
2. Open `templates/index.html` in browser, OR
3. Use Flask to serve templates:
```bash
# From backend folder
export FLASK_APP=app.py
flask run
```

---

## 📱 Features

### Public Pages
- [x] Homepage with featured products
- [x] Product catalog with filters
- [x] Product detail with gallery
- [x] Match tickets listing
- [x] Shopping cart
- [x] Checkout flow
- [x] User login/registration
- [x] Contact form

### Admin Pages
- [x] Dashboard with statistics
- [x] Product management
- [x] Ticket management
- [x] Order tracking
- [x] Review moderation
- [x] Coupon management
- [x] Currency management
- [x] User messages

---

## 🎨 Design System

### Colors
```css
--cetacean-blue: #001440;    /* Primary */
--dark-blue: #00008b;        /* Secondary */
--hyacinth: #b660cd;         /* Accent */
--purple-shade: #800080;     /* Highlight */
--white: #ffffff;
--light-gray: #f8f9fa;
```

### Typography
- Font Family: Segoe UI, Tahoma, Geneva, Verdana, sans-serif
- Responsive font sizes
- Consistent spacing scale

---

## 📦 Static Assets

| Folder | Contents |
|--------|----------|
| `css/` | styles.css, contact.css |
| `js/` | main.js (cart, checkout, forms) |
| `images/` | Placeholder images |

---

## 🔗 API Integration

The frontend communicates with the backend via REST API:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/add-to-cart` | POST | Add item to cart |
| `/update-cart` | POST | Update cart quantity |
| `/remove-from-cart/<key>` | GET | Remove item |
| `/apply-coupon` | POST | Apply discount |
| `/place-order` | POST | Create order |
| `/login` | POST | User authentication |
| `/register` | POST | User registration |

---

## 🌐 Deployment

### Option 1: Static Hosting (Netlify, Vercel, GitHub Pages)

1. Build templates with absolute API URLs
2. Deploy static files
3. Set `API_BASE_URL` to production backend

### Option 2: Same Server as Backend

```bash
# Backend automatically serves static files
# Access at http://your-domain.com
```

---

## 🤝 Related Projects

| Repository | Description |
|------------|-------------|
| [football-store-backend](https://github.com/YOUR_USERNAME/football-store-backend) | Flask backend API |

---

## 📄 License

MIT License - See [LICENSE](../LICENSE)

---

## 👤 Author

**Football Store Team**
- GitHub: [github.com/YOUR_USERNAME](https://github.com/YOUR_USERNAME)
- Email: team@footballstore.com

---

<div align="center">

**Built with ❤️ for football fans**

</div>
