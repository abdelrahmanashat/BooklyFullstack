from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import List
from src.books.schemas import Book
from src.reviews.schemas import ReviewModel

class UserCreateModel(BaseModel):
    first_name: str = Field(max_length=25)
    last_name: str = Field(max_length=25)
    username: str = Field(max_length=8)
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)
    model_config = {
        "json_schema_extra": {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "email": "johndoe123@co.com",
                "password": "testpass123",
            }
        }
    }
    
class UserModel(BaseModel):
    uid: uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_verified: bool 
    password_hash: str = Field(exclude=True)
    created_at: datetime 
    update_at: datetime 
    
class UserBookModel(UserModel):    
    books: List[Book]
    reviews: List[ReviewModel]
    
class UserLoginModel(BaseModel):
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)
    model_config = {
            "json_schema_extra": {
                "example": {
                    "email": "johndoe123@co.com",
                    "password": "testpass123",
                }
            }
        }
        
class EmailModel(BaseModel):
    addresses: list[str]
    model_config = {
            "json_schema_extra": {
                "example": [
                    "johndoe123@co.com",
                    "alansherer@co.com",
                    "marado2@abc.efg",
                    ]
            }
        }
    
class PasswordResetRequestModel(BaseModel):
    email: str = Field(max_length=40)
    model_config = {
                "json_schema_extra": {
                    "example": {
                        "email": "johndoe123@co.com"
                    }
                }
            }
    
class PasswordResetConfirmModel(BaseModel):
    new_password: str = Field(min_length=6)
    confirm_new_password: str = Field(min_length=6)
    model_config = {
                "json_schema_extra": {
                    "example": {
                        "new_password": "testpass123",
                        "confirm_new_password": "testpass123",
                    }
                }
            }