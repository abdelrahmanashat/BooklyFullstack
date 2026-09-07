# 📚 Bookly

Bookly is a comprehensive, full-stack web application designed for managing personal book collections, user reviews, and dynamic tagging. Built with a modular architecture, it features robust user authentication, integrated frontend and backend routing, and is fully configured for seamless cloud deployment and local containerization.

## ✨ Features

*   **User Authentication (`src/auth/`)**: Secure user registration, login, and session management using JWTs and Redis.
*   **Book Management (`src/books/`)**: Complete CRUD operations to add, view, update, and delete books in your personal library.
*   **Tagging System (`src/tags/`)**: Dynamically categorize and organize your books using custom tags.
*   **User Reviews (`src/reviews/`)**: Allow users to leave ratings and write reviews for specific books.
*   **Background Processing**: Asynchronous email delivery and background tasks handled via Celery (`celery_tasks.py` and `mail.py`).
*   **Hybrid Routing System**: Each module separates API logic (`routes.py`) from UI rendering (`frontend_routes.py`) for a clean, maintainable codebase.

## 🛠️ Tech Stack

*   **Backend Application**: Modular Python architecture (FastAPI & FastHTML).
*   **Database**: Relational database handling with structured models (`src/db/models.py`).
*   **Migrations**: Database schema migrations managed by Alembic (`alembic.ini` and `migrations/` directory).
*   **Caching & Message Broker**: Redis integration for high-speed data access and Celery task brokering (`src/db/redis.py`).
*   **Dependency Management**: Managed efficiently via `uv` (`pyproject.toml` and `uv.lock`).
*   **Containerization**: Fully configured Docker and Docker Compose setup for consistent environments.
*   **Testing**: Automated testing suite powered by Pytest (`src/tests/` directory).
*   **Deployment-Ready**: Configured for immediate deployment on modern cloud platforms (e.g., Render) using standard WSGI/ASGI servers.

## 📂 Project Structure

The codebase follows a highly modular, domain-driven design:

```text
BooklyFullstack/
├── alembic.ini                  # Alembic configuration for database migrations
├── migrations/                  # Database migration scripts and versions
├── compose.yml                  # Docker Compose configuration for multi-container orchestration
├── Dockerfile                   # Instructions for building the application image
├── pyproject.toml               # Python project metadata and configurations
├── requirements.txt             # Python dependencies
├── .dockerignore                # Prevents sensitive credentials from mingling into the Docker image
├── .env                         # Local environment variables
├── .env.docker                  # Container-specific environment variables
└── src/                         # Main application source code
    ├── __init__.py              # Application factory and router registration
    ├── celery_tasks.py          # Celery background task definitions
    ├── config.py                # Global configuration management
    ├── errors.py                # Global error and exception handling
    ├── mail_non_celery.py       # Native asynchronous email sending service
    ├── middleware.py            # Custom application middleware
    ├── mail.py                  # Mail configurations for Celery
    ├── utlis.py                 # Shared utility functions (Dynamic forms)
    ├── db/                      # Database configuration and core models
    │   ├── main.py              # Database connection setup
    │   ├── models.py            # Global database schema definitions
    │   └── redis.py             # Redis connection and caching logic
    ├── auth/                    # User authentication module
    ├── books/                   # Book management module
    ├── reviews/                 # Review and rating module
    ├── tags/                    # Tagging and categorization module
    └── tests/                   # Pytest test suite (e.g., test_auth.py, test_book.py)
```

*(Note: Each feature module like `auth`, `books`, `reviews`, and `tags` contains its own `routes.py`, `frontend_routes.py`, `schemas.py`, and `service.py` files to encapsulate logic perfectly.)*

## 🐳 Docker Setup (Recommended)
The easiest way to run the application is via Docker. The project includes a `compose.yml` file that orchestrates the application, database, and Redis services.

### 1. Configure the Docker Environment
Create a `.env.docker` file in the root directory. Ensure the database and Redis URLs point to the container service names (`db` and `redis`) instead of `localhost`:
```Plaintext
DOMAIN="localhost:8000"
DATABASE_URL="postgresql+asyncpg://user:password@db:5432/bookly"
REDIS_URL="redis://redis:6379/0"
POSTGRES_USER="user"
POSTGRES_PASSWORD="password"
POSTGRES_DB="bookly"
# ... other required secrets (JWT, Mail APIs, etc.)
```

### 2. Build and Run the Containers
Launch the stack using Docker Compose:
```Bash
docker compose -f up --build
```

### 3. Automatic Initialization
The `compose.yml` file handles the startup sequence automatically:
* It implements a database healthcheck (`pg_isready`) to ensure PostgreSQL is fully booted and ready to accept connections before the application starts.  
* The application container (`app`) waits for the `db` healthcheck to pass.  
* Once the database is ready, the container automatically applies all database migrations (`uv run alembic upgrade head`) and launches the web server (`uv run fastapi run src/ --host 0.0.0.0 --port 8000`).  
Access the application at `http://localhost:8000/ui`.

## 🚀 Local Execution (Without Docker)

### Prerequisites
* **Python 3.9+**.
* **PostgreSQL** (Local or cloud-hosted database URL required).
* **Redis** (required for caching and background Celery tasks).

### Installation & Setup
1. Clone the repository:
```Bash
git clone [https://github.com/abdelrahmanashat/BooklyFullstack.git](https://github.com/abdelrahmanashat/BooklyFullstack.git)
cd BooklyFullstack
```

2. Navigate to the project folder in CMD on Windows (or bash on Linux) and create and activate a virtual environment:

```Bash
python -m venv venv
venv\Scripts\activate.bat  # On Linux use `source venv/bin/activate`
```

3. Install dependencies:
The file `patch.py` is for solving an import issue with fast-mail package.

```Bash
pip install -r requirements.txt && python patch.py
```

4. Configure Environment Variables:
Create `.env` file in the root directory for local use or provide the necessary environment variables in the cloud server. Ensure you add your PostgreSQL database URL, Redis URL, and mail server credentials.

5. Run Database Migrations:
Initialize your database tables using Alembic.

```Bash
alembic upgrade head
```

### Running the Application
1. **Start the Web Server:**
Execute the application using FastAPI from the root directory. Background tasks (like emails) are handled asynchronously by the server, eliminating the need for a separate Celery worker.

```Bash
fastapi run src\
```
Navigate to your local host (e.g., `http://localhost:8000/ui`) to access the frontend UI.

2. **Start the Celery Worker (for background tasks):**
Celery handles asynchronous processes like emails.
```Bash
celery -A src.celery_tasks worker --loglevel=info --pool=solo
```

## ☁️ Deployment
Bookly is cloud-ready and can be deployed to PaaS providers like **Render**, **Heroku**, or **Railway** with minimal configuration.

1. **Provision External Services:** Ensure you have active instances of PostgreSQL and Redis running on your chosen cloud provider.

2. **Environment Variables:** Add your production database URL, Redis URL, and application secrets to your platform's environment variables settings.

3. **Start Command:** Set your production web service start command to:

```Bash
fastapi run src/
```
(Note: Alembic migrations can be run as a pre-deploy or build step depending on your hosting platform's capabilities: `alembic upgrade head`).

## 🧪 Testing
The project includes an automated test suite located in the `src/tests/` directory. It utilizes a `conftest.py` file for fixture management.

To run the tests, execute:

```Bash
pytest src/tests/
```