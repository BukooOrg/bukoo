from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.database import get_db
from app.models import Collection, CollectionParent, Product
from app.schemas import CollectionResponse, SEOSchema, ParentCategorySchema
from app.routers.products import _serialize_product, _load_product_query

router = APIRouter(prefix="/api/collections", tags=["collections"])

# The root category should be excluded from public listings
ROOT_CATEGORY_ID = "joyco-root"


def _serialize_collection(c: Collection) -> dict:
    return CollectionResponse(
        handle=c.handle,
        title=c.title,
        description=c.description,
        seo=SEOSchema(title=c.seo_title, description=c.seo_description),
        parentCategoryTree=[
            ParentCategorySchema(id=p.parent_id, name=p.parent_name)
            for p in c.parent_categories
        ],
        updatedAt=c.updated_at.isoformat() if c.updated_at else "",
        path=c.path,
    ).model_dump()


@router.get("")
def list_collections(db: Session = Depends(get_db)):
    """List all collections, excluding the root category."""
    collections = (
        db.query(Collection)
        .options(joinedload(Collection.parent_categories))
        .filter(Collection.handle != ROOT_CATEGORY_ID)
        .all()
    )
    return [_serialize_collection(c) for c in collections]


@router.get("/{handle}")
def get_collection(handle: str, db: Session = Depends(get_db)):
    """Get a single collection by handle."""
    collection = (
        db.query(Collection)
        .options(joinedload(Collection.parent_categories))
        .filter(Collection.handle == handle, Collection.handle != ROOT_CATEGORY_ID)
        .first()
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    return _serialize_collection(collection)


@router.get("/{handle}/products")
def get_collection_products(
    handle: str,
    sortKey: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get all products in a collection, including child categories."""
    collection = db.query(Collection).filter(Collection.handle == handle).first()
    if not collection:
        return []

    # Find child categories that have this collection in their parent tree
    child_ids = (
        db.query(CollectionParent.collection_id)
        .filter(CollectionParent.parent_id == handle)
        .all()
    )
    category_ids = [handle] + [c[0] for c in child_ids]

    q = _load_product_query(db).filter(Product.category_id.in_(category_ids))

    if sortKey == "price-low-to-high":
        q = q.order_by(Product.min_price.asc())
    elif sortKey == "price-high-to-low":
        q = q.order_by(Product.max_price.desc())
    elif sortKey == "product-name-ascending":
        q = q.order_by(Product.title.asc())
    elif sortKey == "product-name-descending":
        q = q.order_by(Product.title.desc())

    products = q.limit(limit).all()

    # Deduplicate by id
    seen = set()
    unique = []
    for p in products:
        if p.id not in seen:
            seen.add(p.id)
            unique.append(p)

    return [_serialize_product(p) for p in unique]
