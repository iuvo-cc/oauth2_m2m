from fastapi import HTTPException, Request, Security, Depends
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta
from functools import wraps

class OAuth2M2M:
    def __init__(self, db):
        self.db = db
        self.config = self._load_config()
        self.tokens = db.tokens
        self.clients = db.clients
        self.revoked = db.revoked_tokens
        self.used_refresh = db.used_refresh_tokens
        self.rate_limits = db.rate_limits
        self.audit = db.audit_logs
        self.security = HTTPBearer()

    def _load_config(self):
        config = self.db.config.find_one({"_id": "jwt_config"})
        if not config:
            raise RuntimeError("JWT configuration not found in the database.")
        return config

    def create_access_token(self, data: dict, expires_delta: timedelta):
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.config["SECRET_KEY"], algorithm=self.config["ALGORITHM"])

    def save_refresh_token(self, client_id: str, token: str):
        self.tokens.insert_one({
            "client_id": client_id,
            "refresh_token": token,
            "created_at": datetime.utcnow()
        })

    def revoke_refresh_token(self, token: str):
        self.tokens.delete_one({"refresh_token": token})
        self.used_refresh.insert_one({"refresh_token": token, "used_at": datetime.utcnow()})

    def is_refresh_token_reused(self, token: str):
        return self.used_refresh.find_one({"refresh_token": token}) is not None

    def log_event(self, event_type, client_id=None, ip=None, reason=None):
        self.audit.insert_one({
            "event_type": event_type,
            "client_id": client_id,
            "ip": ip,
            "reason": reason,
            "timestamp": datetime.utcnow()
        })

    def get_ip(self, request: Request):
        return request.client.host

    def rate_limit(self, client_id, ip):
        now = datetime.utcnow().replace(second=0, microsecond=0)
        key = f"{client_id}:{ip}:{now.isoformat()}"
        entry = self.rate_limits.find_one({"_id": key})
        if entry and entry["count"] >= self.config["MAX_REQUESTS_PER_MINUTE"]:
            self.log_event("rate_limit_exceeded", client_id, ip)
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        elif entry:
            self.rate_limits.update_one({"_id": key}, {"$inc": {"count": 1}})
        else:
            self.rate_limits.insert_one({"_id": key, "count": 1, "timestamp": now})

    def authenticate(self, form_data: OAuth2PasswordRequestForm, request: Request):
        client = self.clients.find_one({"client_id": form_data.username})
        ip = self.get_ip(request)
        if not client or client["client_secret"] != form_data.password:
            self.log_event("login_failure", form_data.username, ip, "Invalid credentials")
            raise HTTPException(status_code=401, detail="Invalid client credentials")
        self.log_event("login_success", form_data.username, ip)
        return client

    def get_current_client(self, credentials):
        token = credentials.credentials
        try:
            if self.revoked.find_one({"token": token}):
                self.log_event("token_revoked", reason="Token found in revocation list")
                raise HTTPException(status_code=401, detail="Token has been revoked")
            payload = jwt.decode(token, self.config["SECRET_KEY"], algorithms=[self.config["ALGORITHM"]])
            client_id = payload.get("sub")
            scopes = payload.get("scopes", [])
            role = payload.get("role", "")
        except JWTError:
            self.log_event("token_invalid", reason="JWT decoding error")
            raise HTTPException(status_code=401, detail="Could not validate token")
        return {"client_id": client_id, "scopes": scopes, "role": role}

    def protected(self, required_scope=None):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Get credentials from the first argument if it's HTTPAuthorizationCredentials
                # or from dependency injection
                credentials = None
                for arg in args:
                    if hasattr(arg, 'credentials'):
                        credentials = arg
                        break
                
                if not credentials:
                    raise HTTPException(status_code=401, detail="No authorization credentials provided")
                
                client = self.get_current_client(credentials)
                if required_scope and required_scope not in client["scopes"]:
                    raise HTTPException(status_code=403, detail=f"Missing required scope: {required_scope}")
                return await func(client=client, *args, **kwargs)
            return wrapper
        return decorator