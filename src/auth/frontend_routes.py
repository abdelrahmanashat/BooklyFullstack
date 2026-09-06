from fasthtml.common import *
import httpx
from fastapi.responses import RedirectResponse
from src.url_names import url_names
from src.config import Config
from src.utlis import generate_form_from_model, accept_model_fields
from src.auth.schemas import UserCreateModel, PasswordResetRequestModel, PasswordResetConfirmModel
from src import rt

# Dynamically choose http or https
if "localhost" in Config.DOMAIN or "127.0.0.1" in Config.DOMAIN:
    scheme = "http"
else:
    scheme = "https"

current_url = f"{scheme}://{Config.DOMAIN}"
frontend_prefix = url_names.frontend_url
backend_prefix = url_names.version_prefix

@rt('/')
def get():
    sign_in_form = Form(
        # The names MUST be 'email' and 'password' for FastAPI to accept them
        Label("Email", 
              Input(name="email", placeholder="Enter your email", required=True)),
        
        Label("Password", 
              Input(type="password", name="password", placeholder="Enter your password", required=True)),
        
        Button("Sign In", type="submit"),
        
        # Point this to your existing FastAPI route
        action=f"{frontend_prefix}/login", 
        method="post"
    )

    # Added the links below the form
    extra_links = Div(
        A("Forgot your password?", href=f"{frontend_prefix}/forgot-password", style="margin-right: 15px;"),
        A("Sign up", href=f"{frontend_prefix}/signup"),
        style="margin-top: 15px; text-align: center;"
    )

    return Titled("Sign In to Bookly", Main(sign_in_form, extra_links), cls="container")

@rt('/login')
async def post(email: str, password: str):
    
    # 1. Take the Form data and send it as JSON to your existing API route
    # (Assuming your API is running on localhost:8000)
    api_url = f"{current_url}{backend_prefix}/auth/login"
    payload = {"email": email, "password": password}
    
    async with httpx.AsyncClient() as client:
        api_response = await client.post(api_url, json=payload)
        
    # 2. Check if your API accepted it
    if api_response.status_code != 200:
        return Titled("Sign In", Main(P("Invalid credentials"), A("Back", href=f"{frontend_prefix}/")))
        
    # 3. Extract the token from your API's JSON response
    token_data = api_response.json()
    token = token_data.get("access_token") # Adjust based on your API's JSON key
    
    is_verified = (token_data.get("user")).get("is_verified")
    if not is_verified:
        verify_button = Button(
            "Send Verification Email", 
            hx_post=f"{frontend_prefix}/email-verification/{email}", 
            hx_target="#email-result", 
            hx_swap="innerHTML"
        )
        
        return Div(
            verify_button,
            id="email-result" # The response from your Python function will appear here
        )
    
    # 4. Set the cookie and redirect the browser
    ui_response = RedirectResponse(url=f"{frontend_prefix}/books", status_code=303)
    ui_response.set_cookie(key="access_token", value=token, httponly=True)
    
    return ui_response

# ==========================================
# VERIFICATION ROUTES
# ==========================================

@rt('/email-verification/{email}')
async def post(email:str):
    api_url = f"{current_url}{backend_prefix}/auth/send_verification"
    payload = {"email": email}
    
    timeout = 30.0 # For email to be sent
    async with httpx.AsyncClient(timeout=timeout) as client:
        api_response = await client.post(api_url, json=payload)
    
    # 2. Check if your API accepted it
    if api_response.status_code != 200:
        return Titled("Sign In", Main(P("Something went wrong!"), A("Back", href=f"{frontend_prefix}/")))
    else:
        return Titled("Sign In", Main(P(f"Verification sent to {email}!"), A("Back", href=f"{frontend_prefix}/")))

@rt('/verification-done/{token}')
async def get(token:str):
    api_url = f"{current_url}{backend_prefix}/auth/verify/{token}"
    
    async with httpx.AsyncClient() as client:
        api_response = await client.get(api_url)
    
    if api_response.status_code != 200:
        return Titled("Verification", Main(P("Something went wrong!"), A("Back", href=f"{frontend_prefix}/")))
    else:
        return Titled("Verification", Main(P("Verification successful!")))

# ==========================================
# SIGN UP ROUTES
# ==========================================

@rt('/signup')
def get():
    # Instantly generates the form matching your exact backend schema!
    signup_form = generate_form_from_model(
        model=UserCreateModel, 
        submit_url=f"{frontend_prefix}/signup",
        submit_text="Create Account"
    )
    
    return Titled("Sign Up for Bookly", Main(signup_form), cls="container")

