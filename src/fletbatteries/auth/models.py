"""
Usuarios, grupos y permisos (equivalente a `django.contrib.auth` que usa djgentelella).

Las tablas llevan el prefijo `fb_` para no chocar con las de la aplicación.
"""

import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from fletbatteries.data.db import Base

fb_user_groups = Table(
    "fb_user_groups",
    Base.metadata,
    Column("user_id", ForeignKey("fb_users.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", ForeignKey("fb_groups.id", ondelete="CASCADE"), primary_key=True),
)

fb_user_permissions = Table(
    "fb_user_permissions",
    Base.metadata,
    Column("user_id", ForeignKey("fb_users.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("fb_permissions.id", ondelete="CASCADE"), primary_key=True),
)

fb_group_permissions = Table(
    "fb_group_permissions",
    Base.metadata,
    Column("group_id", ForeignKey("fb_groups.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("fb_permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(Base):
    __tablename__ = "fb_permissions"

    id = Column(Integer, primary_key=True)
    codename = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=True)

    def __str__(self):
        return self.name


class Group(Base):
    __tablename__ = "fb_groups"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), unique=True, nullable=False)
    permissions = relationship(Permission, secondary=fb_group_permissions, lazy="selectin")

    def __str__(self):
        return self.name


class User(Base):
    __tablename__ = "fb_users"

    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    first_name = Column(String(150), nullable=True)
    last_name = Column(String(150), nullable=True)
    email = Column(String(254), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    last_login = Column(DateTime, nullable=True)
    date_joined = Column(DateTime, nullable=False, default=datetime.datetime.now)

    groups = relationship(Group, secondary=fb_user_groups, lazy="selectin")
    permissions = relationship(Permission, secondary=fb_user_permissions, lazy="selectin")

    def __str__(self):
        return self.username
