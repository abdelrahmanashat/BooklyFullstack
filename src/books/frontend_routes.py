from fasthtml.common import *
import httpx
import uuid
from fastapi.responses import RedirectResponse
from starlette.requests import Request

from src.url_names import url_names
from src.config import Config
from src.utlis import generate_form_from_model, accept_model_fields
from src.books.schemas import BookCreateModel, BookUpdateModel 
from src import rt

# Dynamically choose http or https for Render deployment
if "localhost" in Config.DOMAIN or "127.0.0.1" in Config.DOMAIN:
    scheme = "http"
else:
    scheme = "https"

current_url = f"{scheme}://{Config.DOMAIN}"
frontend_prefix = url_names.frontend_url
backend_prefix = url_names.version_prefix

# Helper function to grab the token from cookies and format the Auth header
def get_auth_headers(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}

# ==========================================
# LIST ALL BOOKS (MAIN DASHBOARD)
# ==========================================

@rt('/books')
async def get_books(request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    # NOTE: Added a trailing slash here since your routes_2.py defines it as get('/')
    api_url = f"{current_url}{backend_prefix}/book/" 
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    # FIX: Catch ALL errors, not just 401s!
    if api_response.status_code != 200:
        try:
            error_data = api_response.json()
            error_msg = error_data.get("message", f"Failed to load books. Status: {api_response.status_code}")
        except Exception:
            error_msg = f"Server Error {api_response.status_code}: Something went wrong."
            
        return Titled("Error", Main(
            P(error_msg, style="color: red;"),
            A("Go to Login", href=f"{frontend_prefix}/", cls="button secondary outline")
        ), cls="container")
        
    books_data = api_response.json() 
    
    # Build the interactive library list
    books_list = Ul(*[
        Li(
            Strong(book.get("title", "Untitled")),
            
            Div(
                Button("Details", 
                       hx_get=f"{frontend_prefix}/books/{book.get('uid')}", 
                       hx_target=f"#book-wrapper-{book.get('uid')}", 
                       hx_swap="innerHTML"
                ),
                id=f"book-wrapper-{book.get('uid')}",
                style="margin-top: 5px;"
            )
        ) for book in books_data
    ])
    
    return Titled("My Library", Main(
        Div(
            A("+ Add New Book", href=f"{frontend_prefix}/books/create", cls="button primary"),
            A("Logout", href=f"{frontend_prefix}/logout", cls="button secondary outline", style="float: right;"),
            style="margin-bottom: 20px;"
        ),
        Hr(),
        books_list
    ), cls="container")

# ==========================================
# CREATE NEW BOOK
# ==========================================

@rt('/books/create')
def get_create_book(request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    form = generate_form_from_model(
        model=BookCreateModel,
        submit_url=f"{frontend_prefix}/books/create",
        submit_text="Save Book"
    )
    
    return Titled("Add a Book", Main(
        form, 
        P(A("Cancel & Back to Library", href=f"{frontend_prefix}/books", cls="secondary"))
    ), cls="container")

@rt('/books/create')
@accept_model_fields(BookCreateModel)
async def post_create_book(request: Request, **kwargs):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/book"
    payload = {key: val for key, val in kwargs.items()}
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        api_response = await client.post(api_url, json=payload, headers=headers)
        
    if api_response.status_code in (200, 201):
        # Redirect back to the library upon success
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
    else:
        try:
            error_data = api_response.json()
            error_msg = error_data.get("message", "Failed to add book.")
        except Exception:
            error_msg = f"Server Error {api_response.status_code}: Something went wrong."
            
        return Titled("Error", Main(
            P(error_msg, style="color: red;"),
            A("Try Again", href=f"{frontend_prefix}/books/create", cls="button secondary")
        ), cls="container")

# ==========================================
# BOOK DETAILS SUBMENU (HTMX TOGGLE)
# ==========================================

@rt('/books/{uid}')
async def get_book_details(uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)

    api_url = f"{current_url}{backend_prefix}/book/{uid}"
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    if api_response.status_code == 401:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
    elif api_response.status_code != 200:
        return Div(P("⚠️ Could not load details.", style="color: red;"))
        
    book = api_response.json()
    
    # Returns a tuple: The new "Hide" button, AND the details card
    return (
        Button("Hide Details", 
               hx_get=f"{frontend_prefix}/books/{uid}/close", 
               hx_target=f"#book-wrapper-{uid}", 
               hx_swap="innerHTML",
               cls="secondary outline" 
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
            # Optional: Edit button linking to an update route
            A("Edit Book", href=f"{frontend_prefix}/books/{uid}/edit", cls="button secondary", style="margin-top: 10px; font-size: 0.8rem;"),
            A("Delete Book", href=f"{frontend_prefix}/books/{uid}/delete", cls="button danger", style="margin-top: 10px; font-size: 0.8rem; background-color: #d9534f; color: white; border: none;"),
            A("+ Add Tag", href=f"{frontend_prefix}/books/{uid}/tags/add", cls="button secondary outline", style="margin-top: 10px; font-size: 0.8rem; margin-left: 10px;"),
            style="padding: 15px; border: 1px solid #ccc; border-radius: 8px; margin-top: 10px; background-color: #f9f9f9;"
        ),
        Div(
            # This fetches the reviews automatically when the book details card is rendered!
            hx_get=f"{frontend_prefix}/books/{uid}/reviews",
            hx_trigger="load",
            hx_swap="innerHTML"
        )
    )

@rt('/books/{uid}/close')
async def close_book_details(uid: uuid.UUID):
    # Returns JUST the original button, effectively erasing the submenu card
    return Button("Details", 
        hx_get=f"{frontend_prefix}/books/{uid}", 
        hx_target=f"#book-wrapper-{uid}", 
        hx_swap="innerHTML"
    )

# ==========================================
# UPDATE BOOK
# ==========================================

@rt('/books/{uid}/edit')
async def get_edit_book(uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    # 1. (Optional) Fetch the existing book so you can display its current title
    api_url = f"{current_url}{backend_prefix}/book/{uid}"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    if api_response.status_code != 200:
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
        
    book = api_response.json()
    
    # 2. Generate the update form
    form = generate_form_from_model(
        model=BookUpdateModel,
        submit_url=f"{frontend_prefix}/books/{uid}/edit",
        submit_text="Save Changes"
    )
    
    return Titled(f"Edit: {book.get('title')}", Main(
        form, 
        P(A("Cancel", href=f"{frontend_prefix}/books", cls="secondary outline"))
    ), cls="container")

@rt('/books/{uid}/edit')
@accept_model_fields(BookUpdateModel)
async def post_edit_book(uid: uuid.UUID, request: Request, **kwargs):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/book/{uid}"
    
    # Filter out empty fields if BookUpdateModel makes them optional
    payload = {key: val for key, val in kwargs.items() if val is not None and val != ""}
    
    # Using PATCH for updates (adjust to client.put if your backend requires PUT)
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        api_response = await client.patch(api_url, json=payload, headers=headers)
        
    if api_response.status_code in (200, 201, 204):
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
    else:
        try:
            error_msg = api_response.json().get("message", "Failed to update book.")
        except Exception:
            error_msg = f"Server Error {api_response.status_code}: Something went wrong."
            
        return Titled("Error", Main(
            P(error_msg, style="color: red;"),
            A("Try Again", href=f"{frontend_prefix}/books/{uid}/edit", cls="button secondary")
        ), cls="container")

# ==========================================
# DELETE BOOK
# ==========================================

@rt('/books/{uid}/delete')
async def get_delete_book(uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    # Fetch the book to show the user what they are deleting
    api_url = f"{current_url}{backend_prefix}/book/{uid}"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    if api_response.status_code != 200:
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
        
    book = api_response.json()
    
    return Titled("Delete Book", Main(
        H3(f"Are you sure you want to delete '{book.get('title')}'?"),
        P("This action cannot be undone.", style="color: red;"),
        
        # A simple form that submits a POST request to trigger the deletion
        Form(
            Button("Yes, Delete Book", type="submit", cls="button danger", style="background-color: #d9534f; color: white; border: none;"),
            action=f"{frontend_prefix}/books/{uid}/delete",
            method="post",
            style="display: inline-block; margin-right: 10px;"
        ),
        A("Cancel", href=f"{frontend_prefix}/books", cls="button secondary outline"),
        
        style="text-align: center; margin-top: 50px;"
    ), cls="container")

@rt('/books/{uid}/delete')
async def post_delete_book(uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/book/{uid}"
    
    # Issue the DELETE request to the backend
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        api_response = await client.delete(api_url, headers=headers)
        
    if api_response.status_code in (200, 204):
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
    else:
        try:
            error_msg = api_response.json().get("message", "Failed to delete book.")
        except Exception:
            error_msg = f"Server Error {api_response.status_code}: Something went wrong."
            
        return Titled("Error", Main(
            P(error_msg, style="color: red;"),
            A("Back to Library", href=f"{frontend_prefix}/books", cls="button secondary")
        ), cls="container")