@rt('/signup')
@accept_model_fields(UserCreateModel)
async def post(**kwargs):
    # Adjust this URL to match your FastAPI signup route exactly
    api_url = f"{current_url}{backend_prefix}/auth/signup"
    print("api_url: ", api_url)
    
    payload = {key: val for key, val in kwargs.items()}
    
    timeout = 30.0 # For email to be sent
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        api_response = await client.post(api_url, json=payload)
        
    if api_response.status_code in (200, 201):
        return Titled("Success", Main(
            P("Account created successfully!"), 
            A("Go to Login", href=f"{frontend_prefix}/", cls="button")
        ), cls="container")
    else:
        # Safely attempt to parse JSON, fallback if it is an HTML error page
        try:
            error_detail = api_response.json().get("message", "Failed to create account.")
        except Exception:
            error_detail = f"Server Error {api_response.status_code}: Something went wrong in the background."
            # Print the raw text to your Render logs so you can see the real error!
            print(f"RAW BACKEND ERROR: {api_response.text}") 
            
        return Titled("Error", Main(
            P(error_detail, style="color: red;"), 
            A("Try Again", href=f"{frontend_prefix}/signup", cls="button secondary")
        ), cls="container")
        
# ==========================================
# FORGOT PASSWORD ROUTES
# ==========================================

@rt('/forgot-password')
def get():
    forgotpass_form = generate_form_from_model(
            model=PasswordResetRequestModel, 
            submit_url=f"{frontend_prefix}/forgot-password",
            submit_text="Submit"
        )
    
    return Titled("Forgot Password", 
        Main(
            forgotpass_form, 
            P(A("Back to Login", href=f"{frontend_prefix}/"), style="margin-top: 15px;")
        ), 
        cls="container"
    )

@rt('/forgot-password')
@accept_model_fields(PasswordResetRequestModel)
async def post(**kwargs):
    # Adjust this URL to match your FastAPI password reset request route
    api_url = f"{current_url}{backend_prefix}/auth/password-reset-request"
    payload = {key: val for key, val in kwargs.items()}
    
    timeout = 30.0 # For email to be sent
    async with httpx.AsyncClient(timeout=timeout) as client:
        # We fire the request but typically don't expose if the email exists for security reasons
        await client.post(api_url, json=payload)
    
    email = kwargs.pop("email")
        
    return Titled("Reset Requested", 
        Main(
            P(f"If an account is associated with {email}, you will receive a reset link shortly."), 
            A("Back to Login", href=f"{frontend_prefix}/", cls="button")
        ), 
        cls="container"
    )
    
@rt('/password-reset-confirm/{token}')
def get(token:str):
    newpass_form = generate_form_from_model(
            model=PasswordResetConfirmModel, 
            submit_url=f"{frontend_prefix}/password-reset-confirm/{token}",
            submit_text="Submit"
        )
    
    return Titled("Enter new Password", 
        Main(
            newpass_form, 
            P(A("Back to Login", href=f"{frontend_prefix}/"), style="margin-top: 15px;")
        ), 
        cls="container"
    )

@rt('/password-reset-confirm/{token}')
@accept_model_fields(PasswordResetConfirmModel)
async def post(token: str, **kwargs):
    payload = {key: val for key, val in kwargs.items()}
    
    if payload["new_password"] != payload["confirm_new_password"]:
        return Titled("Error", Main(
            P("Passwords do not match. Please try again.", style="color: red;"),
            A("Back", href=f"{frontend_prefix}/password-reset-confirm/{token}", cls="button secondary")
        ), cls="container")
    
    api_url = f"{current_url}{backend_prefix}/auth/password-reset-confirm/{token}"
        
    async with httpx.AsyncClient() as client:
        api_response = await client.post(api_url, json=payload)
    
    if api_response.status_code == 200:
        return Titled("Success", Main(
            P("Your password has been successfully reset!"),
            A("Go to Login", href=f"{frontend_prefix}/", cls="button")
        ), cls="container")
    else:
        # Extract the error detail from the backend if available
        error_msg = api_response.json().get("message", "Failed to reset password.")
        return Titled("Error", Main(
            P(error_msg, style="color: red;"),
            A("Try Again", href=f"{frontend_prefix}/password-reset-confirm/{token}", cls="button secondary")
        ), cls="container")

# ==========================================
# LOGOUT ROUTE
# ==========================================

@rt('/logout')
async def logout(request: Request):
    # Retrieve the token to blacklist it on the backend
    token = request.cookies.get("access_token")
    if token:
        api_url = f"{current_url}{backend_prefix}/auth/logout"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(follow_redirects=True) as client:
            await client.get(api_url, headers=headers)
            
    # Clear the UI cookie and return to login screen
    ui_response = RedirectResponse(url=f"{frontend_prefix}/", status_code=303)
    ui_response.delete_cookie(key="access_token")
    return ui_response