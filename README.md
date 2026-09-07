# 📚 Bookly

Bookly is a comprehensive, full-stack web application designed for managing personal book collections, user reviews, and dynamic tagging. Built with a modular architecture, it features robust user authentication, integrated frontend and backend routing, and is fully configured for seamless cloud deployment.

## ✨ Features

*   **User Authentication (`src/auth/`)**: Secure user registration, login, and session management using JWTs and Redis.
*   **Book Management (`src/books/`)**: Complete CRUD operations to add, view, update, and delete books in your personal library.
*   **Tagging System (`src/tags/`)**: Dynamically categorize and organize your books using custom tags.
*   **User Reviews (`src/reviews/`)**: Allow users to leave ratings and write reviews for specific books.
*   **Email Notifications**: Asynchronous email delivery handled natively without the need for external task workers like Celery.
*   **Hybrid Routing System**: Each module separates API logic (`routes.py`) from UI rendering (`frontend_routes.py`) for a clean, maintainable codebase.

## 🛠️ Tech Stack

*   **Backend Application**: Modular Python architecture (FastAPI & FastHTML).
*   **Database**: Relational database handling with structured models (`src/db/models.py`).
*   **Migrations**: Database schema migrations managed by Alembic (`alembic.ini` and `migrations/` directory).
*   **Caching & Session Management**: Redis integration for high-speed data access and token management (`src/db/redis.py`).
*   **Testing**: Automated testing suite powered by Pytest (`src/tests/` directory).
*   **Deployment-Ready**: Configured for immediate deployment on modern cloud platforms (e.g., Render) using standard WSGI/ASGI servers.

## 📂 Project Structure

The codebase follows a highly modular, domain-driven design:

```text
BooklyFullstack/
├── alembic.ini                  # Alembic configuration for database migrations
├── migrations/                  # Database migration scripts and versions
├── pyproject.toml               # Python project metadata and configurations
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables configuration
└── src/                         # Main application source code
    ├── __init__.py              # Application factory and router registration
    ├── config.py                # Global configuration management
    ├── mail_non_celery.py       # Native asynchronous email sending service
    ├── middleware.py            # Custom application middleware
    ├── errors.py                # Global error and exception handling
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

## 🚀 Getting Started

### Prerequisites
* **Python 3.9+**.
* **PostgreSQL** (Local or cloud-hosted database URI required).
* **Redis** (Local or cloud-hosted Redis instance required for caching).

### Installation & Setup
1. Clone the repository:
```Bash
git clone [https://github.com/abdelrahmanashat/BooklyFullstack.git](https://github.com/abdelrahmanashat/BooklyFullstack.git)
cd BooklyFullstack
```

2. Create and activate a virtual environment:

```Bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install dependencies:
The file `patch.py` is for solving an import issue with fast-mail package.

```Bash
pip install -r requirements.txt && python patch.py
```

4. Configure Environment Variables:
Create `.env` file in the root directory for local use or provide the necessary environment variables in the cloud server. Ensure you add your PostgreSQL database URI, Redis URI, and mail server credentials.

5. Run Database Migrations:
Initialize your database tables using Alembic.

```Bash
alembic upgrade head
```

### Running the Application
#### Start the Web Server:
Execute the application using FastAPI from the root directory. Background tasks (like emails) are handled asynchronously by the server, eliminating the need for a separate Celery worker.

```Bash
fastapi run src\
```
Navigate to your local host (e.g., `http://localhost:8000/ui`) to access the frontend UI.

## ☁️ Deployment
Bookly is cloud-ready and can be deployed to PaaS providers like **Render**, **Heroku**, or **Railway** with minimal configuration.

1. **Provision External Services:** Ensure you have active instances of PostgreSQL and Redis running on your chosen cloud provider.

2. **Environment Variables:** Add your production database URI, Redis URI, and application secrets to your platform's environment variables settings.

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