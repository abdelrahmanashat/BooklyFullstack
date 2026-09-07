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
        
    # Get current user details
    api_url = f"{current_url}{backend_prefix}/auth/me" 
        
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
    
    # 1. Styled Error Card for Auth Failure
    if api_response.status_code != 200:
        error_msg = api_response.json().get("message", "Session expired or invalid.") if api_response.status_code != 500 else "Server Error."
        return Titled("Session Error", Main(
            Div(
                H3("⚠️ Authentication Failed", style="color: #dc2626; margin-bottom: 10px;"),
                P(error_msg, style="color: #475569; margin-bottom: 25px;"),
                A("Go to Login", href=f"{frontend_prefix}/", cls="button primary", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fef2f2; border: 1px solid #f87171; border-radius: 12px;"
            )
        ), cls="container")
    
    user_uid = api_response.json()["uid"]
    
    # Get the user's books
    api_url = f"{current_url}{backend_prefix}/books/user/{user_uid}" 
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    # 2. Styled Error Card for Data Fetch Failure
    if api_response.status_code != 200:
        error_msg = api_response.json().get("message", "Failed to load your library.") if api_response.status_code != 500 else "Server Error."
        return Titled("Error Loading Library", Main(
            Div(
                H3("⚠️ Could Not Load Books", style="color: #dc2626; margin-bottom: 10px;"),
                P(error_msg, style="color: #475569; margin-bottom: 25px;"),
                A("Try Again", href=f"{frontend_prefix}/books", cls="button primary", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fef2f2; border: 1px solid #f87171; border-radius: 12px;"
            )
        ), cls="container")
        
    books_data = api_response.json() 
    
    # 3. Friendly Empty State UX
    if not books_data:
        books_list = Div(
            H3("📚 Your library is empty", style="color: #475569; margin-bottom: 10px;"),
            P("Start building your collection by adding your first book.", style="color: #64748b; margin-bottom: 25px;"),
            A("+ Add New Book", href=f"{frontend_prefix}/books/create", cls="button primary", style="padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 600;"),
            style="text-align: center; padding: 60px 20px; background-color: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; margin-top: 20px;"
        )
    # 4. Modern Card-Based List
    else:
        books_list = Div(*[
            Div(
                Div(
                    Strong(book.get("title", "Untitled"), style="font-size: 1.15rem; color: #0f172a; display: block; margin-bottom: 4px;"),
                    Span(f"By {book.get('author', 'Unknown')}", style="color: #64748b; font-size: 0.9rem;"),
                    style="flex-grow: 1; margin-bottom: 10px;"
                ),
                # The wrapper for HTMX to expand the submenu into
                Div(
                    Button("▼ Details", 
                           hx_get=f"{frontend_prefix}/books/{book.get('uid')}", 
                           hx_target=f"#book-wrapper-{book.get('uid')}", 
                           hx_swap="innerHTML",
                           cls="button secondary outline",
                           style="font-size: 0.85rem; padding: 6px 14px;"
                    ),
                    id=f"book-wrapper-{book.get('uid')}",
                ),
                style="padding: 20px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 2px 4px -1px rgb(0 0 0 / 0.05);"
            ) for book in books_data
        ], style="display: flex; flex-direction: column; max-width: 800px; margin: 0 auto;")
    
    # 5. Clean Top Navigation Header
    top_nav = Div(
        H2("My Library", style="margin: 0; color: #1e293b; font-size: 1.75rem;"),
        Div(
            A("+ Add Book", href=f"{frontend_prefix}/books/create", cls="button primary", style="margin-right: 12px; border-radius: 6px; font-weight: 600;"),
            A("Logout", href=f"{frontend_prefix}/logout", cls="button secondary outline", style="border-radius: 6px;"),
            style="display: flex; align-items: center;"
        ),
        style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 20px; border-bottom: 1px solid #e2e8f0; margin-bottom: 25px; max-width: 800px; margin-left: auto; margin-right: auto;"
    )
    
    return Titled("Bookly Dashboard", Main(
        top_nav,
        books_list,
        style="padding-top: 20px; padding-bottom: 40px;"
    ), cls="container")

# ==========================================
# CREATE NEW BOOK
# ==========================================

@rt('/books/create')
def get(request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    form = generate_form_from_model(
        model=BookCreateModel,
        submit_url=f"{frontend_prefix}/books/create",
        submit_text="Save Book"
    )
    
    # 1. Styled Cancel Link
    cancel_link = Div(
        A("← Back to Library", href=f"{frontend_prefix}/books", style="font-size: 0.95rem; color: #64748b; text-decoration: none; font-weight: 600;"),
        style="margin-top: 20px; text-align: center;"
    )
    
    # 2. Centered Layout with Descriptive Headers
    return Titled("Add a Book", Main(
        Div(
            H2("Add a New Book", style="text-align: center; color: #1e293b; margin-bottom: 8px;"),
            P("Enter the details of the book to add it to your personal library.", style="text-align: center; color: #64748b; margin-bottom: 30px;"),
            form, 
            cancel_link,
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 75vh;"
        )
    ), cls="container")


@rt('/books/create')
@accept_model_fields(BookCreateModel)
async def post(request: Request, **kwargs):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/books"
    payload = {key: val for key, val in kwargs.items()}
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        api_response = await client.post(api_url, json=payload, headers=headers)
        
    if api_response.status_code in (200, 201):
        # Redirect back to the library upon success
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
    else:
        try:
            error_msg = api_response.json().get("message", "Failed to add book.")
        except Exception:
            error_msg = f"Server Error {api_response.status_code}: Something went wrong."
            
        # 3. Styled Error Card
        return Titled("Error Adding Book", Main(
            Div(
                H3("⚠️ Could Not Save Book", style="color: #dc2626; margin-bottom: 10px;"),
                P(error_msg, style="color: #475569; margin-bottom: 25px;"),
                A("Try Again", href=f"{frontend_prefix}/books/create", cls="button primary", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px; margin-bottom: 10px;"),
                A("Cancel", href=f"{frontend_prefix}/books", cls="button secondary outline", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fef2f2; border: 1px solid #f87171; border-radius: 12px;"
            )
        ), cls="container")

# ==========================================
# BOOK DETAILS SUBMENU (HTMX TOGGLE)
# ==========================================

@rt('/books/{uid}')
async def get(uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)

    api_url = f"{current_url}{backend_prefix}/books/{uid}"
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    if api_response.status_code == 401:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
    elif api_response.status_code != 200:
        return Div(P("⚠️ Could not load details.", style="color: #dc2626; font-size: 0.9rem; margin-top: 10px;"))
        
    book = api_response.json()
    
    # 1. Refined Tag Pills
    tags_data = book.get("tags", [])
    if tags_data:
        tags_ui = Div(
            *[Span(
                tag.get("name", "Unknown") if isinstance(tag, dict) else str(tag), 
                style="display: inline-block; background-color: #e0f2fe; color: #0369a1; padding: 4px 12px; border-radius: 16px; font-size: 0.75rem; font-weight: 600; margin-right: 8px; margin-bottom: 8px; border: 1px solid #bae6fd;"
            ) for tag in tags_data],
            style="margin-bottom: 15px;"
        )
    else:
        tags_ui = P("No tags added yet.", style="font-size: 0.85rem; color: #94a3b8; font-style: italic; margin-bottom: 15px;")

    # 2. Modern Grid Layout for Book Metadata (Replacing Ul/Li)
    metadata_grid = Div(
        Div(Span("Author", style="color: #64748b; font-size: 0.75rem; text-transform: uppercase; font-weight: 600; display: block;"), Span(book.get("author", "N/A"), style="font-weight: 500; color: #1e293b; font-size: 0.95rem;")),
        Div(Span("Publisher", style="color: #64748b; font-size: 0.75rem; text-transform: uppercase; font-weight: 600; display: block;"), Span(book.get("publisher", "N/A"), style="font-weight: 500; color: #1e293b; font-size: 0.95rem;")),
        Div(Span("Published", style="color: #64748b; font-size: 0.75rem; text-transform: uppercase; font-weight: 600; display: block;"), Span(book.get("published_date", "N/A"), style="font-weight: 500; color: #1e293b; font-size: 0.95rem;")),
        Div(Span("Pages", style="color: #64748b; font-size: 0.75rem; text-transform: uppercase; font-weight: 600; display: block;"), Span(str(book.get("page_count", 0)), style="font-weight: 500; color: #1e293b; font-size: 0.95rem;")),
        Div(Span("Language", style="color: #64748b; font-size: 0.75rem; text-transform: uppercase; font-weight: 600; display: block;"), Span(book.get("language", "N/A"), style="font-weight: 500; color: #1e293b; font-size: 0.95rem;")),
        style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 15px; margin-bottom: 20px; background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;"
    )

    # 3. Clean Action Buttons Row
    actions_ui = Div(
        A("✏️ Edit", href=f"{frontend_prefix}/books/{uid}/edit", cls="button secondary outline", style="font-size: 0.85rem; padding: 6px 12px; border-radius: 6px;"),
        A("🏷️ Add Tag", href=f"{frontend_prefix}/books/{uid}/tags/add", cls="button secondary outline", style="font-size: 0.85rem; padding: 6px 12px; border-radius: 6px;"),
        A("⭐ Add Review", href=f"{frontend_prefix}/books/{uid}/reviews/create", cls="button secondary outline", style="font-size: 0.85rem; padding: 6px 12px; border-radius: 6px;"),
        A("🗑️ Delete", href=f"{frontend_prefix}/books/{uid}/delete", cls="button danger", style="font-size: 0.85rem; padding: 6px 12px; border-radius: 6px;"),
        style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px;"
    )

    # Inline CSS for the fade-in animation
    fade_in_style = Style("@keyframes fadeIn { from { opacity: 0; transform: translateY(-5px); } to { opacity: 1; transform: translateY(0); } }")

    # Returns a tuple: The new "Hide" button, AND the details card
    return (
        Button("▲ Hide Details", 
               hx_get=f"{frontend_prefix}/books/{uid}/close", 
               hx_target=f"#book-wrapper-{uid}", 
               hx_swap="innerHTML",
               cls="button secondary",
               style="font-size: 0.85rem; padding: 6px 14px; background-color: #f1f5f9; color: #475569; border: none;"
        ),
        Div(
            fade_in_style,
            H3(book.get("title", "Unknown Title"), style="margin-top: 0; margin-bottom: 10px; color: #0f172a; font-size: 1.25rem;"),
            tags_ui,
            
            metadata_grid,
            actions_ui,
            
            Hr(style="margin: 0 0 20px 0; border-top: 1px solid #e2e8f0;"),
            
            # 4. Reviews section with header
            Div(
                H4("Reader Reviews:", style="margin-top: 0; margin-bottom: 15px; color: #1e293b; font-size: 1.1rem;"),
                Div(
                    hx_get=f"{frontend_prefix}/books/{uid}/reviews",
                    hx_trigger="load",
                    hx_swap="innerHTML",
                    style="min-height: 50px; color: #475569;"
                )
            ),
            
            style="padding: 25px; border: 1px solid #e2e8f0; border-radius: 12px; margin-top: 12px; background-color: #f8fafc; box-shadow: inset 0 2px 4px 0 rgb(0 0 0 / 0.02); animation: fadeIn 0.3s ease-out forwards;"
        )
    )

@rt('/books/{uid}/close')
async def close_book_details(uid: uuid.UUID):
    # Returns JUST the original button, effectively erasing the submenu card
    return Button("▼ Details", 
        hx_get=f"{frontend_prefix}/books/{uid}", 
        hx_target=f"#book-wrapper-{uid}", 
        hx_swap="innerHTML",
        cls="button secondary outline",
        style="font-size: 0.85rem; padding: 6px 14px;"
    )
# ==========================================
# UPDATE BOOK
# ==========================================

@rt('/books/{uid}/edit')
async def get(uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    # 1. Fetch the existing book so you can display its current title
    api_url = f"{current_url}{backend_prefix}/books/{uid}"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    if api_response.status_code != 200:
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
        
    book = api_response.json()
    
    # 2. Generate the update form (our upgraded utility handles the styling!)
    form = generate_form_from_model(
        model=BookUpdateModel,
        submit_url=f"{frontend_prefix}/books/{uid}/edit",
        submit_text="Save Changes",
        initial_data=book
    )
    
    # 3. Styled Cancel Link
    cancel_link = Div(
        A("← Back to Library", href=f"{frontend_prefix}/books", style="font-size: 0.95rem; color: #64748b; text-decoration: none; font-weight: 600;"),
        style="margin-top: 20px; text-align: center;"
    )
    
    # 4. Centered Layout with Contextual Headers
    return Titled("Edit Book", Main(
        Div(
            H2("Edit Book Details", style="text-align: center; color: #1e293b; margin-bottom: 8px;"),
            P("Updating: ", B(book.get('title', 'Unknown Book'), style="color: #0f172a;"), style="text-align: center; color: #64748b; margin-bottom: 30px;"),
            form, 
            cancel_link,
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 75vh;"
        )
    ), cls="container")


@rt('/books/{uid}/edit')
@accept_model_fields(BookUpdateModel)
async def post(uid: uuid.UUID, request: Request, **kwargs):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/books/{uid}"
    
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
            
        # 5. Styled Error Card
        return Titled("Update Failed", Main(
            Div(
                H3("⚠️ Could Not Save Changes", style="color: #dc2626; margin-bottom: 10px;"),
                P(error_msg, style="color: #475569; margin-bottom: 25px;"),
                A("Try Again", href=f"{frontend_prefix}/books/{uid}/edit", cls="button primary", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px; margin-bottom: 10px;"),
                A("Cancel", href=f"{frontend_prefix}/books", cls="button secondary outline", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fef2f2; border: 1px solid #f87171; border-radius: 12px;"
            )
        ), cls="container")

# ==========================================
# DELETE BOOK
# ==========================================

@rt('/books/{uid}/delete')
async def get(uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    # Fetch the book to show the user what they are deleting
    api_url = f"{current_url}{backend_prefix}/books/{uid}"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    if api_response.status_code != 200:
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
        
    book = api_response.json()
    
    # 1. Prominent, Centered Warning Card Layout
    return Titled("Delete Book", Main(
        Div(
            H1("⚠️", style="font-size: 3.5rem; margin-bottom: 10px; line-height: 1;"),
            H2("Delete Book?", style="color: #0f172a; margin-bottom: 15px;"),
            
            P("Are you absolutely sure you want to delete ", B(book.get('title', 'this book')), "?", style="color: #475569; font-size: 1.05rem; margin-bottom: 10px;"),
            P("This action cannot be undone. It will permanently remove this book and detach all associated tags and reviews.", style="color: #dc2626; font-size: 0.9rem; margin-bottom: 30px; line-height: 1.5;"),
            
            # 2. Side-by-Side Flexbox Buttons
            Div(
                A("Cancel", href=f"{frontend_prefix}/books", cls="button secondary outline", style="flex: 1; text-align: center; padding: 0.75rem; border-radius: 8px; font-weight: 600;"),
                Form(
                    Button("Yes, Delete", type="submit", cls="button danger", style="width: 100%; padding: 0.75rem; border-radius: 8px; font-weight: 600; background-color: #dc2626; color: white; border: none;"),
                    action=f"{frontend_prefix}/books/{uid}/delete",
                    method="post",
                    style="flex: 1; margin: 0;"
                ),
                style="display: flex; gap: 15px; width: 100%;"
            ),
            
            style="max-width: 450px; margin: 15vh auto; padding: 40px 30px; text-align: center; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);"
        )
    ), cls="container")

@rt('/books/{uid}/delete')
async def post(uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/books/{uid}"
    
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
            
        # 3. Standardized Error Card
        return Titled("Deletion Failed", Main(
            Div(
                H3("⚠️ Could Not Delete Book", style="color: #dc2626; margin-bottom: 10px;"),
                P(error_msg, style="color: #475569; margin-bottom: 25px;"),
                A("Back to Library", href=f"{frontend_prefix}/books", cls="button secondary outline", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fef2f2; border: 1px solid #f87171; border-radius: 12px;"
            )
        ), cls="container")