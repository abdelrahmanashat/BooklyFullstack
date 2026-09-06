from pydantic import BaseModel
import uuid
from datetime import datetime, date
from typing import List
from src.reviews.schemas import ReviewModel
from src.tags.schemas import TagModel

class Book(BaseModel):
    uid: uuid.UUID
    title: str
    author: str
    publisher: str
    published_date: date
    page_count: int
    language: str
    created_at: datetime
    update_at: datetime

class BookDetailModel(Book):
    reviews: List[ReviewModel]
    tags: List[TagModel]

class BookCreateModel(BaseModel):
    title: str
    author: str
    publisher: str
    published_date: str
    page_count: int
    language: str
    
class BookUpdateModel(BaseModel):
    title: str
    author: str
    publisher: str
    page_count: int
    language: str