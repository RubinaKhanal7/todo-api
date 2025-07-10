# Simple Todo API

A FastAPI-based REST API for managing todos with user authentication and PostgreSQL database integration.

## Features

- User Authentication: JWT-based authentication with secure password hashing
- Todo Management: Full CRUD operations for todos
- User Isolation: Users can only access their own todos
- PostgreSQL Integration: Robust database with SQLAlchemy ORM
- Pagination: Built-in pagination for todo lists
- Input Validation: Comprehensive validation with Pydantic
- Interactive Documentation: Auto-generated OpenAPI/Swagger docs
- Production Ready: Includes proper error handling and security measures

## Tech Stack

- FastAPI: Modern, fast web framework for building APIs
- PostgreSQL: Reliable relational database
- SQLAlchemy: Python SQL toolkit and ORM
- JWT: JSON Web Tokens for authentication
- Bcrypt: Password hashing
- Pydantic: Data validation using Python type annotations
- Uvicorn: ASGI server for running the application


### Prerequisites

- Python 3.8+
- PostgreSQL database
- pip for dependency management

### Installation

1. Clone the repository (In terminal or bash)
   git clone https://github.com/RubinaKhanal7/todo-api
   cd todo-api

2. Create virtual environment (In terminal or bash)
    python -m venv venv
    venv\Scripts\activate

3. Install dependencies (In terminal or bash)
   pip install -r requirements.txt

4. Set up environment variables
   
   Create a '.env' file in the root directory:

   SECRET_KEY=your-super-secret-jwt-key-here
   POSTGRES_USER=todo_user
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=todo
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   ACCESS_TOKEN_EXPIRE_MINUTES=30


5. Set up PostgreSQL database

   CREATE DATABASE todo;
   CREATE USER todo_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE todo TO todo_user;


6. Run the application (In terminal or bash)
   python main.py
   
   Or with uvicorn directly:
   uvicorn main:app --reload --host 127.0.0.1 --port 8000

## API Documentation

Once the server is running, you can access:

- Interactive API docs (Swagger UI http://127.0.0.1:8000/docs)
- Alternative API docs (ReDoc http://127.0.0.1:8000/redoc)
- OpenAPI JSON http://127.0.0.1:8000/openapi.json

## API Endpoints

### Authentication

POST ->  '/auth/register':  Register a new user 
POST ->  '/auth/login'    :  Login and get access token 

### Todos


GET     ->  '/todos'     : Get paginated list of todos 
POST    -> '/todos'      : Create a new todo 
GET     -> '/todos/{id}' : Get specific todo by ID 
PUT     -> '/todos/{id}' : Update todo
DELETE  -> '/todos/{id}' : Delete todo 

### Root

GET ->  '/' : API information and endpoints 

## Usage Examples

### 1. Register a new user

    "full_name": "Example",
    "email": "example@example.com",
    "password": "securepassword123"
 

### 2. Login to get access token

    "email": "example@example.com",
    "password": "securepassword123"
 

### 3. Create a todo (with authentication)

    "full_name": "Example",
    "email": "example@example.com",
    "task": "Complete the project documentation",
    "completed": false


### 4. Get all todos (with pagination)

### 5. Update a todo

    "completed": true
 
### 6. Delete a todo



## Authentication

The API uses JWT (JSON Web Tokens) for authentication. After successful login, include the token in the Authorization header:

Authorization: Bearer YOUR_ACCESS_TOKEN

**Token Expiration**: Access tokens expire after 30 minutes by default (configurable via environment variable).

## Database Schema

### Users Table
- 'id': Primary key (integer)
- 'full_name': User's full name (string)
- 'email': User's email address (string, unique)
- 'hashed_password': Bcrypt hashed password (string)
- 'created_at': Account creation timestamp
- 'updated_at': Last update timestamp

### Todos Table
- 'id': Primary key (integer)
- 'user_id': Foreign key to users table (integer)
- 'full_name': Person's full name (string)
- 'email': Person's email address (string)
- 'task': Todo task description (string)
- 'completed': Completion status (boolean)
- 'created_at': Creation timestamp
- 'updated_at': Last update timestamp

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- **200**: Success
- **201**: Created
- **204**: No Content (successful deletion)
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (authentication required)
- **404**: Not Found
- **422**: Unprocessable Entity (validation errors)

Example error response:
json:

{
  "detail": "Todo not found"
}


## Security Features

- Password Hashing : Uses bcrypt for secure password storage
- JWT Tokens : Stateless authentication with configurable expiration
- Input Validation : Comprehensive validation using Pydantic
- User Isolation : Users can only access their own todos
- SQL Injection Protection : SQLAlchemy ORM prevents SQL injection

## Development

### Running in Development Mode

uvicorn main:app --reload --host 127.0.0.1 --port 8000

## License

This project is a demonstration of RESTful API best practices and an example of JWT authentication implementation

## Support

For issues and questions, please open an issue in the repository or contact the development team.