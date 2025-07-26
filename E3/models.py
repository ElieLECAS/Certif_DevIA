from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relation avec ClientUser
    client_profile = relationship("ClientUser", back_populates="user", uselist=False)
    conversations = relationship("Conversation", back_populates="user")

class ClientUser(Base):
    __tablename__ = "client_users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    is_client_only = Column(Boolean, default=True)
    active_conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    user = relationship("User", back_populates="client_profile")
    active_conversation = relationship("Conversation", foreign_keys=[active_conversation_id])

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    status = Column(String, default="nouveau")  # nouveau, en_cours, termine
    history = Column(JSON, default=list)
    summary = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    user = relationship("User", back_populates="conversations")
    
    def add_message(self, role: str, content: str, image_path: str = None):
        """Ajouter un message à l'historique de la conversation"""
        if not self.history:
            self.history = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if image_path:
            message["image_path"] = image_path
            
        self.history.append(message)
    
    def set_status(self, new_status: str):
        """Changer le statut de la conversation"""
        self.status = new_status
        self.updated_at = datetime.utcnow() 