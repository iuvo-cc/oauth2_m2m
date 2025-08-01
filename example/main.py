from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from pymongo import MongoClient
import dynaconf
import secrets
import sys
import os

from src.oauth2_m2m.oauth2_m2m import OAuth2M2M

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RevokeTokenRequest(BaseModel):
    access_token: str

# Instância global do app e da classe
config = dynaconf.LazySettings(merge_enabled=True, settings_files=["conf/config.toml"] )
app = FastAPI()
client = MongoClient(os.getenv("MONGO_URL"))
m2m = OAuth2M2M(MongoClient(os.getenv("MONGO_URL")).oauth2_m2m)

@app.post("/token", response_model=TokenResponse)
def get_token(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    client = m2m.authenticate(form_data, request)
    access_token = m2m.create_access_token(
        {"sub": client["client_id"], "scopes": client.get("scopes", []), "role": client.get("role", "user")},
        timedelta(minutes=m2m.config["ACCESS_TOKEN_EXPIRE_MINUTES"])
    )
    refresh_token = secrets.token_urlsafe(32)
    m2m.save_refresh_token(client["client_id"], refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@app.post("/refresh", response_model=TokenResponse)
def refresh_token(request_data: RefreshTokenRequest):
    if m2m.is_refresh_token_reused(request_data.refresh_token):
        m2m.log_event("refresh_token_reuse", reason="Detected reuse of refresh token")
        raise HTTPException(status_code=401, detail="Refresh token reuse detected")
    token_doc = m2m.tokens.find_one({"refresh_token": request_data.refresh_token})
    if not token_doc:
        m2m.log_event("refresh_token_invalid", reason="Refresh token not found")
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    client = m2m.clients.find_one({"client_id": token_doc["client_id"]})
    access_token = m2m.create_access_token(
        {"sub": client["client_id"], "scopes": client.get("scopes", []), "role": client.get("role", "user")},
        timedelta(minutes=m2m.config["ACCESS_TOKEN_EXPIRE_MINUTES"])
    )
    new_refresh = secrets.token_urlsafe(32)
    m2m.revoke_refresh_token(request_data.refresh_token)
    m2m.save_refresh_token(client["client_id"], new_refresh)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh)

@app.post("/revoke")
def revoke_token(request_data: RevokeTokenRequest):
    m2m.revoked.insert_one({"token": request_data.access_token, "revoked_at": datetime.utcnow()})
    m2m.log_event("token_revoked", reason="Token manually revoked")
    return {"message": "Token revoked successfully"}

@app.get("/protected")
async def protected_route(current_client: dict = Depends(m2m.get_current_client_dep)):
    if "read" not in current_client["scopes"]:
        raise HTTPException(status_code=403, detail="Missing required scope: read")
    return {"message": f"Hello {current_client['client_id']}, you have accessed a protected route!"}

@app.get("/admin-only")
async def admin_route(current_client: dict = Depends(m2m.get_current_client_dep)):
    if "admin" not in current_client["scopes"]:
        raise HTTPException(status_code=403, detail="Missing required scope: admin")
    if current_client["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return {"message": f"Welcome Admin {current_client['client_id']}!"}
