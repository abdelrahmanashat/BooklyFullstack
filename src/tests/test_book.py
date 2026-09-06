book_prefix = f"/api/v1/book"

def test_get_all_books(fake_session, fake_book_service, test_client):
    
    response = test_client.get(
            url=f"{book_prefix}"
        )
    
    assert fake_book_service.get_all_books_called_once()
    assert fake_book_service.get_all_books_called_once_with(fake_session)