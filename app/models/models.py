from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import BigInteger, Text, ForeignKey, Integer, String, Boolean, text, func
from  app.dao.database import Base
from sqlalchemy import DateTime
from datetime import datetime

class User(Base):
    __tablename__ = 'users'

    # id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str|None] = mapped_column(String(64), nullable=True) 
    first_name: Mapped[str|None] = mapped_column(String(64), nullable=True)
    last_name:Mapped[str|None] = mapped_column(String(64), nullable=True)

    trial_until:Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_trial_used: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    #Отношения к VPN подключениям
    vpns: Mapped[list['UserVPN']] = relationship(back_populates='user')

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"

class VPNCategory(Base):
    __tablename__ = 'vpn_categories'
    # id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(25), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    #Отношение к VPN-серверам
    vpns: Mapped[list['VPN']] = relationship(back_populates='category', lazy="selectin")

    #VPN сервер
class VPN(Base):
    __tablename__ = 'vpns'

    # id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # --- данные клиента из 3x-ui ---
    client_uuid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)   # id из API (UUID клиента)
    email: Mapped[str] = mapped_column(String(125), unique=True, nullable=False)        # email = tg_id или alias
    enable: Mapped[bool] = mapped_column(default=True, nullable=False)
    inbound_id: Mapped[int] = mapped_column(Integer, nullable=True)                     # inboundId
    flow: Mapped[str | None] = mapped_column(String(64), nullable=True)                 # flow
    expiry_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # срок действия

    # --- для магазина ---
    access_url: Mapped[str] = mapped_column(String(256), nullable=False)                # готовая ссылка vless://...
    
    
    # --- связи ---
    category_id: Mapped[int] = mapped_column(ForeignKey('vpn_categories.id'))
    category: Mapped['VPNCategory'] = relationship(back_populates='vpns', lazy="selectin")
    users: Mapped[list['UserVPN']] = relationship(back_populates='vpn', lazy="selectin")

    @hybrid_property
    def price(self) -> int:
        return self.category.price
    @price.expression
    def price(cls):
        return VPNCategory.price


class UserVPN(Base):
    __tablename__ = 'user_vpn'

    user_id:Mapped[int] = mapped_column(Integer, ForeignKey('users.id')) 
    vpn_id:Mapped[int] = mapped_column(Integer, ForeignKey('vpns.id'))
    until:Mapped[datetime] = mapped_column(DateTime)
    status:Mapped[bool] = mapped_column(Boolean, default=True)

    #Отношения
    user: Mapped['User'] = relationship(back_populates='vpns')
    vpn: Mapped['VPN'] = relationship(back_populates='users')

