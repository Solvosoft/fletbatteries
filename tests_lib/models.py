"""Modelos de prueba de la librería (con su propia Base: no se mezclan con los de la demo)."""

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, relationship

from fletbatteries.contrib.history import HistoryMixin
from fletbatteries.contrib.trash import SoftDeleteMixin, TrashMixin
from fletbatteries.data import BaseManager

LibBase = declarative_base()

item_tags = sa.Table(
    "lib_item_tags",
    LibBase.metadata,
    sa.Column("item_id", sa.ForeignKey("lib_items.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("tag_id", sa.ForeignKey("lib_tags.id", ondelete="CASCADE"), primary_key=True),
)


class Category(LibBase):
    __tablename__ = "lib_categories"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False, unique=True)


class Tag(LibBase):
    __tablename__ = "lib_tags"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(30), nullable=False)


class Item(LibBase):
    __tablename__ = "lib_items"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False)
    code = sa.Column(sa.String(20), nullable=True)
    price = sa.Column(sa.Numeric(10, 2), nullable=True)
    active = sa.Column(sa.Boolean, nullable=False, default=True)
    kind = sa.Column(sa.String(10), nullable=True)
    category_id = sa.Column(sa.Integer, sa.ForeignKey("lib_categories.id"), nullable=True)
    category = relationship(Category, lazy="selectin")
    tags = relationship(Tag, secondary=item_tags, lazy="selectin")


class Doc(SoftDeleteMixin, LibBase):
    __tablename__ = "lib_docs"
    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.String(60), nullable=False)


class CategoryManager(BaseManager):
    model = Category
    unique_fields = ("name",)
    default_order = "name"


class ItemManager(BaseManager):
    model = Item
    unique_fields = ("code",)
    default_order = "id"


class DocManager(HistoryMixin, TrashMixin, BaseManager):
    model = Doc
    default_order = "id"
