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

# ==========================================
# SIGN IN ROUTES
# ==========================================

@rt('/')
def get():
    # 1. Styled Form Container with Flexbox and Spacing
    sign_in_form = Form(
        Div(
            Label(Span("Email", style="font-weight: 600; color: #334155;"), 
                  Input(name="email", type="email", placeholder="you@example.com", required=True, style="margin-top: 0.4rem; padding: 0.6rem; border-radius: 6px; width: 100%;")),
            style="margin-bottom: 1.25rem;"
        ),
        
        Div(
            Label(
                Span("Password", style="font-weight: 600; color: #334155;"), 
                # Wrapper div with position relative to absolute-position the button inside it
                Div(
                    Input(id="password-input", type="password", name="password", placeholder="••••••••", required=True, 
                          style="margin-top: 0.4rem; padding: 0.6rem; padding-right: 2.5rem; border-radius: 6px; width: 100%;"),
                    # Toggle Button acting as an eye icon
                    Button(
                        "👁️", 
                        type="button", 
                        id="toggle-password",
                        onclick="""
                            const passwordInput = document.getElementById('password-input');
                            if (passwordInput.type === 'password') {
                                passwordInput.type = 'text';
                                this.textContent = '🙈';
                            } else {
                                passwordInput.type = 'password';
                                this.textContent = '👁️';
                            }
                        """,
                        style="position: absolute; right: 10px; top: 55%; transform: translateY(-50%); background: none; border: none; padding: 0; cursor: pointer; font-size: 1.2rem; box-shadow: none;"
                    ),
                    style="position: relative; width: 100%;"
                )
            ),
            style="margin-bottom: 1.5rem;"
        ),
        
        Button("Sign In", type="submit", cls="button primary", style="width: 100%; padding: 0.75rem; font-size: 1.05rem; font-weight: 600; border-radius: 8px; cursor: pointer;"),
        
        action=f"{frontend_prefix}/login", 
        method="post",
        style="width: 100%; max-width: 400px; padding: 30px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);"
    )

    # 2. Distinct Secondary Links
    extra_links = Div(
        P("Don't have an account? ", A("Sign up", href=f"{frontend_prefix}/signup", style="font-weight: 600; color: #2563eb;")),
        A("Forgot your password?", href=f"{frontend_prefix}/forgot-password", style="font-size: 0.9rem; color: #64748b; text-decoration: underline;"),
        style="margin-top: 25px; text-align: center; display: flex; flex-direction: column; gap: 12px;"
    )

    # 3. Centered Page Layout
    return Titled("Sign In to Bookly", Main(
    # Explicitly create and center the main page heading
    
    Div(
        H2("Welcome Back", style="text-align: center; color: #1e293b; margin-bottom: 8px;"),
        P("Please enter your details to sign in.", style="text-align: center; color: #64748b; margin-bottom: 30px;"),
        
        # Keep your form strictly left-aligned so inputs behave normally
        Div(
            sign_in_form, 
            extra_links,
            style="text-align: left; width: 100%; max-width: 400px;"
        ),
        
        style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 65vh;"
    ),
    ),cls="container"
)

