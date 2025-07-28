# OAuth2 M2M FastAPI Example

This directory contains a complete FastAPI application example that demonstrates how to use the OAuth2 M2M authentication system.

## Overview

This example shows a production-ready implementation of an OAuth2 Machine-to-Machine authentication server with the following features:

- **Token Generation**: OAuth2 compatible token endpoint
- **Token Refresh**: Secure refresh token rotation
- **Token Revocation**: Manual token revocation
- **Protected Routes**: Scope and role-based route protection
- **Audit Logging**: Comprehensive security event logging
- **Rate Limiting**: Built-in protection against abuse

## API Endpoints

### Authentication Endpoints

#### `POST /token`
Generate access and refresh tokens using client credentials.

**Request** (form-data):
```
username: your_client_id
password: your_client_secret
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
Refresh an expired access token using a valid refresh token.

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

**Security Features**:
- Automatic refresh token rotation
- Detection and prevention of refresh token reuse
- Comprehensive audit logging

#### `POST /revoke`
Manually revoke an access token.

**Request Body**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response**:
```json
{
  "message": "Token revoked successfully"
}
```

### Protected Endpoints

#### `GET /protected`
A protected route that requires a valid access token with "read" scope.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "message": "Hello client_id, you have accessed a protected route!"
}
```

#### `GET /admin-only`
An admin-only route that requires both "admin" scope and "admin" role.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "message": "Welcome Admin client_id!"
}
```

## Running the Example

### Prerequisites

1. **MongoDB**: Make sure MongoDB is running on `mongodb://localhost:27017`
2. **Dependencies**: Install required Python packages
3. **Database Setup**: Configure JWT settings and create test clients

### Quick Start

1. **From the project root directory**:
```bash
uvicorn example.main:app --reload
```

2. **Or from the example directory**:
```bash
cd example
python -m uvicorn main:app --reload
```

The server will start on `http://localhost:8000`

### Database Configuration

Before running the example, ensure your MongoDB database is properly configured:

```javascript
// Connect to MongoDB shell
use oauth2_m2m

// Create JWT configuration
db.config.insertOne({
  "_id": "jwt_config",
  "SECRET_KEY": "your-super-secret-key-here",
  "ALGORITHM": "HS256",
  "ACCESS_TOKEN_EXPIRE_MINUTES": 15,
  "MAX_REQUESTS_PER_MINUTE": 60
})

// Create a test client
db.clients.insertOne({
  "client_id": "test_client",
  "client_secret": "test_secret",
  "scopes": ["read", "write", "admin"],
  "role": "admin"
})

// Create a regular user client
db.clients.insertOne({
  "client_id": "user_client",
  "client_secret": "user_secret",
  "scopes": ["read"],
  "role": "user"
})
```

## Testing the API

### 1. Get Access Token

```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test_client&password=test_secret"
```

### 2. Access Protected Route

```bash
curl -X GET "http://localhost:8000/protected" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Access Admin Route

```bash
curl -X GET "http://localhost:8000/admin-only" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Refresh Token

```bash
curl -X POST "http://localhost:8000/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

### 5. Revoke Token

```bash
curl -X POST "http://localhost:8000/revoke" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "YOUR_ACCESS_TOKEN"}'
```

## Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Use these interfaces to explore and test the API endpoints interactively.

## Code Structure

```python
# Pydantic models for request/response validation
class TokenResponse(BaseModel)       # Token endpoint response
class RefreshTokenRequest(BaseModel) # Refresh endpoint request
class RevokeTokenRequest(BaseModel)  # Revoke endpoint request

# FastAPI application instance
app = FastAPI()

# OAuth2 M2M authentication instance
m2m = OAuth2M2M(MongoClient("mongodb://localhost:27017").oauth2_m2m)

# Endpoint definitions with proper security decorators
@app.post("/token")           # Token generation
@app.post("/refresh")         # Token refresh
@app.post("/revoke")          # Token revocation
@app.get("/protected")        # Protected route
@app.get("/admin-only")       # Admin-only route
```

## Security Features Demonstrated

### 1. **Refresh Token Rotation**
- Each refresh operation generates a new refresh token
- Old refresh tokens are immediately invalidated
- Prevents token replay attacks

### 2. **Token Reuse Detection**
- Tracks used refresh tokens
- Raises security alerts on reuse attempts
- Logs all security events for monitoring

### 3. **Scope-based Access Control**
- Routes can require specific scopes
- Fine-grained permission management
- Automatic scope validation

### 4. **Role-based Access Control**
- Additional role checking for sensitive routes
- Hierarchical access control
- Admin vs. user role differentiation

### 5. **Comprehensive Audit Logging**
- All authentication events logged
- Security incidents tracked
- IP address and timestamp recording

## Environment Configuration

### Development
```bash
export MONGODB_URL="mongodb://localhost:27017"
export MONGODB_DB="oauth2_m2m"
export ENVIRONMENT="development"
```

### Production
```bash
export MONGODB_URL="mongodb://your-production-mongo:27017"
export MONGODB_DB="oauth2_m2m_prod"
export ENVIRONMENT="production"
```

## Error Handling

The example demonstrates proper error handling for:

- **401 Unauthorized**: Invalid credentials, expired tokens, revoked tokens
- **403 Forbidden**: Missing required scopes or roles
- **429 Too Many Requests**: Rate limiting exceeded
- **422 Unprocessable Entity**: Invalid request data

## Next Steps

1. **Customize Scopes**: Modify the client scopes based on your application needs
2. **Add More Routes**: Create additional protected endpoints
3. **Implement Middleware**: Add custom middleware for logging or monitoring
4. **Configure CORS**: Add CORS middleware for web applications
5. **Add Health Checks**: Implement health check endpoints
6. **Setup Monitoring**: Integrate with monitoring solutions

## Related Files

- **`../oauth2_m2m.py`**: Core authentication class
- **`../README.md`**: Main project documentation
- **`../Pipfile`**: Project dependencies

This example provides a solid foundation for building OAuth2 M2M authentication into your FastAPI applications.
