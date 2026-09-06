from pydantic import BaseModel, Field
import uuid
from typing import Optional
from datetime import datetime

class ReviewModel(BaseModel):
    uid: uuid.UUID 
    user_uid: Optional[uuid.UUID]
    book_uid: Optional[uuid.UUID]
    review_text: str
    rating: int = Field(lt=6)
    created_at: datetime
    update_at: datetime 

class ReviewCreateModel(BaseModel):
    review_text: str
    rating: int = Field(lt=6)