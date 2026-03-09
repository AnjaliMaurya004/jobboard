from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from fastapi import Request
from sqlalchemy.orm import Session
import models

SECRET = "supersecretkey123"
ALGO = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict) -> str:
    data["exp"] = datetime.utcnow() + timedelta(days=7)
    return jwt.encode(data, SECRET, algorithm=ALGO)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGO])
    except Exception:
        return {}

def get_current_user(request: Request, db: Session):
    token = request.cookies.get("token")
    if not token:
        return None
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        return None
    return db.query(models.User).filter(models.User.id == int(user_id)).first()
