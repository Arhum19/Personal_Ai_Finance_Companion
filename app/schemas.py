from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., max_length=72, min_length=8)

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str

    class Config:
        from_attributes = True

class UserLogin(BaseModel): 
    email: EmailStr
    password: str

# class Token(BaseModel):
#     access_token: str
#     token_type: str