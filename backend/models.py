from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    stripe_customer_id = Column(String, nullable=True)
    paid = Column(Boolean, default=False)
    paid_until = Column(DateTime, nullable=True)

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    # Identification
    name = Column(String, nullable=False)

    brand = Column(String, nullable=True)
    model = Column(String, nullable=True)

    ip_address = Column(String, nullable=True)

    rtsp_url = Column(String, nullable=False)

    # Organisation
    site_name = Column(String, nullable=True)
    location = Column(String, nullable=True)

    # État
    status = Column(String, default="ACTIVE")

    description = Column(String, nullable=True)

    # Compatibilité V1
    zones_json = Column(String, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"))  # 🔥 AJOUT CRUCIAL
    
    message = Column(String)
    video_url = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
