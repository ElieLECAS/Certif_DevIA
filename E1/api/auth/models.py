from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import EmailStr

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    disabled: bool = False

class User(UserBase, table=True):
    __tablename__ = "user"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    date_creation: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    date_creation: datetime

class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    username: Optional[str] = None 