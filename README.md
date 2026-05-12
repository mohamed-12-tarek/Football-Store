# Football Store E-commerce

> Full-stack football merchandise and match tickets e-commerce platform.

---

## Repository Structure

This is a **monorepo** with two main components:

```
football-store/
├── frontend/     → Managed by @ahmed12345678996542
├── backend/      → Managed by @mohamed-12-tarek
├── LICENSE
└── README.md
```

---

## Contributors

| Component | Contributor |
|-----------|-------------|
| Frontend (UI/UX) | [@ahmed12345678996542](https://github.com/ahmed12345678996542) |
| Backend (API/DB) | [@mohamed-12-tarek](https://github.com/mohamed-12-tarek) |

---

## Quick Start

### Frontend
```bash
cd frontend
# Open templates/index.html in browser
# Or serve with Flask from backend folder
```

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python app.py
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, JavaScript, Jinja2 |
| Backend | Python, Flask, SQL Server |
| Database | SQL Server 2022 |
| Icons | Font Awesome 6 |

---

## Git Workflow

This project uses **branch-based workflow** with Pull Requests.

### Branches

| Branch | Purpose | Owner |
|--------|---------|-------|
| `main` | Stable code | mohamed-12-tarek |
| `frontend` | Frontend development | ahmed12345678996542 |
| `backend` | Backend development | mohamed-12-tarek |

### How to Contribute

#### Frontend Contributor (@ahmed12345678996542)
```bash
# Clone the repo
git clone https://github.com/mohamed-12-tarek/football-store-.git
cd football-store-

# Switch to frontend branch
git checkout frontend

# Make changes in frontend/ folder
# Edit templates, static/css, static/js

# Commit and push
git add .
git commit -m "Your message"
git push origin frontend

# Create Pull Request on GitHub
# PR: frontend → main
```

#### Backend Contributor (@mohamed-12-tarek)
```bash
# Clone the repo
git clone https://github.com/mohamed-12-tarek/football-store-.git
cd football-store-

# Switch to backend branch
git checkout backend

# Make changes in backend/ folder
# Edit app.py, models, routes, utils

# Commit and push
git add .
git commit -m "Your message"
git push origin backend

# Create Pull Request on GitHub
# PR: backend → main
```

### Review & Merge
1. Create Pull Request on GitHub
2. Review changes
3. Merge to `main` after approval

---

## License

MIT License
