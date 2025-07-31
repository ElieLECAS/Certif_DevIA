from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

# Schémas pour l'authentification
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Schémas pour les utilisateurs
class UserBase(BaseModel):
    username: str
    email: str
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False

class User(UserBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ClientUserCreate(BaseModel):
    user_id: int
    is_client_only: bool = True

class ClientUser(BaseModel):
    id: int
    user_id: int
    is_client_only: bool
    active_conversation_id: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Schémas pour les conversations
class ConversationCreate(BaseModel):
    client_name: str
    status: str = "nouveau"

class ConversationUpdate(BaseModel):
    client_name: Optional[str] = None
    status: Optional[str] = None
    summary: Optional[str] = None

class Conversation(BaseModel):
    id: int
    client_name: str
    status: str
    history: List[Dict[str, Any]] = []
    summary: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Schémas pour les messages de chat
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    history: List[Dict[str, Any]]

class ConversationClose(BaseModel):
    conversation_id: int

class ClientNameUpdate(BaseModel):
    conversation_id: int
    client_name: str 