from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional

class TokenData(BaseModel):
    username: Optional[str] = None

class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthdate: date
    additional_info: str

class User(BaseModel):
    email: EmailStr
    password: str
    
class ContactCreate(ContactBase):
    pass

class ContactUpdate(ContactBase):
    pass

class Contact(ContactBase):
    id: int

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        orm_mode = True
