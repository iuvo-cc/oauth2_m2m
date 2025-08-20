# OAuth2 Machine-to-Machine Authentication Service

A FastAPI-based OAuth2 Machine-to-Machine (M2M) authentication server with JWT tokens, refresh token rotation, rate limiting, and comprehensive audit logging.

## Features

- **JWT-based Authentication**: Secure token generation and validation
- **Refresh Token Rotation**: Automatic refresh token rotation for enhanced security
- **Rate Limiting**: Per-client IP-based rate limiting
- **Audit Logging**: Comprehensive event logging for security monitoring
- **Token Revocation**: Manual token revocation with blacklist tracking
- **Scope-based Authorization**: Fine-grained access control with scopes
- **Role-based Access Control**: Support for different user roles (user, admin)
- **MongoDB Integration**: Persistent storage for tokens, clients, and audit logs

## Architecture

The system consists of two main components:

1. **`oauth2_m2m.py`**: Core OAuth2 M2M authentication class
2. **`example/main.py`**: FastAPI application demonstrating OAuth2 endpoints usage

## API Endpoints

### Authentication Endpoints

#### `POST /token`
Authenticate a client and receive access and refresh tokens.

**Request Body** (form-data):
```
username: client_id
password: client_secret
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "abc123...",
  "token_type": "bearer"
}
```

#### `POST /refresh`
Refresh an access token using a refresh token.

**Request Body**:
```json
{
  "refresh_token": "abc123..."
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "def456...",
  "token_type": "bearer"
}
```

#### `POST /revoke`
Manually revoke an access token.

**Request Body**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Protected Endpoints

#### `GET /protected`
A protected route requiring "read" scope.

**Headers**:
```
Authorization: Bearer <access_token>
```

#### `GET /admin-only`
An admin-only route requiring "admin" scope and admin role.

**Headers**:
```
Authorization: Bearer <access_token>
```

## Database Schema

The system uses MongoDB with the following collections:

### `config`
Stores JWT configuration:
```json
{
  "_id": "jwt_config",
  "SECRET_KEY": "your-secret-key",
  "ALGORITHM": "HS256",
  "ACCESS_TOKEN_EXPIRE_MINUTES": 15,
  "MAX_REQUESTS_PER_MINUTE": 60
}
```

### `clients`
Stores client credentials and metadata:
```json
{
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "scopes": ["read", "write"],
  "role": "user"
}
```

### `tokens`
Stores active refresh tokens:
```json
{
  "client_id": "your-client-id",
  "refresh_token": "abc123...",
  "created_at": "2025-07-27T10:00:00Z"
}
```

### `revoked_tokens`
Stores revoked access tokens:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "revoked_at": "2025-07-27T10:00:00Z"
}
```

### `used_refresh_tokens`
Tracks used refresh tokens to prevent reuse:
```json
{
  "refresh_token": "abc123...",
  "used_at": "2025-07-27T10:00:00Z"
}
```

### `rate_limits`
Tracks rate limiting per client/IP:
```json
{
  "_id": "client_id:ip:timestamp",
  "count": 5,
  "timestamp": "2025-07-27T10:00:00Z"
}
```

### `audit_logs`
Comprehensive audit logging:
```json
{
  "event_type": "login_success",
  "client_id": "your-client-id",
  "ip": "192.168.1.1",
  "reason": "Valid credentials",
  "timestamp": "2025-07-27T10:00:00Z"
}
```

## Security Features

### Refresh Token Rotation
- Each refresh operation generates a new refresh token
- Old refresh tokens are immediately revoked
- Prevents token reuse attacks

### Rate Limiting
- Configurable requests per minute per client/IP combination
- Automatic blocking when limits are exceeded
- Audit logging of rate limit violations

### Token Revocation
- Manual token revocation support
- Revoked tokens are stored in a blacklist
- All token validations check the revocation list

### Audit Logging
Event types logged:
- `login_success` / `login_failure`
- `token_revoked`
- `refresh_token_reuse`
- `refresh_token_invalid`
- `rate_limit_exceeded`
- `token_invalid`

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd auth
```

2. Install dependencies:
```bash
pip install fastapi uvicorn pymongo python-jose[cryptography] python-multipart
```

3. Set up MongoDB:
```bash
# Start MongoDB locally
mongod --dbpath /path/to/your/db
```

3. Initialize the database with configuration:
```javascript
// In MongoDB shell
use oauth2_m2m
db.config.insertOne({
  "_id": "jwt_config",
  "SECRET_KEY": "your-super-secret-key-here",
  "ALGORITHM": "HS256",
  "ACCESS_TOKEN_EXPIRE_MINUTES": 15,
  "MAX_REQUESTS_PER_MINUTE": 60
})
```

4. Create a test client:
```javascript
db.clients.insertOne({
  "client_id": "test_client",
  "client_secret": "test_secret",
  "scopes": ["read", "write"],
  "role": "user"
})
```

## Usage

1. Start the server from the project root:
```bash
uvicorn example.main:app --reload
```

Or alternatively, from the example directory:
```bash
cd example
python -c "import sys; sys.path.append('..'); import main; import uvicorn; uvicorn.run(main.app, host='0.0.0.0', port=8000, reload=True)"
```

2. Authenticate and get tokens:
```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test_client&password=test_secret"
```

3. Use the access token to access protected endpoints:
```bash
curl -X GET "http://localhost:8000/protected" \
  -H "Authorization: Bearer <your_access_token>"
```

4. Refresh tokens when they expire:
```bash
curl -X POST "http://localhost:8000/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<your_refresh_token>"}'
```

## Development

### Project Structure
```
auth/
├── oauth2_m2m.py           # Core OAuth2 M2M authentication class
├── example/
│   └── main.py             # FastAPI application example
├── Pipfile                 # Dependencies
├── Pipfile.lock            # Locked dependencies
├── .gitignore              # Git ignore file
├── .pre-commit-config.yaml # Pre-commit hooks configuration
└── README.md               # This file
```

### Environment Variables
You can override MongoDB connection:
```bash
export MONGODB_URL="mongodb://localhost:27017"
export MONGODB_DB="oauth2_m2m"
```

### Testing
Test the endpoints using the FastAPI automatic documentation:
```
http://localhost:8000/docs
```

## Security Considerations

1. **Secret Key**: Use a strong, randomly generated secret key in production
2. **HTTPS**: Always use HTTPS in production environments
3. **Token Expiration**: Keep access token expiration short (15 minutes recommended)
4. **Rate Limiting**: Adjust rate limits based on your application needs
5. **Audit Logs**: Regularly monitor audit logs for suspicious activity
6. **Database Security**: Secure your MongoDB instance with authentication and authorization

## License

This project is licensed under the MIT License.
