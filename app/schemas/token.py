from pydantic import BaseModel

class AccessTokenResponse(BaseModel):
    """Schema for access token"""
    access_token: str
    token_type: str