from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import BookCreateModel, BookUpdateModel
from sqlmodel import select, desc
from src.db.models import Book, Review, Tag, BookTag, User
from datetime import datetime

class BookService:
    async def get_all_books(self, session:AsyncSession):
        statement = select(Book).order_by(desc(Book.created_at))
        result = await session.exec(statement)
        return result.all()
    
    async def get_book(self, book_uid:str, session:AsyncSession):
        statement = select(Book).where(Book.uid==book_uid)
        result = await session.exec(statement)
        book = result.first()
        return book if book is not None else None
    
    async def get_user_book_submissions(self, user_uid:str, session:AsyncSession):
        statement = select(Book).order_by(desc(Book.created_at)).where(Book.user_uid==user_uid)
        result = await session.exec(statement)
        return result.all()
    
    async def get_book_reviews(self, book_uid:str, session:AsyncSession):
        statement = select(Review, User.username).join(User, isouter=True).where(Review.book_uid == book_uid)
        result = await session.exec(statement)
        rows = result.all()
    
        # Map the tuples into a list of dictionaries for clean JSON serialization
        reviews_with_usernames = []
        for review, username in rows:
            review_dict = review.model_dump() # Converts SQLModel/Pydantic object to dict
            review_dict["username"] = username or "Anonymous"
            reviews_with_usernames.append(review_dict)
            
        return reviews_with_usernames
    
    async def get_book_tags(self, book_uid:str, session:AsyncSession):
        statement = select(Tag).order_by(desc(Tag.created_at)).join(BookTag, Tag.uid==BookTag.tag_id).where(BookTag.book_id==book_uid)
        result = await session.exec(statement)
        return result.all()
    
    async def create_book(self, book_data:BookCreateModel, session:AsyncSession, user_uid:str):
        book_data_dict = book_data.model_dump()
        new_book = Book(**book_data_dict)
        new_book.published_date = datetime.strptime(book_data_dict['published_date'],"%Y-%m-%d")
        new_book.user_uid = user_uid
        session.add(new_book)   
        await session.commit()
        return new_book
    
    async def update_book(self, book_uid:str, update_data:BookUpdateModel, session:AsyncSession):
        book_to_update = await self.get_book(book_uid, session)
        
        if book_to_update is not None:    
            update_data_dict = update_data.model_dump()
            for k, v in update_data_dict.items():
                if(k == 'published_date'):
                    v = datetime.strptime(update_data_dict['published_date'],"%Y-%m-%d")
                setattr(book_to_update, k, v)
            await session.commit()
            return book_to_update
        else:
            return None
    
    async def delete_book(self, book_uid:str, session:AsyncSession):
        book_to_delete = await self.get_book(book_uid, session)

        if book_to_delete is not None:
            await session.delete(book_to_delete)
            await session.commit()
            return {}
        else:
            return None