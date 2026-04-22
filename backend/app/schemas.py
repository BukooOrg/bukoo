from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# ── Auth ─────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "customer"


class UserLogin(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    id: str
    fullName: str
    role: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    token: str
    user: UserResponse


# ── SEO ──────────────────────────────────────────────────────────────────────
class SEOSchema(BaseModel):
    title: str = ""
    description: str = ""


# ── Image ────────────────────────────────────────────────────────────────────
class ImageSchema(BaseModel):
    url: str
    altText: str = ""
    width: int = 1200
    height: int = 1200

    class Config:
        from_attributes = True


# ── Money ────────────────────────────────────────────────────────────────────
class MoneySchema(BaseModel):
    amount: str
    currencyCode: str


# ── Product Option ───────────────────────────────────────────────────────────
class OptionValueSchema(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class ProductOptionSchema(BaseModel):
    id: str
    name: str
    values: list[OptionValueSchema] = []

    class Config:
        from_attributes = True


# ── Variant ──────────────────────────────────────────────────────────────────
class SelectedOptionSchema(BaseModel):
    name: str
    value: str

    class Config:
        from_attributes = True


class ProductVariantSchema(BaseModel):
    id: str
    title: str
    availableForSale: bool
    selectedOptions: list[SelectedOptionSchema] = []
    price: MoneySchema

    class Config:
        from_attributes = True


# ── Product ──────────────────────────────────────────────────────────────────
class ProductResponse(BaseModel):
    id: str
    handle: str
    title: str
    vendor: str
    description: str
    descriptionHtml: str
    categoryId: Optional[str] = None
    tags: list[str] = []
    featuredImage: ImageSchema
    availableForSale: bool
    currencyCode: str
    priceRange: dict
    images: list[ImageSchema] = []
    options: list[ProductOptionSchema] = []
    seo: SEOSchema
    variants: list[ProductVariantSchema] = []


# ── Collection ───────────────────────────────────────────────────────────────
class ParentCategorySchema(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class CollectionResponse(BaseModel):
    handle: str
    title: str
    description: str
    seo: SEOSchema
    parentCategoryTree: list[ParentCategorySchema] = []
    updatedAt: str = ""
    path: str = ""


# ── Cart ─────────────────────────────────────────────────────────────────────
class AddToCartRequest(BaseModel):
    merchandiseId: str
    quantity: int = 1


class UpdateCartItemRequest(BaseModel):
    quantity: int


class CartProductSchema(BaseModel):
    id: str
    handle: str
    title: str
    images: list[ImageSchema] = []
    featuredImage: ImageSchema


class CartMerchandiseSchema(BaseModel):
    id: str
    title: str
    selectedOptions: list[SelectedOptionSchema] = []
    product: CartProductSchema


class CartCostItemSchema(BaseModel):
    totalAmount: MoneySchema


class CartItemResponse(BaseModel):
    id: str
    quantity: int
    cost: CartCostItemSchema
    merchandise: CartMerchandiseSchema


class AddressSchema(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None


class ShippingMethodSchema(BaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[MoneySchema] = None
    isDefault: bool = False

    class Config:
        from_attributes = True


class CartCostSchema(BaseModel):
    subtotalAmount: MoneySchema
    totalAmount: MoneySchema
    totalTaxAmount: MoneySchema
    shippingAmount: Optional[MoneySchema] = None


class CartResponse(BaseModel):
    id: str
    checkoutUrl: str
    customerEmail: Optional[str] = None
    cost: CartCostSchema
    lines: list[CartItemResponse] = []
    totalQuantity: int = 0
    shippingAddress: Optional[AddressSchema] = None
    billingAddress: Optional[AddressSchema] = None
    shippingMethod: Optional[ShippingMethodSchema] = None


# ── Checkout ─────────────────────────────────────────────────────────────────
class CustomerInfoRequest(BaseModel):
    email: str


class ShippingMethodSelectRequest(BaseModel):
    shippingMethodId: str


class PaymentRequest(BaseModel):
    cardNumber: str
    cardholderName: str
    expirationMonth: int
    expirationYear: int
    securityCode: str
    billingSameAsShipping: Optional[bool] = True


# ── Order ────────────────────────────────────────────────────────────────────
class OrderItemSchema(BaseModel):
    id: str
    product_title: str
    variant_title: Optional[str]
    quantity: int
    price: float
    currency_code: str

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: str
    orderNumber: str
    status: str
    customerEmail: Optional[str]
    subtotal: float
    tax: float
    shippingCost: float
    total: float
    currencyCode: str
    items: list[OrderItemSchema] = []
    createdAt: datetime

    class Config:
        from_attributes = True
