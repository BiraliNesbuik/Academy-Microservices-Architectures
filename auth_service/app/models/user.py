from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    username: str
    hashed_password: str
    role: str

class UserRegister(BaseModel):
    username: str
    password: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"