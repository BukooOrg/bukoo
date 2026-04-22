from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.database import get_db
from app.models import Product, ProductImage, ProductOption, OptionValue, ProductVariant, VariantSelectedOption, Collection
from app.schemas import ProductResponse, ImageSchema, ProductOptionSchema, OptionValueSchema, ProductVariantSchema, SelectedOptionSchema, MoneySchema, SEOSchema

router = APIRouter(prefix="/api/products", tags=["products"])


def _serialize_product(p: Product) -> dict:
    """Convert a Product ORM object to the response shape the frontend expects."""
    images = [
        ImageSchema(url=img.url, altText=img.alt_text, width=img.width, height=img.height)
        for img in p.images
    ]
    featured_image = images[0] if images else ImageSchema(url="", altText="No image")

    options = [
        ProductOptionSchema(
            id=opt.id,
            name=opt.name,
            values=[OptionValueSchema(id=v.id, name=v.name) for v in opt.values],
        )
        for opt in p.options
    ]

    variants = [
        ProductVariantSchema(
            id=var.id,
            title=var.title,
            availableForSale=var.available_for_sale,
            selectedOptions=[
                SelectedOptionSchema(name=so.name, value=so.value)
                for so in var.selected_options
            ],
            price=MoneySchema(amount=var.price, currencyCode=var.currency_code),
        )
        for var in p.variants
    ]

    return ProductResponse(
        id=p.id,
        handle=p.handle,
        title=p.title,
        vendor=p.vendor,
        description=p.description,
        descriptionHtml=p.description_html,
        categoryId=p.category_id,
        tags=[],
        featuredImage=featured_image,
        availableForSale=p.available_for_sale,
        currencyCode=p.currency_code,
        priceRange={
            "maxVariantPrice": {"amount": p.max_price, "currencyCode": p.currency_code},
            "minVariantPrice": {"amount": p.min_price, "currencyCode": p.currency_code},
        },
        images=images,
        options=options,
        seo=SEOSchema(title=p.seo_title, description=p.seo_description),
        variants=variants,
    ).model_dump()


def _load_product_query(db: Session):
    """Return a query with all product relationships eagerly loaded."""
    return db.query(Product).options(
        joinedload(Product.images),
        joinedload(Product.options).joinedload(ProductOption.values),
        joinedload(Product.variants).joinedload(ProductVariant.selected_options),
    )


@router.get("")
def list_products(
    query: Optional[str] = Query(None),
    sortKey: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List/search products. Supports optional text search and sorting."""
    q = _load_product_query(db)

    if query:
        q = q.filter(Product.title.ilike(f"%{query}%"))

    if sortKey == "price-low-to-high":
        q = q.order_by(Product.min_price.asc())
    elif sortKey == "price-high-to-low":
        q = q.order_by(Product.max_price.desc())
    elif sortKey == "product-name-ascending":
        q = q.order_by(Product.title.asc())
    elif sortKey == "product-name-descending":
        q = q.order_by(Product.title.desc())

    # Deduplicate by handle (mock data has duplicates for different categories)
    products = q.limit(limit).all()
    seen_handles = set()
    unique = []
    for p in products:
        if p.handle not in seen_handles:
            seen_handles.add(p.handle)
            unique.append(p)

    return [_serialize_product(p) for p in unique]


@router.get("/{handle}")
def get_product(handle: str, db: Session = Depends(get_db)):
    """Get a single product by its handle/slug."""
    product = _load_product_query(db).filter(Product.handle == handle).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return _serialize_product(product)


@router.get("/{product_id}/recommendations")
def get_recommendations(product_id: str, db: Session = Depends(get_db)):
    """Get product recommendations based on the same category."""
    product = db.query(Product).filter(
        (Product.id == product_id) | (Product.handle == product_id)
    ).first()

    if not product or not product.category_id:
        return []

    related = _load_product_query(db).filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
    ).limit(10).all()

    # Deduplicate
    seen = set()
    unique = []
    for p in related:
        if p.handle not in seen:
            seen.add(p.handle)
            unique.append(p)

    return [_serialize_product(p) for p in unique]
