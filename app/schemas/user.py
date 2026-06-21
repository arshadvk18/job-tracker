from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# --- Input schemas (what CLIENT sends to us) ---

class UserCreate(BaseModel):
    email: EmailStr
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

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Resume schemas (new) ---

class ResumeSave(BaseModel):
    resume_text: str                    # plain text resume content

class ResumeResponse(BaseModel):
    resume_text: Optional[str]          # None if user hasn't saved one yet

class PDFExtractResponse(BaseModel):
    extracted_text: str                 # text pulled out of uploaded PDF
    char_count: int                     # so frontend can show "X characters extracted"