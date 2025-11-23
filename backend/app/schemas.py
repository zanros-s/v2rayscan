from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ---------- Servers ----------

class ServerCreate(BaseModel):
    name: Optional[str] = Field(None, description="Optional display name")
    link: str = Field(..., description="Full config link (vless://, vmess://, ...)")


class ServerUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Optional display name")
    link: Optional[str] = Field(
        None,
        description="Full config link (vless://, vmess://, ...)",
    )
    enabled: Optional[bool] = None
    group_id: Optional[int] = None



class ServerGroupBase(BaseModel):
    name: str
    color: Optional[str] = None
    sort_order: int = 0


class ServerGroupCreate(ServerGroupBase):
    pass


class ServerGroupUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None


class ServerGroupOut(ServerGroupBase):
    id: int

    class Config:
        from_attributes = True  

class ServerListItem(BaseModel):
    id: int
    name: str
    type: str
    host: str
    port: int
    enabled: bool


    group_id: Optional[int] = None
    group: Optional[ServerGroupOut] = None
    raw_link: str

    last_status: Optional[str] = None
    last_latency_ms: Optional[float] = None
    last_checked_at: Optional[datetime] = None

    class Config:
        orm_mode = True



class ServerDetail(BaseModel):
    id: int
    name: str
    raw_link: str
    type: str
    host: str
    port: int
    uuid: Optional[str]
    security: Optional[str]
    sni: Optional[str]
    network: Optional[str]
    params_json: Optional[str]
    enabled: bool

    group_id: Optional[int] = None
    group: Optional[ServerGroupOut] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True



# ---------- Checks ----------

class CheckRead(BaseModel):
    id: int
    server_id: int
    status: str
    latency_ms: Optional[float]
    error: Optional[str]
    checked_at: datetime

    class Config:
        orm_mode = True


# ---------- Settings ----------

class SettingsRead(BaseModel):
    check_interval_seconds: int
    telegram_bot_token: Optional[str]
    telegram_chat_id: Optional[str]
    notify_on_recover: bool

    telegram_use_proxy: bool
    telegram_proxy_mode: str
    telegram_socks_host: Optional[str]
    telegram_socks_port: Optional[int]
    telegram_socks_username: Optional[str]
    telegram_socks_password: Optional[str]
    telegram_server_id: Optional[int]
    down_fail_threshold: int = 3

    class Config:
        orm_mode = True


class SettingsUpdate(BaseModel):
    check_interval_seconds: Optional[int] = Field(None, ge=5)
    telegram_bot_token: Optional[str]
    telegram_chat_id: Optional[str]
    notify_on_recover: Optional[bool]

    telegram_use_proxy: Optional[bool]
    telegram_proxy_mode: Optional[str]
    telegram_socks_host: Optional[str]
    telegram_socks_port: Optional[int]
    telegram_socks_username: Optional[str]
    telegram_socks_password: Optional[str]
    telegram_server_id: Optional[int]
    down_fail_threshold: Optional[int] = Field(None, ge=1, le=20)
