from fastapi import FastAPI
from src.books.routes import book_router
from src.auth.routes import auth_router
from src.reviews.routes import review_router
from src.tags.routes import tags_router
from .errors import register_all_errors
from .middleware import register_middleware
from .url_names import url_names

# Initialize Backend

version_prefix = url_names.version_prefix

app = FastAPI(
    title=url_names.title,
    description=url_names.description,
    version=url_names.version,
    license_info=url_names.license_info,
    contact=url_names.contact,
    terms_of_service=url_names.terms_of_service,
    openapi_url=url_names.openapi_url,
    docs_url=url_names.docs_url,
    redoc_url=url_names.redoc_url
)

register_all_errors(app)
register_middleware(app)

app.include_router(book_router, prefix=f"{version_prefix}/book", tags=['books'])
app.include_router(auth_router, prefix=f"{version_prefix}/auth", tags=['auth'])
app.include_router(review_router, prefix=f"{version_prefix}/reviews", tags=['reviews'])
app.include_router(tags_router, prefix=f"{version_prefix}/tags", tags=["tags"])

# Initialize Frontend

from fasthtml.common import fast_app

# Initialize the FastHTML app and router
ui_app, rt = fast_app()

# Import frontend routes
import src.auth.frontend_routes
import src.books.frontend_routes

# Mount the FastHTML application under the "/ui" path
app.mount(url_names.frontend_url, ui_app)