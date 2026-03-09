# 💼 JobBoard — Job Board Platform

A simple but production-grade job board built with **FastAPI**, **SQLite**, and **Bootstrap 5**.

---

## Features
- User registration & login (JWT via cookies)
- Role-based: **Recruiter** and **Job Seeker**
- Recruiter: create, edit, delete job listings
- Job Seeker: browse, search, filter, apply
- Tag-based search and keyword filtering
- Pagination on job listings
- Company profiles
- SQLite database (no setup needed)

---

## Tech Stack
| Layer     | Technology          |
|-----------|---------------------|
| Backend   | FastAPI             |
| Database  | SQLite + SQLAlchemy |
| Auth      | JWT (PyJWT)         |
| Frontend  | Jinja2 + Bootstrap 5|

---

## How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the server
```bash
uvicorn main:app --reload
```

### 3. Open in browser
```
http://localhost:8000
```

---

## Project Structure
```
jobboard/
├── main.py           # All routes
├── models.py         # Database models
├── database.py       # DB setup
├── auth.py           # Password hashing & JWT
├── requirements.txt
└── templates/        # HTML templates
    ├── base.html
    ├── home.html
    ├── login.html
    ├── register.html
    ├── jobs.html
    ├── job_detail.html
    ├── job_form.html
    ├── companies.html
    ├── company_detail.html
    ├── company_form.html
    ├── dashboard_recruiter.html
    ├── dashboard_seeker.html
    └── my_applications.html
```

---

## Usage

### Recruiter
1. Register as **Recruiter**
2. Go to Dashboard → Add Company
3. Post jobs with tags, location, salary
4. Edit or delete jobs from dashboard

### Job Seeker
1. Register as **Job Seeker**
2. Browse/search jobs by keyword or tag
3. Click a job → Apply
4. View all applications under "My Applications"
