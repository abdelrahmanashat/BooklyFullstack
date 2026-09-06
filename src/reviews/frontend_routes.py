from fasthtml.common import *
import httpx
import uuid
from fastapi.responses import RedirectResponse
from starlette.requests import Request

from src.url_names import url_names
from src.config import Config
from src.utlis import generate_form_from_model, accept_model_fields
from src.reviews.schemas import ReviewCreateModel 
from src import rt

# Dynamically choose http or https for Render deployment
if "localhost" in Config.DOMAIN or "127.0.0.1" in Config.DOMAIN:
    scheme = "http"
else:
    scheme = "https"

current_url = f"{scheme}://{Config.DOMAIN}"
frontend_prefix = url_names.frontend_url
backend_prefix = url_names.version_prefix

# Helper function to grab the token from cookies
def get_auth_headers(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}

# ==========================================
# VIEW REVIEWS FOR A BOOK (HTMX Snippet)
# ==========================================
# This route returns a list of reviews that you can inject into your book details UI

@rt('/books/{book_uid}/reviews')
async def get_book_reviews(book_uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return P("Please log in to view reviews.", style="color: red;")
        
    api_url = f"{current_url}{backend_prefix}/books/{book_uid}/reviews" 
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    if api_response.status_code != 200:
        return P("⚠️ Could not load reviews.", style="color: grey;")
        
    reviews_data = api_response.json()
    
    if not reviews_data:
        return P("No reviews yet. Be the first to review!", style="font-style: italic; color: grey;")
    
    # Build a simple UI list for the reviews
    reviews_list = Ul(*[
        Li(
            Strong(f"Rating: {review.get('rating', 'N/A')}/5"),
            P(review.get('comment', 'No comment provided.'), style="margin: 5px 0;"),
            Small(f"By User: {review.get('user_uid', 'Anonymous')}", style="color: grey;"),
            
            # Add these action links:
            Div(
                A("Edit", href=f"{frontend_prefix}/books/{book_uid}/reviews/{review.get('uid')}/edit", style="font-size: 0.8rem; margin-right: 10px;"),
                A("Delete", href=f"{frontend_prefix}/books/{book_uid}/reviews/{review.get('uid')}/delete", style="font-size: 0.8rem; color: #d9534f;"),
                style="margin-top: 5px;"
            ),
            
            style="border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 10px;"
        ) for review in reviews_data
    ], style="list-style-type: none; padding-left: 0;")

# ==========================================
# CREATE A REVIEW
# ==========================================

@rt('/books/{book_uid}/reviews/create')
def get_create_review(book_uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    form = generate_form_from_model(
        model=ReviewCreateModel,
        submit_url=f"{frontend_prefix}/books/{book_uid}/reviews/create",
        submit_text="Submit Review"
    )
    
    return Titled("Add a Review", Main(
        form, 
        P(A("Cancel", href=f"{frontend_prefix}/books", cls="secondary"))
    ), cls="container")

@rt('/books/{book_uid}/reviews/create')
@accept_model_fields(ReviewCreateModel)
async def post_create_review(book_uid: uuid.UUID, request: Request, **kwargs):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/books/{book_uid}/reviews"
    payload = {key: val for key, val in kwargs.items()}
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        api_response = await client.post(api_url, json=payload, headers=headers)
        
    if api_response.status_code in (200, 201):
        # Redirect back to the library upon success
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
    else:
        try:
            error_data = api_response.json()
            error_msg = error_data.get("message", "Failed to add review.")
        except Exception:
            error_msg = f"Server Error {api_response.status_code}: Something went wrong."
            
        return Titled("Error", Main(
            P(error_msg, style="color: red;"),
            A("Try Again", href=f"{frontend_prefix}/books/{book_uid}/reviews/create", cls="button secondary")
        ), cls="container")
        
# ==========================================
# DELETE REVIEW
# ==========================================

@rt('/books/{book_uid}/reviews/{review_uid}/delete')
async def get_delete_review(book_uid: uuid.UUID, review_uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    return Titled("Delete Review", Main(
        H3("Are you sure you want to delete this review?"),
        P("This action cannot be undone.", style="color: red;"),
        
        Form(
            Button("Yes, Delete Review", type="submit", cls="button danger", style="background-color: #d9534f; color: white; border: none;"),
            action=f"{frontend_prefix}/books/{book_uid}/reviews/{review_uid}/delete",
            method="post",
            style="display: inline-block; margin-right: 10px;"
        ),
        A("Cancel", href=f"{frontend_prefix}/books", cls="button secondary outline"),
        
        style="text-align: center; margin-top: 50px;"
    ), cls="container")

@rt('/books/{book_uid}/reviews/{review_uid}/delete')
async def post_delete_review(book_uid: uuid.UUID, review_uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    # Adjust this URL if your backend expects a nested path
    api_url = f"{current_url}{backend_prefix}/reviews/{review_uid}"
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        api_response = await client.delete(api_url, headers=headers)
        
    if api_response.status_code in (200, 204):
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
    else:
        try:
            error_msg = api_response.json().get("message", "Failed to delete review.")
        except Exception:
            error_msg = f"Server Error {api_response.status_code}: Something went wrong."
            
        return Titled("Error", Main(
            P(error_msg, style="color: red;"),
            A("Back to Library", href=f"{frontend_prefix}/books", cls="button secondary")
        ), cls="container")