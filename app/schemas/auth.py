from pydantic import BaseModel, ConfigDict
from app.models.enums import UserRole

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.VIEWER

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    model_config = ConfigDict(
        from_attributes=True
    )