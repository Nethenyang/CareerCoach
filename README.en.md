# Career Coach

A career coach application system built with a FastAPI backend and Vue 3 frontend, providing basic functions such as user registration and login.

## Technology Stack

### Backend
- **FastAPI** - Modern high-performance web framework
- **SQLAlchemy** - Asynchronous ORM for database operations
- **Pydantic** - Data validation and model definition
- **Passlib** - Password hashing and encryption

### Frontend
- **Vue 3** - Progressive JavaScript framework
- **Vite** - Fast build tool
- **Pinia** - State management
- **Vue Router** - Routing management

### Database
- **MySQL** - Relational database

## Project Structure

```
├── api/                    # API routing layer
│   └── auth.py            # Authentication-related endpoints
├── core/                  # Core modules
│   ├── config.py         # Configuration management
│   ├── database.py      # Database connection
│   └── security.py      # Security utilities
├── models/                # Data models
│   └── user.py          # User model
├── schemas/               # Pydantic models
│   ├── response.py     # Response models
│   └── user.py         # User request/response models
├── services/              # Business logic layer
│   └── user.py         # User service
├── middleware/           # Middleware
├── util/                 # Utility functions
├── resource/             # Resource files
│   └── init.sql        # Database initialization script
├── frontend/             # Frontend application
│   ├── src/           # Source code
│   ├── public/       # Static assets
│   └── package.json  # Frontend dependencies
├── main.py              # Application entry point
└── requirements.txt    # Backend dependencies
```

## Features

- User registration
- User login
- Secure password encryption and storage
- Asynchronous database operations
- RESTful API design

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- MySQL 8.0+

### Backend Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

2. Configure the database:

Update the database connection settings in `core/config.py`:

```python
class Settings(BaseSettings):
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = "your_password"
    DATABASE_NAME: str = "career_coach"
```

3. Initialize the database:

```bash
mysql -u root -p < resource/init.sql
```

4. Start the backend server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Install frontend dependencies:

```bash
cd frontend
npm install
```

2. Start the development server:

```bash
npm run dev
```

3. Build for production:

```bash
npm run build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST   | /api/auth/register | User registration |
| POST   | /api/auth/login | User login |

### Registration Endpoint

**Request:**

```json
{
  "username": "example",
  "password": "password123",
  "nickname": "昵称"
}
```

**Response:**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "example",
    "nickname": "昵称"
  }
}
```

### Login Endpoint

**Request:**

```json
{
  "username": "example",
  "password": "password123"
}
```

**Response:**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "example",
    "nickname": "昵称"
  }
}
```

## Development Guidelines

Refer to [RULES.md](./RULES.md) for project coding standards, including:

- File structure ordering
- Type annotation conventions
- ORM model definition rules
- Asynchronous database operation guidelines
- Naming conventions
- Commenting style

## License

MIT License