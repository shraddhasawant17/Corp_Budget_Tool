# RBL Bank — IT Budget Portal (Prototype)

## Quick Start

```bash
# 1. Virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed demo data
python seed.py

# 4. Run server
uvicorn main:app --reload

# 5. Open browser
# http://localhost:8000
```

## Demo Login Credentials

| Role       | Email                | Password  |
| ---------- | -------------------- | --------- |
| IT Head    | AmitGoel@rblbank.com | Pass@1234 |
| IT Head 2  | DeepaS@rblbank.com   | Pass@1234 |
| Admin (CA) | Madhav@rblbank.com   | Pass@1234 |
| CEO        | Raj@rblbank.com      | Pass@1234 |
| VP2        | Niki@rblbank.com     | Pass@1234 |

## What's Built

- Login with JWT cookie auth (3 roles)
- Budget entry form (5-step wizard with live calculations)
- Budget lines table (role-filtered)
- 3-level approval flow (IT Head → Admin → CEO)
- Dashboard with KPI cards + charts
- Dark/Light mode toggle
- Dummy1 & Dummy2 tables (future features placeholder)
- Swagger docs at /docs

## Folder Structure

```
rbl-budget-portal/
├── main.py              ← FastAPI app entry point
├── seed.py              ← Demo data script
├── requirements.txt
└── app/
    ├── database.py      ← SQLite connection
    ├── models.py        ← DB tables (5 tables)
    ├── schemas.py       ← Pydantic validation
    ├── auth.py          ← JWT + password hashing
    ├── routers/
    │   ├── auth_router.py
    │   ├── budget_router.py
    │   ├── approval_router.py
    │   ├── dashboard_router.py
    │   └── dummy_router.py
    ├── templates/
    │   ├── base.html
    │   ├── auth/login.html
    │   ├── dashboard/index.html
    │   ├── budget/form.html
    │   ├── budget/list.html
    │   └── approval/index.html
    └── static/
        ├── css/style.css
        └── js/main.js
```
