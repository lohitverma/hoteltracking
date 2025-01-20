from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Optional, Tuple
import httpx
import json
from datetime import datetime
import os
from models import User, OAuthAccount
from database import get_db

class OAuthService:
    def __init__(self):
        # Google OAuth settings
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
        
        # GitHub OAuth settings
        self.github_client_id = os.getenv("GITHUB_CLIENT_ID")
        self.github_client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        self.github_redirect_uri = os.getenv("GITHUB_REDIRECT_URI")
        
    async def get_google_auth_url(self) -> str:
        """Get Google OAuth authorization URL"""
        params = {
            "client_id": self.google_client_id,
            "redirect_uri": self.google_redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
        
    async def get_github_auth_url(self) -> str:
        """Get GitHub OAuth authorization URL"""
        params = {
            "client_id": self.github_client_id,
            "redirect_uri": self.github_redirect_uri,
            "scope": "read:user user:email",
            "response_type": "code"
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://github.com/login/oauth/authorize?{query_string}"
        
    async def handle_google_callback(
        self,
        code: str,
        db: Session
    ) -> Tuple[User, str, str]:
        """Handle Google OAuth callback"""
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": self.google_client_id,
            "client_secret": self.google_client_secret,
            "code": code,
            "redirect_uri": self.google_redirect_uri,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Failed to get access token from Google"
            )
            
        tokens = token_response.json()
        
        # Get user info
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        async with httpx.AsyncClient() as client:
            user_response = await client.get(user_info_url, headers=headers)
            
        if user_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Failed to get user info from Google"
            )
            
        user_info = user_response.json()
        
        # Create or update user
        return await self._handle_oauth_user(
            db,
            "google",
            user_info["id"],
            user_info["email"],
            user_info.get("name", ""),
            tokens["access_token"],
            tokens.get("refresh_token")
        )
        
    async def handle_github_callback(
        self,
        code: str,
        db: Session
    ) -> Tuple[User, str, str]:
        """Handle GitHub OAuth callback"""
        # Exchange code for access token
        token_url = "https://github.com/login/oauth/access_token"
        token_data = {
            "client_id": self.github_client_id,
            "client_secret": self.github_client_secret,
            "code": code,
            "redirect_uri": self.github_redirect_uri
        }
        headers = {"Accept": "application/json"}
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, json=token_data, headers=headers)
            
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Failed to get access token from GitHub"
            )
            
        tokens = token_response.json()
        
        # Get user info
        user_url = "https://api.github.com/user"
        headers = {
            "Authorization": f"Bearer {tokens['access_token']}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            user_response = await client.get(user_url, headers=headers)
            email_response = await client.get(f"{user_url}/emails", headers=headers)
            
        if user_response.status_code != 200 or email_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Failed to get user info from GitHub"
            )
            
        user_info = user_response.json()
        emails = email_response.json()
        
        # Get primary email
        primary_email = next(
            (email["email"] for email in emails if email["primary"]),
            emails[0]["email"] if emails else None
        )
        
        if not primary_email:
            raise HTTPException(
                status_code=400,
                detail="No email found in GitHub account"
            )
            
        # Create or update user
        return await self._handle_oauth_user(
            db,
            "github",
            str(user_info["id"]),
            primary_email,
            user_info.get("name", ""),
            tokens["access_token"],
            None  # GitHub doesn't provide refresh tokens
        )
        
    async def _handle_oauth_user(
        self,
        db: Session,
        provider: str,
        provider_user_id: str,
        email: str,
        full_name: str,
        access_token: str,
        refresh_token: Optional[str]
    ) -> Tuple[User, str, str]:
        """Handle OAuth user creation/update and return tokens"""
        # Check if OAuth account exists
        oauth_account = db.query(OAuthAccount).filter(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id
        ).first()
        
        if oauth_account:
            # Update existing account
            user = oauth_account.user
            oauth_account.access_token = access_token
            oauth_account.refresh_token = refresh_token
            oauth_account.updated_at = datetime.utcnow()
            
        else:
            # Check if user exists with email
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                # Create new user
                user = User(
                    email=email,
                    username=email.split("@")[0],
                    full_name=full_name,
                    is_active=True
                )
                db.add(user)
                db.flush()
                
            # Create OAuth account
            oauth_account = OAuthAccount(
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_user_id,
                access_token=access_token,
                refresh_token=refresh_token
            )
            db.add(oauth_account)
            
        db.commit()
        
        # Generate JWT tokens
        from services.auth_service import AuthService
        auth_service = AuthService()
        tokens = auth_service.create_tokens(user.id)
        
        return user, tokens["access_token"], tokens["refresh_token"]
        
    async def refresh_oauth_token(
        self,
        provider: str,
        refresh_token: str
    ) -> Dict[str, str]:
        """Refresh OAuth access token"""
        if provider == "google":
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to refresh Google token"
                )
                
            return response.json()
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Token refresh not supported for {provider}"
            )
