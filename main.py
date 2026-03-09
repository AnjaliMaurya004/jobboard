from fastapi import FastAPI, Request, Depends, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models, auth, database

app = FastAPI(title="Job Board")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

database.create_db()

# ─── Auth Pages ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(database.get_db)):
    jobs = db.query(models.Job).filter(models.Job.is_active == True).order_by(models.Job.id.desc()).limit(10).all()
    return templates.TemplateResponse("home.html", {"request": request, "jobs": jobs})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@app.post("/register", response_class=HTMLResponse)
def register(request: Request, username: str = Form(...), email: str = Form(...),
             password: str = Form(...), role: str = Form(...), db: Session = Depends(database.get_db)):
    if db.query(models.User).filter(models.User.email == email).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email already registered"})
    user = models.User(username=username, email=email,
                       password=auth.hash_password(password), role=role)
    db.add(user)
    db.commit()
    return RedirectResponse("/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), password: str = Form(...),
          db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not auth.verify_password(password, user.password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    token = auth.create_token({"sub": str(user.id), "role": user.role})
    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie("token", token)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("token")
    return response

# ─── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(database.get_db)):
    user = auth.get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    if user.role == "recruiter":
        jobs = db.query(models.Job).filter(models.Job.recruiter_id == user.id).all()
        return templates.TemplateResponse("dashboard_recruiter.html", {"request": request, "user": user, "jobs": jobs})
    else:
        jobs = db.query(models.Job).filter(models.Job.is_active == True).all()
        return templates.TemplateResponse("dashboard_seeker.html", {"request": request, "user": user, "jobs": jobs})

# ─── Company ────────────────────────────────────────────────────────────────────

@app.get("/company/create", response_class=HTMLResponse)
def company_create_page(request: Request, db: Session = Depends(database.get_db)):
    user = auth.get_current_user(request, db)
    if not user or user.role != "recruiter":
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("company_form.html", {"request": request, "user": user, "company": None})

@app.post("/company/create")
def company_create(request: Request, name: str = Form(...), description: str = Form(""),
                   website: str = Form(""), db: Session = Depends(database.get_db)):
    user = auth.get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    company = models.Company(name=name, description=description, website=website, owner_id=user.id)
    db.add(company)
    db.commit()
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/companies", response_class=HTMLResponse)
def companies_list(request: Request, db: Session = Depends(database.get_db)):
    user = auth.get_current_user(request, db)
    companies = db.query(models.Company).all()
    return templates.TemplateResponse("companies.html", {"request": request, "user": user, "companies": companies})

@app.get("/company/{company_id}", response_class=HTMLResponse)
def company_detail(company_id: int, request: Request, db: Session = Depends(database.get_db)):
    user = auth.get_current_user(request, db)
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(404, "Company not found")
    jobs = db.query(models.Job).filter(models.Job.company_id == company_id, models.Job.is_active == True).all()
    return templates.TemplateResponse("company_detail.html", {"request": request, "user": user, "company": company, "jobs": jobs})

# ─── Jobs ───────────────────────────────────────────────────────────────────────

@app.get("/jobs", response_class=HTMLResponse)
def jobs_list(request: Request, db: Session = Depends(database.get_db),
              search: str = Query(""), tag: str = Query(""), page: int = Query(1)):
    user = auth.get_current_user(request, db)
    query = db.query(models.Job).filter(models.Job.is_active == True)
    if search:
        query = query.filter(models.Job.title.contains(search) | models.Job.description.contains(search))
    if tag:
        query = query.filter(models.Job.tags.contains(tag))
    total = query.count()
    per_page = 6
    jobs = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page
    return templates.TemplateResponse("jobs.html", {
        "request": request, "user": user, "jobs": jobs,
        "search": search, "tag": tag, "page": page, "total_pages": total_pages
    })

@app.get("/job/new", response_class=HTMLResponse)
def job_new_page(request: Request, db: Session = Depends(database.get_db)):
    user = auth.get_current_user(request, db)
    if not user or user.role != "recruiter":
        return RedirectResponse("/login", status_code=302)
    companies = db.query(models.Company).filter(models.Company.owner_id == user.id).all()
    return templates.TemplateResponse("job_form.html", {"request": request, "user": user, "job": None, "companies": companies})

@app.post("/job/new")
def job_create(request: Request, title: str = Form(...), description: str = Form(...),
               location: str = Form(""), salary: str = Form(""), tags: str = Form(""),
               company_id: int = Form(None), db: Session = Depends(database.get_db)):
    user = auth.get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    job = models.Job(title=title, description=description, location=location,
                     salary=salary, tags=tags, recruiter_id=user.id, company_id=company_id)
    db.add(job)
    db.commit()
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/job/{job_id}", response_class=HTMLResponse)
def job_detail(job_id: int, request: Request, db: Session = Depends(database.get_db)):
    user = auth.get_current_user(request, db)
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    already_applied = False
    if user and user.role == "seeker":
        already_applied = db.query(models.Application).filter(
            models.Application.job_id == job_id, models.Application.user_id == user.id).first() is not None
    return templates.TemplateResponse("job_detail.html", {
        "request": request, "user": user, "job": job, "already_applied": already_applied
    })

@app.get("/job/{job_id}/edit", response_class=HTMLResponse)
def job_edit_page(job_id: int, request: Request, db: Session = Depends(database.get_db)):
    user = auth.get_current_user(request, db)
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job or job.recruiter_id != user.id:
        return RedirectResponse("/dashboard", status_code=302)
    companies = db.query(models.Company).filter(models.Company.owner_id == user.id).all()
    return templates.TemplateResponse("job_form.html", {"request": request, "user": user, "job": job, "companies": companies})

@app.post("/job/{job_id}/edit")
def job_edit(job_id: int, request: Request, title: str = Form(...), description: str = Form(...),
             location: str = Form(""), salary: str = Form(""), tags: str = Form(""),
             company_id: int = Form(None), db: Session = Depends(database.get_db)):
    user = auth.get_current_user(request, db)
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job or job.recruiter_id != user.id:
        return RedirectResponse("/dashboard", status_code=302)
    job.title = title; job.description = description
    job.location = location; job.salary = salary
    job.tags = tags; job.company_id = company_id
    db.commit()
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/job/{job_id}/delete")
def job_delete(job_id: int, request: Request, db: Session = Depends(database.get_db)):
    user = auth.get_current_user(request, db)
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if job and job.recruiter_id == user.id:
        db.delete(job)
        db.commit()
    return RedirectResponse("/dashboard", status_code=302)

# ─── Applications ───────────────────────────────────────────────────────────────

@app.post("/job/{job_id}/apply")
def apply(job_id: int, request: Request, db: Session = Depends(database.get_db)):
    user = auth.get_current_user(request, db)
    if not user or user.role != "seeker":
        return RedirectResponse("/login", status_code=302)
    existing = db.query(models.Application).filter(
        models.Application.job_id == job_id, models.Application.user_id == user.id).first()
    if not existing:
        app_obj = models.Application(job_id=job_id, user_id=user.id)
        db.add(app_obj)
        db.commit()
    return RedirectResponse(f"/job/{job_id}", status_code=302)

@app.get("/my-applications", response_class=HTMLResponse)
def my_applications(request: Request, db: Session = Depends(database.get_db)):
    user = auth.get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    apps = db.query(models.Application).filter(models.Application.user_id == user.id).all()
    return templates.TemplateResponse("my_applications.html", {"request": request, "user": user, "apps": apps})
