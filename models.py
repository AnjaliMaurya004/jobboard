from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="seeker")  # "seeker" or "recruiter"

    jobs = relationship("Job", back_populates="recruiter")
    applications = relationship("Application", back_populates="user")
    companies = relationship("Company", back_populates="owner")

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    website = Column(String, default="")
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="companies")
    jobs = relationship("Job", back_populates="company")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    location = Column(String, default="")
    salary = Column(String, default="")
    tags = Column(String, default="")  # comma-separated
    is_active = Column(Boolean, default=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"))
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)

    recruiter = relationship("User", back_populates="jobs")
    company = relationship("Company", back_populates="jobs")
    applications = relationship("Application", back_populates="job")

    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    job = relationship("Job", back_populates="applications")
    user = relationship("User", back_populates="applications")
