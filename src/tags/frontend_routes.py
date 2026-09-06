from fasthtml.common import *
import httpx
import uuid
from fastapi.responses import RedirectResponse
from starlette.requests import Request

from src.url_names import url_names
from src.config import Config
from src.utlis import generate_form_from_model, accept_model_fields
from src.tags.schemas import TagCreateModel, TagAddModel
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
# LIST ALL TAGS
# ==========================================

@rt('/tags')
async def get_tags(request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/tags" 
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    if api_response.status_code == 401:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    tags_data = api_response.json() 
    
    # Build the tag list UI
    tags_list = Ul(*[
        Li(
            Strong(tag.get("name", "Unnamed Tag")),
            Div(
                A("Edit", href=f"{frontend_prefix}/tags/{tag.get('uid')}/edit", style="font-size: 0.8rem; margin-right: 10px;"),
                A("Delete", href=f"{frontend_prefix}/tags/{tag.get('uid')}/delete", style="font-size: 0.8rem; color: #d9534f;"),
                style="display: inline-block; margin-left: 15px;"
            ),
            style="margin-bottom: 10px;"
        ) for tag in tags_data
    ])
    
    return Titled("Manage Tags", Main(
        Div(
            A("+ Create New Tag", href=f"{frontend_prefix}/tags/create", cls="button primary"),
            A("Back to Library", href=f"{frontend_prefix}/books", cls="button secondary outline", style="float: right;"),
            style="margin-bottom: 20px;"
        ),
        Hr(),
        tags_list if tags_data else P("No tags found. Create one to get started!", style="color: grey;")
    ), cls="container")

# ==========================================
# CREATE A TAG
# ==========================================

@rt('/tags/create')
def get_create_tag(request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    form = generate_form_from_model(
        model=TagCreateModel,
        submit_url=f"{frontend_prefix}/tags/create",
        submit_text="Save Tag"
    )
    
    return Titled("Create Tag", Main(
        form, 
        P(A("Cancel", href=f"{frontend_prefix}/tags", cls="secondary"))
    ), cls="container")

@rt('/tags/create')
@accept_model_fields(TagCreateModel)
async def post_create_tag(request: Request, **kwargs):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/tags"
    payload = {key: val for key, val in kwargs.items()}
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        api_response = await client.post(api_url, json=payload, headers=headers)
        
    if api_response.status_code in (200, 201):
        return RedirectResponse(url=f"{frontend_prefix}/tags", status_code=303)
    else:
        try:
            error_msg = api_response.json().get("message", "Failed to create tag.")
        except Exception:
            error_msg = f"Server Error {api_response.status_code}: Something went wrong."
            
        return Titled("Error", Main(
            P(error_msg, style="color: red;"),
            A("Try Again", href=f"{frontend_prefix}/tags/create", cls="button secondary")
        ), cls="container")

# ==========================================
# UPDATE TAG
# ==========================================

@rt('/tags/{uid}/edit')
async def get_edit_tag(uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    # Generate the update form
    form = generate_form_from_model(
        model=TagCreateModel,
        submit_url=f"{frontend_prefix}/tags/{uid}/edit",
        submit_text="Save Changes"
    )
    
    return Titled("Edit Tag", Main(
        form, 
        P(A("Cancel", href=f"{frontend_prefix}/tags", cls="secondary outline"))
    ), cls="container")

@rt('/tags/{uid}/edit')
@accept_model_fields(TagCreateModel)
async def post_edit_tag(uid: uuid.UUID, request: Request, **kwargs):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/tags/{uid}"
    payload = {key: val for key, val in kwargs.items() if val is not None and val != ""}
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        api_response = await client.patch(api_url, json=payload, headers=headers)
        
    if api_response.status_code in (200, 201, 204):
        return RedirectResponse(url=f"{frontend_prefix}/tags", status_code=303)
    else:
        try:
            error_msg = api_response.json().get("message", "Failed to update tag.")
        except Exception:
            error_msg = f"Server Error {api_response.status_code}: Something went wrong."
            
        return Titled("Error", Main(
            P(error_msg, style="color: red;"),
            A("Try Again", href=f"{frontend_prefix}/tags/{uid}/edit", cls="button secondary")
        ), cls="container")

# ==========================================
# DELETE TAG
# ==========================================

@rt('/tags/{uid}/delete')
async def get_delete_tag(uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    # Optional: fetch the tag to show its name in the warning
    api_url = f"{current_url}{backend_prefix}/tags/{uid}"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    tag_name = "this tag"
    if api_response.status_code == 200:
        tag_name = f"'{api_response.json().get('name')}'"
        
    return Titled("Delete Tag", Main(
        H3(f"Are you sure you want to delete {tag_name}?"),
        P("This action cannot be undone.", style="color: red;"),
        
        Form(
            Button("Yes, Delete", type="submit", cls="button danger", style="background-color: #d9534f; color: white; border: none;"),
            action=f"{frontend_prefix}/tags/{uid}/delete",
            method="post",
            style="display: inline-block; margin-right: 10px;"
        ),
        A("Cancel", href=f"{frontend_prefix}/tags", cls="button secondary outline"),
        
        style="text-align: center; margin-top: 50px;"
    ), cls="container")

@rt('/tags/{uid}/delete')
async def post_delete_tag(uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/tags/{uid}"
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        api_response = await client.delete(api_url, headers=headers)
        
    if api_response.status_code in (200, 204):
        return RedirectResponse(url=f"{frontend_prefix}/tags", status_code=303)
    else:
        try:
            error_msg = api_response.json().get("message", "Failed to delete tag.")
        except Exception:
            error_msg = f"Server Error {api_response.status_code}: Something went wrong."
            
        return Titled("Error", Main(
            P(error_msg, style="color: red;"),
            A("Back to Tags", href=f"{frontend_prefix}/tags", cls="button secondary")
        ), cls="container")

# ==========================================
# ADD TAG TO BOOK
# ==========================================

@rt('/books/{book_uid}/tags/add')
async def get_add_tag_to_book(book_uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    # 1. Fetch all available tags to populate the dropdown menu
    api_url = f"{current_url}{backend_prefix}/tags"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    if api_response.status_code != 200:
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
        
    tags_data = api_response.json()
    
    # 2. Handle the case where the user hasn't created any tags yet
    if not tags_data:
        return Titled("Add Tag", Main(
            P("No tags exist yet. Please create a tag first."),
            A("Create Tag", href=f"{frontend_prefix}/tags/create", cls="button primary"),
            A("Cancel", href=f"{frontend_prefix}/books", cls="button secondary outline", style="margin-left: 10px;")
        ), cls="container")

    # 3. Create dropdown options dynamically using standard FastHTML
    tag_options = [Option(tag.get("name"), value=tag.get("uid")) for tag in tags_data]
    
    form = Form(
        Label("Select a Tag", Select(*tag_options, name="tag_uid", required=True)),
        Button("Add Tag to Book", type="submit"),
        action=f"{frontend_prefix}/books/{book_uid}/tags/add",
        method="post"
    )
    
    return Titled("Add Tag to Book", Main(
        form, 
        P(A("Cancel", href=f"{frontend_prefix}/books", cls="secondary"))
    ), cls="container")

@rt('/books/{book_uid}/tags/add')
async def post_add_tag_to_book(book_uid: uuid.UUID, tag_uid: str, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    # NOTE: Check your FastAPI backend to see exactly what URL and payload it expects!
    # Option A (Most common): POST /books/{book_uid}/tags with body {"uid": tag_uid}
    # Option B (Path parameter): POST /books/{book_uid}/tags/{tag_uid}
    
    # I am assuming Option A here. If your API expects something else, tweak the URL/Payload below:
    api_url = f"{current_url}{backend_prefix}/books/{book_uid}/tags"
    
    # We construct a simple JSON dictionary to send the tag ID to the backend
    payload = {"uid": tag_uid} 
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        api_response = await client.post(api_url, json=payload, headers=headers)
        
    if api_response.status_code in (200, 201):
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
    else:
        try:
            error_msg = api_response.json().get("message", "Failed to add tag.")
        except Exception:
            error_msg = f"Server Error {api_response.status_code}: Something went wrong."
            
        return Titled("Error", Main(
            P(error_msg, style="color: red;"),
            A("Try Again", href=f"{frontend_prefix}/books/{book_uid}/tags/add", cls="button secondary")
        ), cls="container")

# ==========================================
# ADD TAG TO BOOK
# ==========================================

@rt('/books/{book_uid}/tags/add')
async def get_add_tag_to_book(book_uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    # 1. Fetch all available tags to populate the dropdown menu
    api_url = f"{current_url}{backend_prefix}/tags" # Matches the GET "/" in routes_3.py
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    if api_response.status_code != 200:
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
        
    tags_data = api_response.json()
    
    # 2. Handle the case where the user hasn't created any tags yet
    if not tags_data:
        return Titled("Add Tag", Main(
            P("No tags exist yet. Please create a tag first."),
            A("Create Tag", href=f"{frontend_prefix}/tags/create", cls="button primary"),
            A("Cancel", href=f"{frontend_prefix}/books", cls="button secondary outline", style="margin-left: 10px;")
        ), cls="container")

    # 3. Create dropdown options dynamically
    tag_options = [Option(tag.get("name"), value=tag.get("uid")) for tag in tags_data]
    
    # ⚠️ IMPORTANT: The 'name' attribute in the Select below MUST exactly match 
    # the field name expected by your TagAddModel (e.g., 'tag_uid' or 'tags')
    form = Form(
        Label("Select a Tag", Select(*tag_options, name="tags", required=True)),
        Button("Add Tag to Book", type="submit"),
        action=f"{frontend_prefix}/books/{book_uid}/tags/add",
        method="post"
    )
    
    return Titled("Add Tag to Book", Main(
        form, 
        P(A("Cancel", href=f"{frontend_prefix}/books", cls="secondary"))
    ), cls="container")


@rt('/books/{book_uid}/tags/add')
@accept_model_fields(TagAddModel)
async def post_add_tag_to_book(book_uid: uuid.UUID, request: Request, **kwargs):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    # This URL targets the exact endpoint defined in your routes_3.py file
    api_url = f"{current_url}{backend_prefix}/tags/book/{book_uid}/tags"
    
    # Extract the payload based on TagAddModel
    payload = {key: val for key, val in kwargs.items()}
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        api_response = await client.post(api_url, json=payload, headers=headers)
        
    # The backend returns the updated Book model on success 
    if api_response.status_code in (200, 201):
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
    else:
        try:
            error_msg = api_response.json().get("message", "Failed to add tag.")
        except Exception:
            error_msg = f"Server Error {api_response.status_code}: Something went wrong."
            
        return Titled("Error", Main(
            P(error_msg, style="color: red;"),
            A("Try Again", href=f"{frontend_prefix}/books/{book_uid}/tags/add", cls="button secondary")
        ), cls="container")