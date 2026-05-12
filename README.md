# Football Store E-commerce

> Full-stack football merchandise and match tickets e-commerce platform.

---

## Repository Structure

```
football-store/
├── frontend/          # HTML templates, CSS, JS (Frontend Contributor)
├── backend/           # Flask API, models, routes (Backend Contributor)
├── templates/         # Jinja2 templates (dev)
├── static/           # Static files (dev)
├── app.py            # Main Flask app (dev)
├── config/           # Configuration (dev)
├── models/           # Database models (dev)
├── routes/           # API routes (dev)
├── utils/           # Utilities (dev)
├── db_scripts/       # SQL scripts
├── requirements.txt  # Python dependencies
├── LICENSE          # MIT License
├── .gitignore       # Git ignore rules
└── README.md        # This file
```

---

## Contributors

| Role | Contributor |
|------|-------------|
| Frontend | [@ahmed12345678996542](https://github.com/ahmed12345678996542) |
| Backend | [@mohamed-12-tarek](https://github.com/mohamed-12-tarek) |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, JavaScript, Jinja2 |
| Backend | Python, Flask, SQL Server |
| Database | SQL Server 2022 |
| Icons | Font Awesome 6 |

---

## Quick Start

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Configure .env with your database credentials
python app.py
```

### Frontend
Access via Flask at `http://127.0.0.1:5000`

---

## Environment Variables

### Backend (.env)
```
DB_SERVER=localhost
DB_NAME=football_store
DB_USERNAME=sa
DB_PASSWORD=your_password
ADMIN_EMAIL=admin@footballstore.com
ADMIN_PASSWORD=changeme
SECRET_KEY=your-secret-key
```

---

## Git Workflow

### Branches
| Branch | Purpose | Owner |
|--------|---------|-------|
| `main` | Stable code | mohamed-12-tarek |
| `frontend` | Frontend development | ahmed12345678996542 |
| `backend` | Backend development | mohamed-12-tarek |

### Frontend Contributor
```bash
git checkout frontend
git pull
# Edit frontend/ folder
git add . && git commit -m "message"
git push origin frontend
# Create PR: frontend → main
```

### Backend Contributor
```bash
git checkout backend
git pull
# Edit backend/ folder
git add . && git commit -m "message"
git push origin backend
# Create PR: backend → main
```

---

## License

MIT License - See [LICENSE](LICENSE) file
