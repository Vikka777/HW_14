from fastapi import FastAPI, HTTPException, Depends, Form, status
from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import cloudinary, cloudinary.uploader, cloudinary.api
from starlette.middleware.cors import CORSMiddleware
from database import SessionLocal, engine
from models import Contact, User
from schemas import ContactCreate, ContactUpdate, Token, TokenData, UserCreate, User, Contact as ContactSchema
import redis
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY')
ALGORITHM = os.environ.get('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES'))
APP_URL = os.environ.get('APP_URL')

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

app = FastAPI()

# Підключення до Cloudinary
cloudinary.config( 
  cloud_name = "dsqjbvqq9", 
  api_key = "598976946911279", 
  api_secret = "***************************" 
)

# Налаштування CORS
app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
)

redis_client = redis.Redis(host='localhost', port=6379, db=0)



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        return user_email
    except JWTError:
        return None

def send_verification_email(receiver_email, verification_code):
    subject = "Email Verification Code"
    sender_email = EMAIL_ADDRESS
    receiver_email = receiver_email

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    body = f"Your email verification code is: {verification_code}"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(sender_email, receiver_email, msg.as_string())

@app.post("/register/", response_model=Token)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="User with this email already registered")

    verification_code = "123456"

    send_verification_email(user.email, verification_code)

    def get_password_hash(password):
        return pwd_context.hash(password)

    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, password=hashed_password, verification_code=verification_code)
    db.add(db_user)
    db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.email == username).first()
    if user is None or not verify_password(password, user.password):
        return None
    return user

# Логин и выдача токена доступа
@app.post("/token/", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if user is None:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/refresh-token/", response_model=Token)
def refresh_access_token(token: str = Form(...), db: Session = Depends(get_db)):
    user = verify_token(token)
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid token")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/contacts/", response_model=Contact)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_contact = Contact(**contact.dict(), user_id=current_user.username)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@app.get("/contacts/{contact_id}", response_model=Contact)
def read_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.username).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@app.put("/contacts/{contact_id}", response_model=Contact)
def update_contact(contact_id: int, contact_update: ContactUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.username).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    for field, value in contact_update.dict().items():
        setattr(db_contact, field, value)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@app.delete("/contacts/{contact_id}", response_model=Contact)
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.username).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return contact

@app.get("/contacts/", response_model=List[Contact])
def search_contacts(q: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contacts = db.query(Contact).filter(
        (Contact.first_name.ilike(f"%{q}%")) |
        (Contact.last_name.ilike(f"%{q}%")) |
        (Contact.email.ilike(f"%{q}%")),
        Contact.user_id == current_user.username
    ).all()
    return contacts

@app.get("/contacts/birthdays/", response_model=List[Contact])
def upcoming_birthdays(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_date = date.today()
    seven_days_later = current_date + timedelta(days=7)
    upcoming_birthday_contacts = (
        db.query(Contact)
        .filter(Contact.birthdate >= current_date, Contact.birthdate <= seven_days_later, Contact.user_id == current_user.username)
        .all()
    )
    return upcoming_birthday_contacts

class PasswordResetRequest(BaseModel):
    email: str

@app.post("/password-reset-request/", response_model=None)
def cache_current_user(redis, token, user_email):
    redis.set(token, user_email, ex=ACCESS_TOKEN_EXPIRE_MINUTES * 60)

def get_cached_user(redis, token):
    return redis.get(token)
def send_password_reset_email(email, reset_token):
    subject = "Password Reset Code"
    sender_email = EMAIL_ADDRESS
    receiver_email = email

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    body = f"Your password reset code is: {reset_token}"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(sender_email, receiver_email, msg.as_string())

def password_reset_request(request: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    reset_token = str(uuid.uuid4())

    cache_current_user(reset_token, {"user_id": user.id, "action": "password_reset"})

    send_password_reset_email(user.email, reset_token)

    return {"message": "Password reset email sent"}

class PasswordResetUpdate(BaseModel):
    token: str
    new_password: str

@app.post("/password-reset/", response_model=None)
def get_password_hash(password):
    return pwd_context.hash(password)

def password_reset(request: PasswordResetUpdate, db: Session = Depends(get_db)):
    cached_user_data = get_cached_user(request.token)
    if not cached_user_data or cached_user_data.get("action") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user_id = cached_user_data["user_id"]
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = get_password_hash(request.new_password)
    db.commit()

    redis_client.delete(request.token)

    return {"message": "Password reset successful"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
