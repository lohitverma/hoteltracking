from fastapi import Request, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader, APIKey
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import secrets
import hashlib
from models import APIKeyModel, User
from database import get_db

class APIKeyService:
    def __init__(self):
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        
    def generate_api_key(self) -> str:
        """Generate a new API key"""
        return secrets.token_urlsafe(32)
        
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
        
    async def create_api_key(
        self,
        db: Session,
        user: User,
        name: str,
        expires_in_days: Optional[int] = 365,
        scopes: List[str] = None
    ) -> Dict[str, str]:
        """Create a new API key"""
        # Generate API key
        api_key = self.generate_api_key()
        hashed_key = self.hash_api_key(api_key)
        
        # Set expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
        # Create API key record
        api_key_model = APIKeyModel(
            user_id=user.id,
            name=name,
            key_hash=hashed_key,
            scopes=scopes or [],
            expires_at=expires_at
        )
        
        db.add(api_key_model)
        db.commit()
        db.refresh(api_key_model)
        
        return {
            "api_key": api_key,  # Only shown once
            "id": api_key_model.id,
            "name": name,
            "expires_at": expires_at,
            "scopes": scopes or []
        }
        
    async def validate_api_key(
        self,
        db: Session,
        api_key: str
    ) -> Optional[APIKeyModel]:
        """Validate API key and return associated model"""
        if not api_key:
            return None
            
        hashed_key = self.hash_api_key(api_key)
        api_key_model = db.query(APIKeyModel).filter(
            APIKeyModel.key_hash == hashed_key,
            APIKeyModel.is_active == True
        ).first()
        
        if not api_key_model:
            return None
            
        # Check expiration
        if api_key_model.expires_at and api_key_model.expires_at < datetime.utcnow():
            api_key_model.is_active = False
            db.commit()
            return None
            
        # Update last used
        api_key_model.last_used_at = datetime.utcnow()
        api_key_model.usage_count += 1
        db.commit()
        
        return api_key_model
        
    async def get_api_key(
        self,
        request: Request,
        db: Session = Depends(get_db)
    ) -> Optional[APIKeyModel]:
        """Get and validate API key from request"""
        api_key = await self.api_key_header(request)
        if api_key:
            api_key_model = await self.validate_api_key(db, api_key)
            if api_key_model:
                return api_key_model
        return None
        
    async def require_api_key(
        self,
        request: Request,
        db: Session = Depends(get_db),
        required_scopes: List[str] = None
    ) -> APIKeyModel:
        """Require valid API key with optional scope requirements"""
        api_key_model = await self.get_api_key(request, db)
        if not api_key_model:
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
            
        # Check scopes if required
        if required_scopes:
            if not all(scope in api_key_model.scopes for scope in required_scopes):
                raise HTTPException(
                    status_code=403,
                    detail="API key does not have required scopes",
                )
                
        return api_key_model
        
    async def list_api_keys(
        self,
        db: Session,
        user: User
    ) -> List[APIKeyModel]:
        """List all API keys for a user"""
        return db.query(APIKeyModel).filter(
            APIKeyModel.user_id == user.id,
            APIKeyModel.is_active == True
        ).all()
        
    async def revoke_api_key(
        self,
        db: Session,
        user: User,
        key_id: int
    ) -> bool:
        """Revoke an API key"""
        api_key = db.query(APIKeyModel).filter(
            APIKeyModel.id == key_id,
            APIKeyModel.user_id == user.id
        ).first()
        
        if not api_key:
            return False
            
        api_key.is_active = False
        api_key.revoked_at = datetime.utcnow()
        db.commit()
        
        return True
        
    def get_available_scopes(self) -> Dict[str, str]:
        """Get list of available API scopes"""
        return {
            "read:hotels": "Read hotel information",
            "write:hotels": "Create and update hotels",
            "read:prices": "Read price information",
            "write:alerts": "Create and manage price alerts",
            "read:alerts": "Read price alerts",
            "chat:send": "Send messages to chatbot",
            "analytics:read": "Read analytics data"
        }
