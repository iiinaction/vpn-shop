from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime, timezone
from typing import Optional

class TelegramIDModel(BaseModel):
    telegram_id: int
    model_config = ConfigDict(from_attributes=True)

class VPNEmailFilter(BaseModel):
    email: str
    
class UserModel(TelegramIDModel):
    username: Optional[str] = None
    first_name: str|None
    last_name: str|None
    trial_until: datetime|None
    is_trial_used: bool = False

    model_config = ConfigDict(from_attributes=True)

class UserRead(UserModel):
    id: int  # primary key из БД

class VPNCreate(BaseModel):
    client_uuid: str = Field(alias="id")
    email: str
    inbound_id: int = Field(alias="inboundId")
    enable: bool
    expiry_time: datetime = Field(alias="expiryTime")
    flow: str
    access_url: str
    model_config = ConfigDict(extra='ignore', 
                              populate_by_name=True,
                              from_attributes=True
    )
    @model_validator(mode='before')
    def convert_to_timestamp(cls, values):
        ts = values.get("expiryTime")
        if isinstance(ts, int):
            values["expiryTime"] = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        return values



class VPNRead(VPNCreate):
    id: int  # id в нашей БД (не путать с key_id из XUI)