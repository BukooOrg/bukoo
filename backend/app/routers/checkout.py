import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Cart, CartItem, Order, OrderItem, Product, ProductVariant, ShippingMethod
from app.schemas import (
    AddressSchema,
    CustomerInfoRequest,
    ShippingMethodSelectRequest,
    ShippingMethodSchema,
    PaymentRequest,
    MoneySchema,
    OrderResponse,
    OrderItemSchema,
)
from app.routers.cart import _get_cart_or_404, _serialize_cart

router = APIRouter(prefix="/api/cart", tags=["checkout"])


@router.put("/{cart_id}/customer-info")
def update_customer_info(cart_id: str, data: CustomerInfoRequest, db: Session = Depends(get_db)):
    """Update customer email on the cart."""
    cart = _get_cart_or_404(cart_id, db)
    cart.customer_email = data.email
    db.commit()
    db.refresh(cart)
    return _serialize_cart(cart, db)


@router.put("/{cart_id}/shipping-address")
def update_shipping_address(cart_id: str, data: AddressSchema, db: Session = Depends(get_db)):
    """Update the shipping address on the cart."""
    cart = _get_cart_or_404(cart_id, db)
    cart.shipping_first_name = data.firstName
    cart.shipping_last_name = data.lastName
    cart.shipping_address1 = data.address1
    cart.shipping_address2 = data.address2
    cart.shipping_city = data.city
    cart.shipping_state = data.state
    cart.shipping_zip = data.zip
    cart.shipping_country = data.country
    cart.shipping_phone = data.phone
    db.commit()
    db.refresh(cart)
    return _serialize_cart(cart, db)


@router.put("/{cart_id}/billing-address")
def update_billing_address(cart_id: str, data: AddressSchema, db: Session = Depends(get_db)):
    """Update the billing address on the cart."""
    cart = _get_cart_or_404(cart_id, db)
    cart.billing_first_name = data.firstName
    cart.billing_last_name = data.lastName
    cart.billing_address1 = data.address1
    cart.billing_address2 = data.address2
    cart.billing_city = data.city
    cart.billing_state = data.state
    cart.billing_zip = data.zip
    cart.billing_country = data.country
    cart.billing_phone = data.phone
    db.commit()
    db.refresh(cart)
    return _serialize_cart(cart, db)


@router.get("/{cart_id}/shipping-methods")
def get_shipping_methods(cart_id: str, db: Session = Depends(get_db)):
    """Get available shipping methods."""
    _get_cart_or_404(cart_id, db)  # Validate cart exists

    methods = db.query(ShippingMethod).all()

    # If no methods in DB, return defaults
    if not methods:
        return [
            ShippingMethodSchema(
                id="standard",
                name="Standard Shipping",
                description="5-7 business days",
                price=MoneySchema(amount="5.99", currencyCode="GBP"),
                isDefault=True,
            ).model_dump(),
            ShippingMethodSchema(
                id="express",
                name="Express Shipping",
                description="2-3 business days",
                price=MoneySchema(amount="12.99", currencyCode="GBP"),
                isDefault=False,
            ).model_dump(),
            ShippingMethodSchema(
                id="overnight",
                name="Overnight Shipping",
                description="Next business day",
                price=MoneySchema(amount="24.99", currencyCode="GBP"),
                isDefault=False,
            ).model_dump(),
        ]

    return [
        ShippingMethodSchema(
            id=m.id,
            name=m.name,
            description=m.description,
            price=MoneySchema(amount=f"{m.price:.2f}", currencyCode=m.currency_code),
            isDefault=m.is_default,
        ).model_dump()
        for m in methods
    ]


@router.put("/{cart_id}/shipping-method")
def update_shipping_method(cart_id: str, data: ShippingMethodSelectRequest, db: Session = Depends(get_db)):
    """Select a shipping method for the cart."""
    cart = _get_cart_or_404(cart_id, db)

    # Check DB first
    method = db.query(ShippingMethod).filter(ShippingMethod.id == data.shippingMethodId).first()

    if method:
        cart.shipping_method_id = method.id
        cart.shipping_method_name = method.name
        cart.shipping_method_price = method.price
    else:
        # Fallback for hardcoded defaults
        defaults = {
            "standard": ("Standard Shipping", 5.99),
            "express": ("Express Shipping", 12.99),
            "overnight": ("Overnight Shipping", 24.99),
        }
        if data.shippingMethodId in defaults:
            name, price = defaults[data.shippingMethodId]
            cart.shipping_method_id = data.shippingMethodId
            cart.shipping_method_name = name
            cart.shipping_method_price = price
        else:
            raise HTTPException(status_code=404, detail="Shipping method not found")

    db.commit()
    db.refresh(cart)
    return _serialize_cart(cart, db)