@rt('/login')
async def post(email: str, password: str):
    api_url = f"{current_url}{backend_prefix}/auth/login"
    payload = {"email": email, "password": password}
    
    async with httpx.AsyncClient() as client:
        api_response = await client.post(api_url, json=payload)
        
    # 4. Styled Error Card 
    if api_response.status_code != 200:
        return Titled("Sign In Failed", Main(
            Div(
                H3("⚠️ Invalid Credentials", style="color: #dc2626; margin-bottom: 10px;"),
                P("The email or password you entered is incorrect.", style="color: #475569; margin-bottom: 25px;"),
                A("Try Again", href=f"{frontend_prefix}/", cls="button primary", style="width: 100%; display: inline-block; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 400px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fef2f2; border: 1px solid #f87171; border-radius: 12px;"
            )
        ), cls="container")
        
    token_data = api_response.json()
    token = token_data.get("access_token") 
    
    is_verified = (token_data.get("user")).get("is_verified")
    
    # 5. Full-page Warning Layout for Unverified Users
    if not is_verified:
        verify_button = Button(
            "📧 Send Verification Email", 
            hx_post=f"{frontend_prefix}/email-verification/{email}", 
            hx_target="#email-result", 
            hx_swap="innerHTML",
            cls="button primary",
            style="width: 100%; padding: 0.75rem; font-size: 1rem; border-radius: 8px; margin-bottom: 15px;"
        )
        
        return Titled("Account Verification", Main(
            Div(
                H3("Action Required", style="color: #d97706; margin-bottom: 10px;"),
                P("Your account hasn't been verified yet. Please check your inbox or request a new verification link below.", style="color: #475569; margin-bottom: 25px; line-height: 1.5;"),
                Div(verify_button, id="email-result"),
                Div(A("Back to Login", href=f"{frontend_prefix}/", cls="button secondary outline", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;")),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fffbeb; border: 1px solid #fcd34d; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);"
            )
        ), cls="container")
    
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
    
    # 1. HTMX Partial - Error Alert (Replaces the button seamlessly)
    if api_response.status_code != 200:
        return Div(
            P("⚠️ Failed to send verification email. Please try again later.", style="color: #991b1b; margin: 0; font-weight: 600;"),
            style="background-color: #fef2f2; border: 1px solid #f87171; padding: 15px; border-radius: 8px; text-align: center;"
        )
        
    # 2. HTMX Partial - Success Alert (Replaces the button seamlessly)
    else:
        return Div(
            P(f"✅ Verification link sent to ", B(email), style="color: #166534; margin: 0; font-weight: 600;"),
            P("Please check your inbox and spam folder.", style="color: #15803d; font-size: 0.9em; margin-top: 5px;"),
            style="background-color: #f0fdf4; border: 1px solid #4ade80; padding: 15px; border-radius: 8px; text-align: center;"
        )

@rt('/verification-done/{token}')
async def get(token:str):
    api_url = f"{current_url}{backend_prefix}/auth/verify/{token}"
    
    async with httpx.AsyncClient() as client:
        api_response = await client.get(api_url)
    
    # 3. Full Page Load - Error Landing Page
    if api_response.status_code != 200:
        return Titled("Verification Failed", Main(
            Div(
                H1("❌", style="font-size: 3.5rem; margin-bottom: 15px; line-height: 1;"),
                H2("Link Invalid or Expired", style="color: #dc2626; margin-bottom: 10px;"),
                P("We couldn't verify your email. The link may have expired or has already been used.", style="color: #475569; margin-bottom: 25px; line-height: 1.5;"),
                A("Back to Login", href=f"{frontend_prefix}/", cls="button secondary outline", style="display: block; width: 100%; padding: 0.75rem; border-radius: 8px; text-align: center;"),
                style="max-width: 450px; margin: 15vh auto; padding: 40px 30px; text-align: center; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);"
            )
        ), cls="container")
        
    # 4. Full Page Load - Success Landing Page
    else:
        return Titled("Verification Successful", Main(
            Div(
                H1("🎉", style="font-size: 3.5rem; margin-bottom: 15px; line-height: 1;"),
                H2("Email Verified!", style="color: #16a34a; margin-bottom: 10px;"),
                P("Thank you for confirming your email address. Your account is now fully active.", style="color: #475569; margin-bottom: 25px; line-height: 1.5;"),
                A("Continue to Sign In", href=f"{frontend_prefix}/", cls="button primary", style="display: block; width: 100%; padding: 0.75rem; border-radius: 8px; text-align: center; font-weight: 600;"),
                style="max-width: 450px; margin: 15vh auto; padding: 40px 30px; text-align: center; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);"
            )
        ), cls="container")

# ==========================================
# SIGN UP ROUTES
# ==========================================

@rt('/signup')
def get():
    # 1. The form itself is already perfectly styled by our upgraded utility!
    signup_form = generate_form_from_model(
        model=UserCreateModel, 
        submit_url=f"{frontend_prefix}/signup",
        submit_text="Create Account"
    )
    
    # 2. Add a clear secondary link back to the login page
    extra_links = Div(
        P("Already have an account? ", A("Sign in here", href=f"{frontend_prefix}/", style="font-weight: 600; color: #2563eb;")),
        style="margin-top: 25px; text-align: center;"
    )
    
    # 3. Center the layout and add welcoming headers
    return Titled("Sign Up for Bookly", Main(
        Div(
            H2("Join Bookly", style="text-align: center; color: #1e293b; margin-bottom: 8px;"),
            P("Fill in your details below to get started.", style="text-align: center; color: #64748b; margin-bottom: 30px;"),
            signup_form,
            extra_links,
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 75vh;"
        )
    ), cls="container")

@rt('/signup')
@accept_model_fields(UserCreateModel)
async def post(**kwargs):
    api_url = f"{current_url}{backend_prefix}/auth/signup"
    print("api_url: ", api_url)
    
    payload = {key: val for key, val in kwargs.items()}
    
    timeout = 30.0 # For email to be sent
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        api_response = await client.post(api_url, json=payload)
        
    if api_response.status_code in (200, 201):
        # 4. Styled Success Landing Page
        return Titled("Account Created", Main(
            Div(
                H1("✨", style="font-size: 3.5rem; margin-bottom: 15px; line-height: 1;"),
                H2("Welcome to Bookly!", style="color: #16a34a; margin-bottom: 10px;"),
                P("Your account has been created successfully. We've sent a verification link to your email address.", style="color: #475569; margin-bottom: 25px; line-height: 1.5;"),
                A("Go to Sign In", href=f"{frontend_prefix}/", cls="button primary", style="display: block; width: 100%; padding: 0.75rem; border-radius: 8px; text-align: center; font-weight: 600;"),
                style="max-width: 450px; margin: 15vh auto; padding: 40px 30px; text-align: center; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);"
            )
        ), cls="container")
    else:
        try:
            error_detail = api_response.json().get("message", "Failed to create account.")
        except Exception:
            error_detail = f"Server Error {api_response.status_code}: Something went wrong in the background."
            print(f"RAW BACKEND ERROR: {api_response.text}") 
            
        # 5. Styled Error Card matching the Login flow
        return Titled("Registration Failed", Main(
            Div(
                H3("⚠️ Sign Up Error", style="color: #dc2626; margin-bottom: 10px;"),
                P(error_detail, style="color: #475569; margin-bottom: 25px;"),
                A("Try Again", href=f"{frontend_prefix}/signup", cls="button primary", style="width: 100%; display: inline-block; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fef2f2; border: 1px solid #f87171; border-radius: 12px;"
            )
        ), cls="container")
        
# ==========================================
# FORGOT PASSWORD ROUTES
# ==========================================

@rt('/forgot-password')
def get():
    forgotpass_form = generate_form_from_model(
        model=PasswordResetRequestModel, 
        submit_url=f"{frontend_prefix}/forgot-password",
        submit_text="Send Reset Link"
    )
    
    extra_links = Div(
        A("← Back to Login", href=f"{frontend_prefix}/", style="font-size: 0.95rem; color: #64748b; text-decoration: none; font-weight: 600;"),
        style="margin-top: 20px; text-align: center;"
    )
    
    return Titled("Forgot Password", Main(
        Div(
            H2("Reset Password", style="text-align: center; color: #1e293b; margin-bottom: 8px;"),
            P("Enter your email address and we'll send you a link to reset your password.", style="text-align: center; color: #64748b; margin-bottom: 30px; line-height: 1.5;"),
            forgotpass_form, 
            extra_links,
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 75vh;"
        )
    ), cls="container")


@rt('/forgot-password')
@accept_model_fields(PasswordResetRequestModel)
async def post(**kwargs):
    api_url = f"{current_url}{backend_prefix}/auth/password-reset-request"
    payload = {key: val for key, val in kwargs.items()}
    
    timeout = 30.0 
    async with httpx.AsyncClient(timeout=timeout) as client:
        await client.post(api_url, json=payload)
    
    email = kwargs.pop("email")
        
    return Titled("Reset Link Sent", Main(
        Div(
            H1("📬", style="font-size: 3.5rem; margin-bottom: 15px; line-height: 1;"),
            H2("Check Your Inbox", style="color: #2563eb; margin-bottom: 10px;"),
            P("If an account is associated with ", B(email), ", you will receive a secure reset link shortly.", style="color: #475569; margin-bottom: 25px; line-height: 1.5;"),
            A("Return to Login", href=f"{frontend_prefix}/", cls="button primary", style="display: block; width: 100%; padding: 0.75rem; border-radius: 8px; text-align: center; font-weight: 600;"),
            style="max-width: 450px; margin: 15vh auto; padding: 40px 30px; text-align: center; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);"
        )
    ), cls="container")

    
# ==========================================
# PASSWORD RESET CONFIRM ROUTES
# ==========================================

@rt('/password-reset-confirm/{token}')
def get(token:str):
    newpass_form = generate_form_from_model(
        model=PasswordResetConfirmModel, 
        submit_url=f"{frontend_prefix}/password-reset-confirm/{token}",
        submit_text="Update Password"
    )
    
    return Titled("Create New Password", Main(
        Div(
            H2("Set New Password", style="text-align: center; color: #1e293b; margin-bottom: 8px;"),
            P("Please enter and confirm your new password below.", style="text-align: center; color: #64748b; margin-bottom: 30px;"),
            newpass_form, 
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 75vh;"
        )
    ), cls="container")


@rt('/password-reset-confirm/{token}')
@accept_model_fields(PasswordResetConfirmModel)
async def post(token: str, **kwargs):
    payload = {key: val for key, val in kwargs.items()}
    
    # Validation Error Layout
    if payload.get("new_password") != payload.get("confirm_new_password"):
        return Titled("Passwords Mismatch", Main(
            Div(
                H3("⚠️ Passwords Do Not Match", style="color: #d97706; margin-bottom: 10px;"),
                P("The new password and confirmation password must be exactly the same.", style="color: #475569; margin-bottom: 25px;"),
                A("Try Again", href=f"{frontend_prefix}/password-reset-confirm/{token}", cls="button secondary outline", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fffbeb; border: 1px solid #fcd34d; border-radius: 12px;"
            )
        ), cls="container")
    
    api_url = f"{current_url}{backend_prefix}/auth/password-reset-confirm/{token}"
        
    async with httpx.AsyncClient() as client:
        api_response = await client.post(api_url, json=payload)
    
    # Success Layout
    if api_response.status_code == 200:
        return Titled("Password Updated", Main(
            Div(
                H1("🔒", style="font-size: 3.5rem; margin-bottom: 15px; line-height: 1;"),
                H2("Password Reset Successful", style="color: #16a34a; margin-bottom: 10px;"),
                P("Your password has been securely updated. You can now use it to sign in to your account.", style="color: #475569; margin-bottom: 25px; line-height: 1.5;"),
                A("Go to Login", href=f"{frontend_prefix}/", cls="button primary", style="display: block; width: 100%; padding: 0.75rem; border-radius: 8px; text-align: center; font-weight: 600;"),
                style="max-width: 450px; margin: 15vh auto; padding: 40px 30px; text-align: center; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);"
            )
        ), cls="container")
        
    # API Error Layout
    else:
        error_msg = api_response.json().get("message", "Failed to reset password. The link might be expired.")
        return Titled("Reset Failed", Main(
            Div(
                H3("⚠️ Reset Error", style="color: #dc2626; margin-bottom: 10px;"),
                P(error_msg, style="color: #475569; margin-bottom: 25px;"),
                A("Request New Link", href=f"{frontend_prefix}/forgot-password", cls="button primary", style="display: block; width: 100%; text-align: center; padding: 0.75rem; border-radius: 8px;"),
                style="max-width: 450px; margin: 10vh auto; padding: 30px; text-align: center; background-color: #fef2f2; border: 1px solid #f87171; border-radius: 12px;"
            )
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