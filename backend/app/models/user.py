from sqlalchemy import (
    UniqueConstraint, Column, Integer, Enum as SAEnum,
    String, Date, Boolean, DateTime, func
)
from sqlalchemy.orm import relationship

from core.database import Base
from .enums import AuthProvider

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),
    )

    user_id = Column(Integer, primary_key=True, index=True)

    name = Column(String(50), nullable=True)
    nickname = Column(String(50), nullable=True)

    email = Column(String(255), nullable=True)
    phone_number = Column(String(20), index=True, nullable=True)
    birth_date = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)

    provider = Column(
        SAEnum(AuthProvider, name="auth_provider_enum", native_enum=False),
        nullable=False,
    )
    provider_user_id = Column(String(255), nullable=False, index=True)

    refresh_token_hash = Column(String(512), nullable=True)
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    refresh_token_revoked = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    created_rooms = relationship("DebateRoom", back_populates="creator")