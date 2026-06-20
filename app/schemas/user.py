from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# --- Input schemas (what CLIENT sends to us) ---

class UserCreate(BaseModel):
    email: EmailStr          # auto-validates email format
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- Output schemas (what WE send back to client) ---

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}  # lets Pydantic read SQLAlchemy objects

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None