from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Cart, CartItem, Product, ProductVariant, VariantSelectedOption, ProductImage
from app.schemas import (
    AddToCartRequest,
    UpdateCartItemRequest,
    CartResponse,
    CartItemResponse,
    CartCostSchema,
    CartCostItemSchema,
    CartProductSchema,
    CartMerchandiseSchema,
    MoneySchema,
    ImageSchema,
    SelectedOptionSchema,
    AddressSchema,
    ShippingMethodSchema,
)

router = APIRouter(prefix="/api/cart", tags=["cart"])


def _get_cart_or_404(cart_id: str, db: Session) -> Cart:
    cart = (
        db.query(Cart)
        .options(
            joinedload(Cart.items)
            .joinedload(CartItem.product)
            .joinedload(Product.images),
        )
        .filter(Cart.id == cart_id)
        .first()
    )
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart


def _serialize_cart(cart: Cart, db: Session) -> dict:
    """Build the cart response shape the frontend expects."""
    lines = []
    subtotal = 0.0
    total_quantity = 0
    currency = "GBP"

    for item in cart.items:
        product = item.product
        if not product:
            continue

        # Resolve variant price
        price = 0.0
        variant_title = ""
        selected_options = []

        if item.variant_id:
            variant = (
                db.query(ProductVariant)
                .options(joinedload(ProductVariant.selected_options))
                .filter(ProductVariant.id == item.variant_id)
                .first()
            )
            if variant:
                price = float(variant.price or 0)
                variant_title = variant.title
                currency = variant.currency_code
                selected_options = [
                    SelectedOptionSchema(name=so.name, value=so.value)
                    for so in variant.selected_options
                ]
        else:
            price = float(product.min_price or 0)
            currency = product.currency_code

        line_total = price * item.quantity
        subtotal += line_total
        total_quantity += item.quantity

        images = [
            ImageSchema(url=img.url, altText=img.alt_text, width=img.width, height=img.height)
            for img in product.images
        ]
        featured = images[0] if images else ImageSchema(url="", altText="No image")

        lines.append(
            CartItemResponse(
                id=item.id,
                quantity=item.quantity,
                cost=CartCostItemSchema(
                    totalAmount=MoneySchema(amount=f"{line_total:.2f}", currencyCode=currency)
                ),
                merchandise=CartMerchandiseSchema(
                    id=item.variant_id or item.product_id,
                    title=variant_title or product.title,
                    selectedOptions=selected_options,
                    product=CartProductSchema(
                        id=product.id,
                        handle=product.handle,
                        title=product.title,
                        images=images,
                        featuredImage=featured,
                    ),
                ),
            ).model_dump()
        )

    shipping_cost = cart.shipping_method_price or 0
    tax = subtotal * 0.0  # Could implement tax calculation
    total = subtotal + tax + shipping_cost

    # Build address objects
    shipping_address = None
    if cart.shipping_address1:
        shipping_address = AddressSchema(
            firstName=cart.shipping_first_name,
            lastName=cart.shipping_last_name,
            address1=cart.shipping_address1,
            address2=cart.shipping_address2,
            city=cart.shipping_city,
            state=cart.shipping_state,
            zip=cart.shipping_zip,
            country=cart.shipping_country,
            phone=cart.shipping_phone,
        ).model_dump()

    billing_address = None
    if cart.billing_address1:
        billing_address = AddressSchema(
            firstName=cart.billing_first_name,
            lastName=cart.billing_last_name,
            address1=cart.billing_address1,
            address2=cart.billing_address2,
            city=cart.billing_city,
            state=cart.billing_state,
            zip=cart.billing_zip,
            country=cart.billing_country,
            phone=cart.billing_phone,
        ).model_dump()

    shipping_method = None
    if cart.shipping_method_id:
        shipping_method = ShippingMethodSchema(
            id=cart.shipping_method_id,
            name=cart.shipping_method_name,
            price=MoneySchema(amount=f"{shipping_cost:.2f}", currencyCode=currency),
        ).model_dump()

    return CartResponse(
        id=cart.id,
        checkoutUrl=cart.checkout_url or "/checkout/information",
        customerEmail=cart.customer_email,
        cost=CartCostSchema(
            subtotalAmount=MoneySchema(amount=f"{subtotal:.2f}", currencyCode=currency),
            totalAmount=MoneySchema(amount=f"{total:.2f}", currencyCode=currency),
            totalTaxAmount=MoneySchema(amount=f"{tax:.2f}", currencyCode=currency),
            shippingAmount=MoneySchema(amount=f"{shipping_cost:.2f}", currencyCode=currency) if shipping_cost else None,
        ),
        lines=lines,
        totalQuantity=total_quantity,
        shippingAddress=shipping_address,
        billingAddress=billing_address,
        shippingMethod=shipping_method,
    ).model_dump()


@router.post("")
def create_cart(db: Session = Depends(get_db)):
    """Create a new empty cart."""
    cart = Cart()
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return _serialize_cart(cart, db)


@router.get("/{cart_id}")
def get_cart(cart_id: str, db: Session = Depends(get_db)):
    """Get cart by ID."""
    cart = _get_cart_or_404(cart_id, db)
    return _serialize_cart(cart, db)


@router.post("/{cart_id}/items")
def add_item(cart_id: str, data: AddToCartRequest, db: Session = Depends(get_db)):
    """Add an item to the cart."""
    cart = _get_cart_or_404(cart_id, db)

    # Check if the merchandise ID is a variant or product
    variant = db.query(ProductVariant).filter(ProductVariant.id == data.merchandiseId).first()
    if variant:
        product_id = variant.product_id
        variant_id = variant.id
    else:
        product = db.query(Product).filter(Product.id == data.merchandiseId).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        product_id = product.id
        variant_id = None

    # Check if item already in cart
    existing = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
            CartItem.variant_id == variant_id,
        )
        .first()
    )

    if existing:
        existing.quantity += data.quantity
    else:
        item = CartItem(
            cart_id=cart_id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=data.quantity,
        )
        db.add(item)

    db.commit()

    # Re-fetch with relationships
    cart = _get_cart_or_404(cart_id, db)
    return _serialize_cart(cart, db)


@router.put("/{cart_id}/items/{item_id}")
def update_item(cart_id: str, item_id: str, data: UpdateCartItemRequest, db: Session = Depends(get_db)):
    """Update cart item quantity."""
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if data.quantity <= 0:
        db.delete(item)
    else:
        item.quantity = data.quantity

    db.commit()

    cart = _get_cart_or_404(cart_id, db)
    return _serialize_cart(cart, db)


@router.delete("/{cart_id}/items/{item_id}")
def remove_item(cart_id: str, item_id: str, db: Session = Depends(get_db)):
    """Remove an item from the cart."""
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(item)
    db.commit()

    cart = _get_cart_or_404(cart_id, db)
    return _serialize_cart(cart, db)
