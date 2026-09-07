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
async def get(book_uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return P("Please log in to view reviews.", style="color: #dc2626; font-size: 0.9rem;")
        
    api_url = f"{current_url}{backend_prefix}/books/{book_uid}/reviews" 
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    if api_response.status_code != 200:
        return P("⚠️ Could not load reviews.", style="color: #64748b; font-size: 0.9rem;")
        
    reviews_data = api_response.json()
    
    if not reviews_data:
        return P("No reviews yet. Be the first to share your thoughts!", style="font-style: italic; color: #94a3b8; font-size: 0.95rem; text-align: center; padding: 20px 0;")
    
    # Build a clean, styled UI list for the reviews
    review_items = []
    for review in reviews_data:
        # Convert numerical rating to visual stars safely
        try:
            rating_val = int(review.get('rating', 0))
            stars = "⭐" * rating_val + "☆" * (5 - rating_val)
        except (ValueError, TypeError):
            stars = "No rating"

        review_items.append(
            Div(
                # Header: User & Rating
                Div(
                    Span(f"👤 User {str(review.get('username', 'Anonymous'))}", style="font-weight: 600; font-size: 0.85rem; color: #475569;"),
                    Span(stars, style="color: #fbbf24; font-size: 0.9rem; letter-spacing: 2px;"),
                    style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;"
                ),
                
                # Review Text
                P(f"\"{review.get('review_text', 'No comment provided.')}\"", style="margin: 0 0 12px 0; color: #1e293b; font-size: 0.95rem; line-height: 1.5; font-style: italic;"),
                
                # Action: Delete (Aligned Right)
                Div(
                    A("🗑️ Delete", href=f"{frontend_prefix}/books/{book_uid}/reviews/{review.get('uid')}/delete", style="font-size: 0.75rem; color: #ef4444; text-decoration: none; font-weight: 600;"),
                    style="text-align: right;"
                ),
                
                style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin-bottom: 12px; box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);"
            )
        )
        
    return Div(*review_items)


# ==========================================
# CREATE A REVIEW
# ==========================================

@rt('/books/{book_uid}/reviews/create')
def get(book_uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    form = generate_form_from_model(
        model=ReviewCreateModel,
        submit_url=f"{frontend_prefix}/books/{book_uid}/reviews/create",
        submit_text="Submit Review"
    )
    
    cancel_link = Div(
        A("← Back to Library", href=f"{frontend_prefix}/books", style="font-size: 0.95rem; color: #64748b; text-decoration: none; font-weight: 600;"),
        style="margin-top: 20px; text-align: center;"
    )
    
    return Titled("Add a Review", Main(
        Div(
            H2("Write a Review", style="text-align: center; color: #1e293b; margin-bottom: 8px;"),
            P("Share your thoughts and rate this book out of 5.", style="text-align: center; color: #64748b; margin-bottom: 30px;"),
            form, 
            cancel_link,
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 75vh;"
        )
    ), cls="container")

@rt('/books/{book_uid}/reviews/create')
@accept_model_fields(ReviewCreateModel)
async def post(book_uid: uuid.UUID, request: Request, **kwargs):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/reviews/books/{book_uid}"
    payload = {key: val for key, val in kwargs.items()}
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        api_response = await client.post(api_url, json=payload, headers=headers)
        
    if api_response.status_code in (200, 201):
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
    else:
        try:
            error_msg = api_response.json().get("message", "Failed to add review.")
        except Exception:
            error_msg = f"Server Error {api_response.status_code}: Something went wrong."
            
        return Titled("Error Adding Review", Main(
            Div(
                H3("⚠️ Could Not Save Review", style="color: #dc2626; margin-bottom: 10px;"),
                P(error_msg, style="color: #475569; margin-bottom: 25px;"),
                A("Try Again", href=f"{frontend_prefix}/books/{book_uid}/reviews/create", cls="button primary", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px; margin-bottom: 10px;"),
                A("Cancel", href=f"{frontend_prefix}/books", cls="button secondary outline", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fef2f2; border: 1px solid #f87171; border-radius: 12px;"
            )
        ), cls="container")
        
        
# ==========================================
# DELETE REVIEW
# ==========================================

@rt('/books/{book_uid}/reviews/{review_uid}/delete')
async def get(book_uid: uuid.UUID, review_uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    return Titled("Delete Review", Main(
        Div(
            H1("⚠️", style="font-size: 3.5rem; margin-bottom: 10px; line-height: 1;"),
            H2("Delete Review?", style="color: #0f172a; margin-bottom: 15px;"),
            
            P("Are you sure you want to delete this review?", style="color: #475569; font-size: 1.05rem; margin-bottom: 10px; font-weight: 600;"),
            P("This action cannot be undone and the review will be permanently removed from this book.", style="color: #dc2626; font-size: 0.9rem; margin-bottom: 30px; line-height: 1.5;"),
            
            # Side-by-Side Flexbox Buttons
            Div(
                A("Cancel", href=f"{frontend_prefix}/books", cls="button secondary outline", style="flex: 1; text-align: center; padding: 0.75rem; border-radius: 8px; font-weight: 600;"),
                Form(
                    Button("Yes, Delete", type="submit", cls="button danger", style="width: 100%; padding: 0.75rem; border-radius: 8px; font-weight: 600; background-color: #dc2626; color: white; border: none;"),
                    action=f"{frontend_prefix}/books/{book_uid}/reviews/{review_uid}/delete",
                    method="post",
                    style="flex: 1; margin: 0;"
                ),
                style="display: flex; gap: 15px; width: 100%;"
            ),
            
            style="max-width: 450px; margin: 15vh auto; padding: 40px 30px; text-align: center; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);"
        )
    ), cls="container")

@rt('/books/{book_uid}/reviews/{review_uid}/delete')
async def post(book_uid: uuid.UUID, review_uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
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
            
        return Titled("Deletion Failed", Main(
            Div(
                H3("⚠️ Could Not Delete Review", style="color: #dc2626; margin-bottom: 10px;"),
                P(error_msg, style="color: #475569; margin-bottom: 25px;"),
                A("Back to Library", href=f"{frontend_prefix}/books", cls="button secondary outline", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fef2f2; border: 1px solid #f87171; border-radius: 12px;"
            )
        ), cls="container")