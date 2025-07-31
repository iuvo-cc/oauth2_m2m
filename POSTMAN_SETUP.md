# Postman Collection for OAuth2 M2M FastAPI

This directory contains Postman collection and environment files for testing the OAuth2 Machine-to-Machine FastAPI application.

## Files

- `postman_collection.json` - Postman collection with all API endpoints
- `postman_environment.json` - Environment variables for the collection
- `POSTMAN_SETUP.md` - This setup guide

## Quick Setup

### 1. Import Files into Postman

1. Open Postman
2. Click **Import** button
3. Import both files:
   - `postman_collection.json`
   - `postman_environment.json`

### 2. Configure Environment Variables

After importing, select the "OAuth2 M2M Environment" from the environment dropdown and update the following variables:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `base_url` | Your FastAPI server URL | `http://localhost:8000` |
| `client_id` | Your OAuth2 client ID | `test_client_123` |
| `client_secret` | Your OAuth2 client secret | `secret_key_456` |

**Note**: `access_token` and `refresh_token` are automatically populated when you run the authentication requests.

### 3. Start Your FastAPI Server

Make sure your FastAPI server is running:

```bash
cd /Users/neilor/oauth2_m2m/example
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Collection Structure

The collection is organized into two main folders:

### Authentication
- **Get Access Token** - Authenticate using client credentials
- **Refresh Token** - Refresh an access token using refresh token
- **Revoke Token** - Revoke an access token

### Protected Routes
- **Protected Route - Read Scope** - Test endpoint requiring 'read' scope
- **Admin Only Route** - Test endpoint requiring admin role

## Usage Workflow

### 1. Authentication Flow

1. **Set up credentials**: Update `client_id` and `client_secret` in environment
2. **Get Access Token**: Run "Get Access Token" request
   - Uses form data with client credentials
   - Automatically saves `access_token` and `refresh_token` to environment
3. **Test Protected Routes**: Run any protected endpoint requests

### 2. Token Refresh Flow

1. **Refresh Token**: Run "Refresh Token" request when access token expires
   - Uses saved `refresh_token`
   - Updates both `access_token` and `refresh_token` in environment

### 3. Token Revocation

1. **Revoke Token**: Run "Revoke Token" request to invalidate current access token

## Request Details

### Get Access Token
- **Method**: POST
- **Endpoint**: `/token`
- **Body**: Form data with client credentials
- **Response**: Access token, refresh token, and token type

### Refresh Token
- **Method**: POST
- **Endpoint**: `/refresh`
- **Body**: JSON with refresh token
- **Response**: New access token and refresh token

### Revoke Token
- **Method**: POST
- **Endpoint**: `/revoke`
- **Body**: JSON with access token to revoke

### Protected Routes
- **Authentication**: Bearer token (automatically uses `access_token` variable)
- **Headers**: Authorization header with Bearer token

## Automated Testing

Each request includes test scripts that:

- Validate response status codes
- Check response structure
- Automatically save tokens to environment variables
- Verify expected response messages

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check if access token is valid
   - Try refreshing the token
   - Verify client credentials

2. **403 Forbidden**
   - Check if client has required scopes/roles
   - For admin routes, ensure client has admin role

3. **Connection Refused**
   - Verify FastAPI server is running
   - Check `base_url` in environment variables

### Debug Tips

- Use Postman Console (View → Show Postman Console) to see detailed request/response logs
- Check the Tests tab results for detailed test outcomes
- Verify environment variables are properly set and selected

## Environment Variables Reference

| Variable | Auto-Updated | Description |
|----------|--------------|-------------|
| `base_url` | No | Base URL of your API server |
| `client_id` | No | OAuth2 client identifier |
| `client_secret` | No | OAuth2 client secret |
| `access_token` | Yes | Current access token (auto-saved) |
| `refresh_token` | Yes | Current refresh token (auto-saved) |

## Security Notes

- Never commit files containing real client secrets
- Use Postman's secret variable type for sensitive data
- Consider using different environments for development/staging/production
- Regularly rotate client credentials in production environments