@router.post("/{cart_id}/payment")
def add_payment(cart_id: str, data: PaymentRequest, db: Session = Depends(get_db)):
    """Store payment info (card last 4 only — no real processing)."""
    cart = _get_cart_or_404(cart_id, db)

    # We only store the last 4 digits for display purposes
    # In production, use a real payment processor (Stripe, etc.)
    last4 = data.cardNumber.replace(" ", "")[-4:]

    # Store temporarily on the cart (we'll use it when placing the order)
    # For now, return the cart as-is (payment info stored in session/frontend)
    return {
        "success": True,
        "cardLast4": last4,
        "cardType": _detect_card_type(data.cardNumber),
    }


@router.post("/{cart_id}/place-order")
def place_order(cart_id: str, db: Session = Depends(get_db)):
    """Convert the cart into an order."""
    cart = (
        db.query(Cart)
        .options(
            joinedload(Cart.items)
            .joinedload(CartItem.product),
        )
        .filter(Cart.id == cart_id)
        .first()
    )
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Calculate totals
    subtotal = 0.0
    currency = "GBP"
    order_items = []

    for item in cart.items:
        product = item.product
        if not product:
            continue

        price = float(product.min_price or 0)
        if item.variant_id:
            variant = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first()
            if variant:
                price = float(variant.price or 0)
                currency = variant.currency_code

        line_total = price * item.quantity
        subtotal += line_total

        order_items.append(
            OrderItem(
                product_id=product.id,
                product_title=product.title,
                variant_id=item.variant_id,
                variant_title="",
                quantity=item.quantity,
                price=price,
                currency_code=currency,
            )
        )

    shipping_cost = cart.shipping_method_price or 0
    tax = 0.0
    total = subtotal + tax + shipping_cost

    # Generate order number
    order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    order = Order(
        order_number=order_number,
        customer_email=cart.customer_email,
        status="confirmed",
        subtotal=subtotal,
        tax=tax,
        shipping_cost=shipping_cost,
        total=total,
        currency_code=currency,
        shipping_first_name=cart.shipping_first_name,
        shipping_last_name=cart.shipping_last_name,
        shipping_address1=cart.shipping_address1,
        shipping_city=cart.shipping_city,
        shipping_state=cart.shipping_state,
        shipping_zip=cart.shipping_zip,
        shipping_country=cart.shipping_country,
        shipping_method_name=cart.shipping_method_name,
        billing_first_name=cart.billing_first_name,
        billing_last_name=cart.billing_last_name,
        billing_address1=cart.billing_address1,
        billing_city=cart.billing_city,
        billing_state=cart.billing_state,
        billing_zip=cart.billing_zip,
        billing_country=cart.billing_country,
        items=order_items,
    )

    db.add(order)

    # Clear the cart items
    for item in cart.items:
        db.delete(item)

    db.commit()
    db.refresh(order)

    return OrderResponse(
        id=order.id,
        orderNumber=order.order_number,
        status=order.status,
        customerEmail=order.customer_email,
        subtotal=order.subtotal,
        tax=order.tax,
        shippingCost=order.shipping_cost,
        total=order.total,
        currencyCode=order.currency_code,
        items=[OrderItemSchema.model_validate(i) for i in order.items],
        createdAt=order.created_at,
    ).model_dump()


@router.get("/orders/{order_id}", tags=["orders"])
def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get an order by ID or order number."""
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter((Order.id == order_id) | (Order.order_number == order_id))
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderResponse(
        id=order.id,
        orderNumber=order.order_number,
        status=order.status,
        customerEmail=order.customer_email,
        subtotal=order.subtotal,
        tax=order.tax,
        shippingCost=order.shipping_cost,
        total=order.total,
        currencyCode=order.currency_code,
        items=[OrderItemSchema.model_validate(i) for i in order.items],
        createdAt=order.created_at,
    ).model_dump()


def _detect_card_type(card_number: str) -> str:
    digits = card_number.replace(" ", "")
    if digits.startswith("4"):
        return "Visa"
    elif digits[:2] in ("51", "52", "53", "54", "55"):
        return "MasterCard"
    elif digits[:2] in ("34", "37"):
        return "Amex"
    elif digits[:4] == "6011" or digits[:2] == "65":
        return "Discover"
    return "Unknown"
