from fasthtml.common import *
import httpx
import uuid
from fastapi.responses import RedirectResponse
from starlette.requests import Request

from src.url_names import url_names
from src.config import Config
from src.utlis import generate_form_from_model, accept_model_fields
from src.tags.schemas import TagCreateModel
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
# LIST ALL TAGS (MANAGEMENT DASHBOARD)
# ==========================================

@rt('/tags')
async def get(request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/tags" 
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    if api_response.status_code == 401:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    tags_data = api_response.json() 
    
    # 1. Clean Top Navigation Header
    top_nav = Div(
        H2("Manage Tags", style="margin: 0; color: #1e293b; font-size: 1.75rem;"),
        Div(
            A("+ Create Tag", href=f"{frontend_prefix}/tags/create", cls="button primary", style="margin-right: 12px; border-radius: 6px; font-weight: 600;"),
            A("Library", href=f"{frontend_prefix}/books", cls="button secondary outline", style="border-radius: 6px;"),
            style="display: flex; align-items: center;"
        ),
        style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 20px; border-bottom: 1px solid #e2e8f0; margin-bottom: 25px; max-width: 800px; margin-left: auto; margin-right: auto;"
    )
    
    # 2. Friendly Empty State
    if not tags_data:
        tags_list = Div(
            H3("🏷️ No tags created yet", style="color: #475569; margin-bottom: 10px;"),
            P("Create tags to organize and categorize your library.", style="color: #64748b; margin-bottom: 25px;"),
            A("+ Create New Tag", href=f"{frontend_prefix}/tags/create", cls="button primary", style="padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 600;"),
            style="text-align: center; padding: 60px 20px; background-color: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px;"
        )
    # 3. Modern Grid of Tag Cards
    else:
        tags_list = Div(*[
            Div(
                Strong(tag.get("name", "Unnamed Tag"), style="font-size: 1.1rem; color: #0f172a;"),
                Div(
                    A("✏️ Edit", href=f"{frontend_prefix}/tags/{tag.get('uid')}/edit", style="font-size: 0.85rem; margin-right: 15px; text-decoration: none; color: #64748b; font-weight: 600;"),
                    A("🗑️ Delete", href=f"{frontend_prefix}/tags/{tag.get('uid')}/delete", style="font-size: 0.85rem; text-decoration: none; color: #ef4444; font-weight: 600;"),
                    style="margin-top: 15px; border-top: 1px solid #f1f5f9; padding-top: 10px;"
                ),
                style="padding: 20px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);"
            ) for tag in tags_data
        ], style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; max-width: 800px; margin: 0 auto;")
    
    return Titled("Manage Tags", Main(
        top_nav,
        tags_list,
        style="padding-top: 20px; padding-bottom: 40px;"
    ), cls="container")

# ==========================================
# CREATE A TAG
# ==========================================

@rt('/tags/create')
def get(request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    form = generate_form_from_model(
        model=TagCreateModel,
        submit_url=f"{frontend_prefix}/tags/create",
        submit_text="Save Tag"
    )
    
    cancel_link = Div(
        A("← Back to Tags", href=f"{frontend_prefix}/tags", style="font-size: 0.95rem; color: #64748b; text-decoration: none; font-weight: 600;"),
        style="margin-top: 20px; text-align: center;"
    )
    
    return Titled("Create Tag", Main(
        Div(
            H2("Create a New Tag", style="text-align: center; color: #1e293b; margin-bottom: 8px;"),
            P("Add a new category to help organize your books.", style="text-align: center; color: #64748b; margin-bottom: 30px;"),
            form, 
            cancel_link,
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 75vh;"
        )
    ), cls="container")

@rt('/tags/create')
@accept_model_fields(TagCreateModel)
async def post(request: Request, **kwargs):
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
            Div(
                H3("⚠️ Could Not Create Tag", style="color: #dc2626; margin-bottom: 10px;"),
                P(error_msg, style="color: #475569; margin-bottom: 25px;"),
                A("Try Again", href=f"{frontend_prefix}/tags/create", cls="button primary", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px; margin-bottom: 10px;"),
                A("Cancel", href=f"{frontend_prefix}/tags", cls="button secondary outline", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fef2f2; border: 1px solid #f87171; border-radius: 12px;"
            )
        ), cls="container")

# ==========================================
# UPDATE TAG
# ==========================================

@rt('/tags/{uid}/edit')
async def get(uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    # UX UPGRADE: Fetch the tag so it pre-fills the form!
    api_url = f"{current_url}{backend_prefix}/tags/{uid}"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    tag_data = api_response.json() if api_response.status_code == 200 else {}
        
    form = generate_form_from_model(
        model=TagCreateModel,
        submit_url=f"{frontend_prefix}/tags/{uid}/edit",
        submit_text="Save Changes",
        initial_data=tag_data
    )
    
    cancel_link = Div(
        A("← Back to Tags", href=f"{frontend_prefix}/tags", style="font-size: 0.95rem; color: #64748b; text-decoration: none; font-weight: 600;"),
        style="margin-top: 20px; text-align: center;"
    )
    
    return Titled("Edit Tag", Main(
        Div(
            H2("Edit Tag", style="text-align: center; color: #1e293b; margin-bottom: 8px;"),
            P("Rename your tag below.", style="text-align: center; color: #64748b; margin-bottom: 30px;"),
            form, 
            cancel_link,
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 75vh;"
        )
    ), cls="container")

@rt('/tags/{uid}/edit')
@accept_model_fields(TagCreateModel)
async def post(uid: uuid.UUID, request: Request, **kwargs):
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
            Div(
                H3("⚠️ Could Not Update Tag", style="color: #dc2626; margin-bottom: 10px;"),
                P(error_msg, style="color: #475569; margin-bottom: 25px;"),
                A("Try Again", href=f"{frontend_prefix}/tags/{uid}/edit", cls="button primary", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px; margin-bottom: 10px;"),
                A("Cancel", href=f"{frontend_prefix}/tags", cls="button secondary outline", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fef2f2; border: 1px solid #f87171; border-radius: 12px;"
            )
        ), cls="container")


# ==========================================
# DELETE TAG
# ==========================================

@rt('/tags/{uid}/delete')
async def get(uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/tags/{uid}"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    tag_name = "this tag"
    if api_response.status_code == 200:
        tag_name = f"'{api_response.json().get('name')}'"
        
    return Titled("Delete Tag", Main(
        Div(
            H1("⚠️", style="font-size: 3.5rem; margin-bottom: 10px; line-height: 1;"),
            H2("Delete Tag?", style="color: #0f172a; margin-bottom: 15px;"),
            
            P("Are you sure you want to delete ", B(tag_name), "?", style="color: #475569; font-size: 1.05rem; margin-bottom: 10px;"),
            P("This action cannot be undone. It will remove this tag from all associated books.", style="color: #dc2626; font-size: 0.9rem; margin-bottom: 30px; line-height: 1.5;"),
            
            Div(
                A("Cancel", href=f"{frontend_prefix}/tags", cls="button secondary outline", style="flex: 1; text-align: center; padding: 0.75rem; border-radius: 8px; font-weight: 600;"),
                Form(
                    Button("Yes, Delete", type="submit", cls="button danger", style="width: 100%; padding: 0.75rem; border-radius: 8px; font-weight: 600; background-color: #dc2626; color: white; border: none;"),
                    action=f"{frontend_prefix}/tags/{uid}/delete",
                    method="post",
                    style="flex: 1; margin: 0;"
                ),
                style="display: flex; gap: 15px; width: 100%;"
            ),
            
            style="max-width: 450px; margin: 15vh auto; padding: 40px 30px; text-align: center; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);"
        )
    ), cls="container")

@rt('/tags/{uid}/delete')
async def post(uid: uuid.UUID, request: Request):
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
            Div(
                H3("⚠️ Could Not Delete Tag", style="color: #dc2626; margin-bottom: 10px;"),
                P(error_msg, style="color: #475569; margin-bottom: 25px;"),
                A("Back to Tags", href=f"{frontend_prefix}/tags", cls="button secondary outline", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fef2f2; border: 1px solid #f87171; border-radius: 12px;"
            )
        ), cls="container")


# ==========================================
# ADD TAGS TO BOOK
# ==========================================

@rt('/books/{book_uid}/tags/add')
async def get(book_uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    api_url = f"{current_url}{backend_prefix}/tags"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    tags_data = []
    if api_response.status_code == 200:
        tags_data = api_response.json()

    tag_options = [Option(tag.get("name"), value=tag.get("name")) for tag in tags_data]
    
    # Custom styled form to match the `generate_form_from_model` aesthetics
    form = Form(
        Div(
            Label(Span("Select Existing Tags (Hold Ctrl/Cmd to select multiple)", style="font-weight: 600; color: #334155; display: block; margin-bottom: 5px;"), 
                  Select(*tag_options, name="existing_tags", multiple=True, size=5, style="width: 100%; padding: 0.6rem; border-radius: 6px; border: 1px solid #cbd5e1;")),
            style="margin-bottom: 1.25rem;"
        ),
              
        Div(
            Label(Span("And/Or Create New Tags", style="font-weight: 600; color: #334155; display: block; margin-bottom: 5px;"), 
                  Input(name="new_tags", placeholder="e.g. Science Fiction, Web Development", style="width: 100%; padding: 0.6rem; border-radius: 6px; border: 1px solid #cbd5e1; margin-top: 0.4rem;")),
            style="margin-bottom: 1.25rem;"
        ),
              
        Button("Save Tags to Book", type="submit", cls="button primary", style="width: 100%; padding: 0.75rem; font-size: 1.05rem; font-weight: 600; border-radius: 8px; cursor: pointer;"),
        
        action=f"{frontend_prefix}/books/{book_uid}/tags/add",
        method="post",
        style="width: 100%; max-width: 500px; padding: 25px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);"
    )
    
    cancel_link = Div(
        A("← Back to Library", href=f"{frontend_prefix}/books", style="font-size: 0.95rem; color: #64748b; text-decoration: none; font-weight: 600;"),
        style="margin-top: 20px; text-align: center;"
    )
    
    return Titled("Add Tags to Book", Main(
        Div(
            H2("Organize Your Book", style="text-align: center; color: #1e293b; margin-bottom: 8px;"),
            P("Select from existing tags or create entirely new ones on the fly.", style="text-align: center; color: #64748b; margin-bottom: 30px;"),
            form, 
            cancel_link,
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 75vh;"
        )
    ), cls="container")


@rt('/books/{book_uid}/tags/add')
async def post(book_uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
        
    form_data = await request.form()
    
    existing_tags = form_data.getlist("existing_tags") 
    new_tags_str = form_data.get("new_tags", "")
    
    new_tags = [t.strip() for t in new_tags_str.split(",") if t.strip()]
    all_tag_names = list(set(existing_tags + new_tags))
    
    if not all_tag_names:
        return Titled("Selection Required", Main(
            Div(
                H3("⚠️ No Tags Provided", style="color: #d97706; margin-bottom: 10px;"),
                P("Please select at least one existing tag or type a new one.", style="color: #475569; margin-bottom: 25px;"),
                A("Try Again", href=f"{frontend_prefix}/books/{book_uid}/tags/add", cls="button secondary outline", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fffbeb; border: 1px solid #fcd34d; border-radius: 12px;"
            )
        ), cls="container")

    payload = {
        "tags": [{"name": name} for name in all_tag_names]
    }
    
    api_url = f"{current_url}{backend_prefix}/tags/books/{book_uid}/tags"
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        api_response = await client.post(api_url, json=payload, headers=headers)
        
    if api_response.status_code in (200, 201):
        return RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
    else:
        try:
            error_msg = api_response.json().get("message", "Failed to add tags.")
        except Exception:
            error_msg = f"Server Error {api_response.status_code}: Something went wrong."
            
        return Titled("Error", Main(
            Div(
                H3("⚠️ Could Not Add Tags", style="color: #dc2626; margin-bottom: 10px;"),
                P(error_msg, style="color: #475569; margin-bottom: 25px;"),
                A("Try Again", href=f"{frontend_prefix}/books/{book_uid}/tags/add", cls="button primary", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px; margin-bottom: 10px;"),
                A("Cancel", href=f"{frontend_prefix}/books", cls="button secondary outline", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fef2f2; border: 1px solid #f87171; border-radius: 12px;"
            )
        ), cls="container")

# ==========================================
# VIEW TAGS FOR A BOOK (HTMX Snippet)
# ==========================================

@rt('/books/{book_uid}/tags')
async def get(book_uid: uuid.UUID, request: Request):
    headers = get_auth_headers(request)
    if not headers:
        return P("Please log in to view tags.", style="color: #dc2626; font-size: 0.85rem;")
        
    api_url = f"{current_url}{backend_prefix}/books/{book_uid}/tags" 
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        api_response = await client.get(api_url, headers=headers)
        
    if api_response.status_code != 200:
        return P("⚠️ Could not load tags.", style="color: #64748b; font-size: 0.85rem;")
        
    tags_data = api_response.json()
    
    if not tags_data:
        return P("No tags added yet.", style="font-style: italic; color: #94a3b8; font-size: 0.85rem;")
    
    # Render Tags as a responsive wrap of stylish "Pills" instead of a vertical list!
    tags_list = Div(*[
        Span(
            str(tag.get("name", tag)) if isinstance(tag, dict) else str(tag), 
            style="display: inline-block; background-color: #e0f2fe; color: #0369a1; padding: 4px 12px; border-radius: 16px; font-size: 0.75rem; font-weight: 600; border: 1px solid #bae6fd;"
        ) for tag in tags_data
    ], style="display: flex; flex-wrap: wrap; gap: 8px;")
    
    return tags_list