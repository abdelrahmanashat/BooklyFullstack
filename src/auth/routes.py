from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from datetime import timedelta, datetime

from src.db.main import get_session
from src.db.redis import add_jti_to_blocklist
from src.mail_non_celery import send_email_via_api
#from src.celery_tasks import send_email

from .schemas import (UserCreateModel, 
                      UserLoginModel, 
                      UserBookModel, 
                      EmailModel, 
                      PasswordResetRequestModel, 
                      PasswordResetConfirmModel)
from .service import UserService
from .utils import create_access_token, verify_password, create_url_safe_token, decode_url_safe_token, generate_pass_hash
from .dependencies import RefreshTokenBearer, AccessTokenBearer, get_current_user, RoleChecker

from src.errors import UserAlreadyExists, InvalidCredentials, InvalidToken, UserNotFound
from src.config import Config

from src.url_names import url_names

auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(['admin','user'])

frontend_prefix = url_names.frontend_url
backend_prefix = url_names.version_prefix

REFRESH_TOKEN_EXPIRY = 2    

@auth_router.post('/send_mail')
async def send_mail(emails:EmailModel, bg_tasks: BackgroundTasks):
    emails = emails.addresses
    html_message = "<h1>Welcome to the app</h1>"
    subject = "Welcome to our app"
    #send_email.delay(emails, subject, html)
    bg_tasks.add_task(send_email_via_api, emails, subject, html_message)
    return {"message":"Email sent successfully"}

@auth_router.post('/send_verification', status_code=status.HTTP_200_OK)
async def create_user_account(user_data:PasswordResetRequestModel, bg_tasks: BackgroundTasks, session:AsyncSession = Depends(get_session)):
    email = user_data.email
    user_exists = await user_service.user_exists(email, session)
    if not user_exists: 
        raise UserNotFound()
    
    token = create_url_safe_token({"email":email})
    link = f"http://{Config.DOMAIN}{frontend_prefix}/verification-done/{token}"
    html_message = f"""
    <h1>Verify your email</h1>
    <p>Please click this <a href="{link}">link</a> to verify your email</p>
    """
    emails = [email]
    subject="Verify your email"
    #send_email.delay(emails, subject, html_message)
    bg_tasks.add_task(send_email_via_api, emails, subject, html_message)
    
    return {
        "message" : f"Check your email: {email} to verify your account"
    }

@auth_router.post('/signup', status_code=status.HTTP_201_CREATED)
async def create_user_account(user_data:UserCreateModel, bg_tasks: BackgroundTasks, session:AsyncSession = Depends(get_session)):
    email = user_data.email
    user_exists = await user_service.user_exists(email, session)
    if user_exists: 
        raise UserAlreadyExists()
    new_user = await user_service.create_user(user_data, session)
    
    token = create_url_safe_token({"email":email})
    link = f"http://{Config.DOMAIN}{frontend_prefix}/verification-done/{token}"
    html_message = f"""
    <h1>Verify your email</h1>
    <p>Please click this <a href="{link}">link</a> to verify your email</p>
    """
    emails = [email]
    subject="Verify your email"
    #send_email.delay(emails, subject, html_message)
    bg_tasks.add_task(send_email_via_api, emails, subject, html_message)
    
    return {
        "message" : f"Account Created! Check your email: {email} to verify your account",
        "user" : new_user
    }
        
@auth_router.get('/verify/{token}')
async def verify_user_account(token:str, session:AsyncSession = Depends(get_session)):
    token_data = decode_url_safe_token(token)
    user_email = token_data.get('email')
    if user_email:
        user = await user_service.get_user(user_email, session)
        if not user:
            raise UserNotFound()
       
        await user_service.update_user(user, {'is_verified':True}, session)
        return JSONResponse(
            content={
                "message":"Account is verified successfully!"
            },
            status_code=status.HTTP_200_OK
        )
    return JSONResponse(
        content={
            "message":"Error occured during verification"
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

@auth_router.post('/login')
async def login_users(login_data:UserLoginModel, session:AsyncSession = Depends(get_session)):
    
    email = login_data.email
    password = login_data.password
    
    user = await user_service.get_user(email, session)
    if user is not None:
        password_valid = verify_password(password, user.password_hash)
        if password_valid:
            access_token = create_access_token(user_data={
                'email' : user.email,
                'user_uid' : str(user.uid),
                'role' : user.role
                }
            )
            refresh_token = create_access_token(
                user_data={
                'email' : user.email,
                'user_uid' : str(user.uid)
                },
                refresh=True,
                expiry=timedelta(days=REFRESH_TOKEN_EXPIRY)
            )
            return JSONResponse(
                content={
                    'message' : "Login Successful",
                    'access_token' : access_token,
                    'refresh_token' : refresh_token,
                    'user' : {
                        'email' : user.email,
                        'uid' : str(user.uid),
                        'is_verified' : user.is_verified
                    }
                }
            )
    
    raise InvalidCredentials()

@auth_router.get('/refresh_token')
async def get_new_access_token(token_details:dict = Depends(RefreshTokenBearer())):
    expiry_timestamp = token_details["exp"]
    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_acces_token = create_access_token(token_details["user"])
        return JSONResponse(
            content={
                "access_token" : new_acces_token
            }
        )
    
    return InvalidToken()

@auth_router.get('/me', response_model=UserBookModel)
async def get_current_user(user = Depends(get_current_user), _:bool=Depends(role_checker)):
    return user

@auth_router.get('/logout')
async def revoke_token(token_details:dict=Depends(AccessTokenBearer())):
    jti = token_details["jti"]
    await add_jti_to_blocklist(jti)
    return JSONResponse(content={
        "message":"Logout successfully"
        },
        status_code=status.HTTP_200_OK
    )
    
@auth_router.post('/password-reset-request')
async def password_reset_request(email_data:PasswordResetRequestModel, bg_tasks: BackgroundTasks, session:AsyncSession = Depends(get_session)):
    email = email_data.email
    user_exists = await user_service.user_exists(email, session)
    if not user_exists: 
        raise UserNotFound()
    
    token = create_url_safe_token({"email":email})
    link = f"http://{Config.DOMAIN}{frontend_prefix}/password-reset-confirm/{token}"
    html_message = f"""
    <h1>Password reset request</h1>
    <p>Please click this <a href="{link}">link</a> to confirm resetting your password</p>
    """
    emails = [email]
    subject="Password Reset Request"
    #send_email.delay(emails, subject, html_message)
    bg_tasks.add_task(send_email_via_api, emails, subject, html_message)
    
    return JSONResponse(content={"message" : f"Check your email: {email} to confirm password reset"},
                        status_code=status.HTTP_200_OK)

@auth_router.post('/password-reset-confirm/{token}')
async def reset_account_password(token:str, passwords:PasswordResetConfirmModel, session:AsyncSession = Depends(get_session)):
    new_password = passwords.new_password
    confirm_new_password = passwords.confirm_new_password
    if(new_password != confirm_new_password):
        raise HTTPException(detail="Paswords don't match", status_code=status.HTTP_400_BAD_REQUEST)
    
    token_data = decode_url_safe_token(token)
    user_email = token_data.get('email')
    if user_email:
        user = await user_service.get_user(user_email, session)
        if not user:
            raise UserNotFound()
       
        password_hash = generate_pass_hash(new_password)
        await user_service.update_user(user, {"password_hash": password_hash}, session)
        return JSONResponse(
            content={
                "message":"Password reset successfully!"
            },
            status_code=status.HTTP_200_OK
        )
    return JSONResponse(
        content={
            "message":"Error occured password reset"
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )