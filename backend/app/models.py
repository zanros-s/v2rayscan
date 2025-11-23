from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    raw_link = Column(Text, nullable=False)

    type = Column(String(50), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)

    uuid = Column(String(64), nullable=True)
    security = Column(String(50), nullable=True)
    sni = Column(String(255), nullable=True)
    network = Column(String(50), nullable=True)

    params_json = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    group_id = Column(Integer, ForeignKey("server_groups.id"), nullable=True)

    group = relationship("ServerGroup", back_populates="servers")

    checks = relationship(
        "Check",
        back_populates="server",
        cascade="all, delete-orphan",
        order_by="Check.checked_at.desc()",
    )


class Check(Base):
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)
    status = Column(String(10), nullable=False)  # "UP" or "DOWN"
    latency_ms = Column(Float, nullable=True)
    error = Column(Text, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow, index=True)

    server = relationship("Server", back_populates="checks")


class SettingsModel(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, default=1)
    check_interval_seconds = Column(Integer, default=30)

    telegram_bot_token = Column(String(255), nullable=True)
    telegram_chat_id = Column(String(255), nullable=True)
    notify_on_recover = Column(Boolean, default=True)


    telegram_use_proxy = Column(Boolean, default=False)
    # none | socks | server
    telegram_proxy_mode = Column(String(20), default="none")


    telegram_socks_host = Column(String(255), nullable=True)
    telegram_socks_port = Column(Integer, nullable=True)
    telegram_socks_username = Column(String(255), nullable=True)
    telegram_socks_password = Column(String(255), nullable=True)

 
    telegram_server_id = Column(Integer, nullable=True)
    down_fail_threshold = Column(Integer, default=3)


class ServerGroup(Base):
    __tablename__ = "server_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(20), nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    servers = relationship("Server", back_populates="group")
