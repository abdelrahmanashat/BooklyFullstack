from fasthtml.common import *
import httpx
import uuid
from fastapi.responses import RedirectResponse
from src.url_names import url_names
from src.config import Config
from src import rt

current_url = f"http://{Config.DOMAIN}"
frontend_prefix = url_names.frontend_url
backend_prefix = url_names.version_prefix

@rt('/books')
async def get_ui_books(request: Request):
    # 1. Extract the token from the browser's cookie
    token = request.cookies.get("access_token")
    
    # If there is no token, boot them back to the login page
    if not token:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    # 2. Construct the header exactly how your FastAPI backend wants it
    headers = {"Authorization": f"Bearer {token}"}
    api_url = f"{current_url}{backend_prefix}/book/"
    
    # 3. Make the API request on behalf of the user
    async with httpx.AsyncClient() as client:
        api_response = await client.get(api_url, headers=headers)
        
    # If the token is expired or invalid, send them to login
    if api_response.status_code == 401:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
    
    # 4. Extract the JSON data and build your HTML UI
    books_data = api_response.json()
    
    # Assuming your API returns a list of dictionaries, e.g., [{"title": "Book 1"}, ...]
    # We map that data into HTML elements
    book_list = Ul(*[
        Li(
            Strong(book.get("title")),
            
            # 1. Create a wrapper Div to hold both the button and the submenu
            Div(
                Button("Details", 
                    hx_get=f"{frontend_prefix}/books/{book.get('uid')}", 
                    # Target the wrapper Div itself
                    hx_target=f"#book-wrapper-{book.get('uid')}", 
                    hx_swap="innerHTML"
                ),
                id=f"book-wrapper-{book.get('uid')}",
                style="margin-top: 5px;"
            )
        ) for book in books_data
    ])
    
    return Titled("Your Library",
        Main(
            H2("My Books"),
            book_list,
            # A logout button that will eventually clear the cookie
            A("Log out", href=f"{frontend_prefix}/", cls="secondary") 
        ),
        cls="container"
    )
    
@rt('/books/{uid}')
async def get(uid:uuid.UUID, request: Request):
    # 1. Grab the token for backend authentication
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)

    # 2. Fetch the specific book from your FastAPI backend
    api_url = f"{current_url}{backend_prefix}/book/{uid}"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        api_response = await client.get(api_url, headers=headers)
        
    # 3. Handle potential API errors gracefully
    if api_response.status_code == 401:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
    elif api_response.status_code != 200:
        return Div(
            P("⚠️ Could not load book details.", style="color: red;"),
            cls="submenu-error"
        )
        
    # 4. Extract the JSON payload
    book = api_response.json()
    
    # 2. Return the "Hide Details" button AND the data Div
    return (
        Button("Hide Details", 
               hx_get=f"{frontend_prefix}/books/{uid}/close", 
               hx_target=f"#book-wrapper-{uid}", 
               hx_swap="innerHTML",
               cls="secondary outline" # Optional styling to differentiate it
        ),
        Div(
            H3(book.get("title", "Unknown Title"), style="margin-bottom: 5px;"),
            Hr(),
            Ul(
                Li(B("Author: "), book.get("author", "N/A")),
                Li(B("Publisher: "), book.get("publisher", "N/A")),
                Li(B("Published: "), book.get("published_date", "N/A")),
                Li(B("Pages: "), str(book.get("page_count", 0))),
                Li(B("Language: "), book.get("language", "N/A"))
            ),
            style="padding: 15px; border: 1px solid #ccc; border-radius: 8px; margin-top: 10px; background-color: #f9f9f9;"
        )
    )

@rt('/books/{uid}/close')
async def close_book_details(uid: uuid.UUID):
    # 3. Return ONLY the original button (which removes the submenu)
    return Button("Details", 
        hx_get=f"{frontend_prefix}/books/{uid}", 
        hx_target=f"#book-wrapper-{uid}", 
        hx_swap="innerHTML"
    )