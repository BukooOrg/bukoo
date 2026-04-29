"""
Seed the database with mock product and collection data.

Usage:
    cd backend
    python -m app.seed
"""

import json
import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app.models import (
    Collection,
    CollectionParent,
    Product,
    ProductImage,
    ProductOption,
    OptionValue,
    ProductVariant,
    VariantSelectedOption,
    ShippingMethod,
    User,
)
from app.auth import hash_password


def seed():
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if data already exists
        if db.query(Product).count() > 0:
            print("Database already seeded. Skipping...")
            print(f"  Products: {db.query(Product).count()}")
            print(f"  Collections: {db.query(Collection).count()}")
            print(f"  Users: {db.query(User).count()}")
            return

        print("Seeding database...")

        # ── Seed Admin User ──────────────────────────────────────────────
        admin = User(
            email="admin@store.com",
            hashed_password=hash_password("admin123"),
            full_name="Store Admin",
            role="admin",
        )
        db.add(admin)

        # Seed a test customer
        customer = User(
            email="customer@test.com",
            hashed_password=hash_password("customer123"),
            full_name="Test Customer",
            role="customer",
        )
        db.add(customer)
        print("  ✓ Users created (admin@store.com / admin123, customer@test.com / customer123)")

        # ── Seed Collections ─────────────────────────────────────────────
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

        with open(os.path.join(data_dir, "collections.json"), "r", encoding="utf-8") as f:
            collections_data = json.load(f)

        for c in collections_data:
            collection = Collection(
                handle=c["handle"],
                title=c["title"],
                description=c.get("description", ""),
                seo_title=c.get("seo", {}).get("title", ""),
                seo_description=c.get("seo", {}).get("description", ""),
                path=c.get("path", ""),
            )
            db.add(collection)
            db.flush()

            for parent in c.get("parentCategoryTree", []):
                cp = CollectionParent(
                    collection_id=collection.id,
                    parent_id=parent["id"],
                    parent_name=parent["name"],
                )
                db.add(cp)

        db.flush()
        print(f"  ✓ {len(collections_data)} collections created")

        # ── Seed Products ────────────────────────────────────────────────
        with open(os.path.join(data_dir, "products.json"), "r", encoding="utf-8") as f:
            products_data = json.load(f)

        for p in products_data:
            product = Product(
                id=p["id"] + "-" + (p.get("categoryId", "default")),  # Make unique per category
                handle=p["handle"],
                title=p["title"],
                vendor=p.get("vendor", ""),
                description=p.get("description", ""),
                description_html=p.get("descriptionHtml", ""),
                category_id=p.get("categoryId"),
                currency_code=p.get("currencyCode", "GBP"),
                min_price=p.get("priceRange", {}).get("minVariantPrice", {}).get("amount", "0"),
                max_price=p.get("priceRange", {}).get("maxVariantPrice", {}).get("amount", "0"),
                available_for_sale=p.get("availableForSale", True),
                seo_title=p.get("seo", {}).get("title", ""),
                seo_description=p.get("seo", {}).get("description", ""),
            )
            db.add(product)
            db.flush()

            # Images
            for idx, img in enumerate(p.get("images", [])):
                db.add(ProductImage(
                    product_id=product.id,
                    url=img["url"],
                    alt_text=img.get("altText", ""),
                    width=img.get("width", 1200),
                    height=img.get("height", 1200),
                    sort_order=idx,
                ))

            # Options
            for opt in p.get("options", []):
                option = ProductOption(
                    id=opt["id"] + "-" + product.id,
                    product_id=product.id,
                    name=opt["name"],
                )
                db.add(option)
                db.flush()

                for val in opt.get("values", []):
                    db.add(OptionValue(
                        id=val["id"] + "-" + option.id,
                        option_id=option.id,
                        name=val["name"],
                    ))

            # Variants
            for var in p.get("variants", []):
                variant = ProductVariant(
                    id=var["id"] + "-" + product.id[-8:],
                    product_id=product.id,
                    title=var.get("title", ""),
                    available_for_sale=var.get("availableForSale", True),
                    price=var.get("price", {}).get("amount", "0"),
                    currency_code=var.get("price", {}).get("currencyCode", "GBP"),
                )
                db.add(variant)
                db.flush()

                for so in var.get("selectedOptions", []):
                    db.add(VariantSelectedOption(
                        variant_id=variant.id,
                        name=so["name"],
                        value=so["value"],
                    ))

        db.flush()
        print(f"  ✓ {len(products_data)} products created")

        # ── Seed Shipping Methods ────────────────────────────────────────
        shipping_methods = [
            ShippingMethod(id="standard", name="Standard Shipping", description="5-7 business days", price=5.99, is_default=True),
            ShippingMethod(id="express", name="Express Shipping", description="2-3 business days", price=12.99),
            ShippingMethod(id="overnight", name="Overnight Shipping", description="Next business day", price=24.99),
        ]
        for sm in shipping_methods:
            db.add(sm)
        print("  ✓ 3 shipping methods created")

        db.commit()
        print("\n✅ Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
