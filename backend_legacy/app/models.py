import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ── helpers ──────────────────────────────────────────────────────────────────
def _uuid():
    return str(uuid.uuid4())


# ── User ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SAEnum("customer", "admin", name="user_role"), default="customer", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # password reset
    reset_token = Column(String, nullable=True)

    orders = relationship("Order", back_populates="user")


# ── Collection ───────────────────────────────────────────────────────────────
class Collection(Base):
    __tablename__ = "collections"

    id = Column(String, primary_key=True, default=_uuid)
    handle = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    seo_title = Column(String, default="")
    seo_description = Column(Text, default="")
    path = Column(String, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent_categories = relationship("CollectionParent", back_populates="collection", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="collection")


class CollectionParent(Base):
    __tablename__ = "collection_parents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(String, ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(String, nullable=False)
    parent_name = Column(String, nullable=False)

    collection = relationship("Collection", back_populates="parent_categories")


# ── Product ──────────────────────────────────────────────────────────────────
class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=_uuid)
    handle = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    description_html = Column(Text, default="")
    category_id = Column(String, ForeignKey("collections.handle"), nullable=True)
    vendor = Column(String, default="")
    currency_code = Column(String, default="GBP")
    min_price = Column(String, default="0")
    max_price = Column(String, default="0")
    available_for_sale = Column(Boolean, default=True)
    seo_title = Column(String, default="")
    seo_description = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    collection = relationship("Collection", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.sort_order")
    options = relationship("ProductOption", back_populates="product", cascade="all, delete-orphan")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    alt_text = Column(String, default="")
    width = Column(Integer, default=1200)
    height = Column(Integer, default=1200)
    sort_order = Column(Integer, default=0)

    product = relationship("Product", back_populates="images")


class ProductOption(Base):
    __tablename__ = "product_options"

    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)

    product = relationship("Product", back_populates="options")
    values = relationship("OptionValue", back_populates="option", cascade="all, delete-orphan")


class OptionValue(Base):
    __tablename__ = "option_values"

    id = Column(String, primary_key=True, default=_uuid)
    option_id = Column(String, ForeignKey("product_options.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)

    option = relationship("ProductOption", back_populates="values")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, default="")
    available_for_sale = Column(Boolean, default=True)
    price = Column(String, default="0")
    currency_code = Column(String, default="GBP")

    product = relationship("Product", back_populates="variants")
    selected_options = relationship("VariantSelectedOption", back_populates="variant", cascade="all, delete-orphan")


class VariantSelectedOption(Base):
    __tablename__ = "variant_selected_options"

    id = Column(Integer, primary_key=True, autoincrement=True)
    variant_id = Column(String, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    value = Column(String, nullable=False)

    variant = relationship("ProductVariant", back_populates="selected_options")


# ── Cart ─────────────────────────────────────────────────────────────────────
class Cart(Base):
    __tablename__ = "carts"

    id = Column(String, primary_key=True, default=_uuid)
    checkout_url = Column(String, default="/checkout/information")
    customer_email = Column(String, nullable=True)
    shipping_first_name = Column(String, nullable=True)
    shipping_last_name = Column(String, nullable=True)
    shipping_address1 = Column(String, nullable=True)
    shipping_address2 = Column(String, nullable=True)
    shipping_city = Column(String, nullable=True)
    shipping_state = Column(String, nullable=True)
    shipping_zip = Column(String, nullable=True)
    shipping_country = Column(String, nullable=True)
    shipping_phone = Column(String, nullable=True)
    billing_first_name = Column(String, nullable=True)
    billing_last_name = Column(String, nullable=True)
    billing_address1 = Column(String, nullable=True)
    billing_address2 = Column(String, nullable=True)
    billing_city = Column(String, nullable=True)
    billing_state = Column(String, nullable=True)
    billing_zip = Column(String, nullable=True)
    billing_country = Column(String, nullable=True)
    billing_phone = Column(String, nullable=True)
    shipping_method_id = Column(String, nullable=True)
    shipping_method_name = Column(String, nullable=True)
    shipping_method_price = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(String, primary_key=True, default=_uuid)
    cart_id = Column(String, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    variant_id = Column(String, nullable=True)
    quantity = Column(Integer, default=1)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")


# ── Order ────────────────────────────────────────────────────────────────────
class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=_uuid)
    order_number = Column(String, unique=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    customer_email = Column(String, nullable=True)
    status = Column(String, default="pending")
    subtotal = Column(Float, default=0)
    tax = Column(Float, default=0)
    shipping_cost = Column(Float, default=0)
    total = Column(Float, default=0)
    currency_code = Column(String, default="GBP")
    shipping_first_name = Column(String, nullable=True)
    shipping_last_name = Column(String, nullable=True)
    shipping_address1 = Column(String, nullable=True)
    shipping_city = Column(String, nullable=True)
    shipping_state = Column(String, nullable=True)
    shipping_zip = Column(String, nullable=True)
    shipping_country = Column(String, nullable=True)
    shipping_method_name = Column(String, nullable=True)
    billing_first_name = Column(String, nullable=True)
    billing_last_name = Column(String, nullable=True)
    billing_address1 = Column(String, nullable=True)
    billing_city = Column(String, nullable=True)
    billing_state = Column(String, nullable=True)
    billing_zip = Column(String, nullable=True)
    billing_country = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    payment_card_last4 = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True, default=_uuid)
    order_id = Column(String, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String, nullable=False)
    product_title = Column(String, nullable=False)
    variant_id = Column(String, nullable=True)
    variant_title = Column(String, nullable=True)
    quantity = Column(Integer, default=1)
    price = Column(Float, default=0)
    currency_code = Column(String, default="GBP")

    order = relationship("Order", back_populates="items")


# ── Shipping Methods (static/configurable) ───────────────────────────────────
class ShippingMethod(Base):
    __tablename__ = "shipping_methods"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    price = Column(Float, default=0)
    currency_code = Column(String, default="GBP")
    is_default = Column(Boolean, default=False)
