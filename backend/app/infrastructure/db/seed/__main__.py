"""
Bukoo Database Seed Script
==========================
Seeds the database with initial data from CSV files.

Run from the `backend/` folder:
    uv run python -m app.infrastructure.db.seed

Seeding order:
    1. Truncate all tables (CASCADE)
    2. Seed collections   → app/infrastructure/db/data/bukoo_dataset_collection.csv
    3. Seed categories    → app/infrastructure/db/data/bukoo_dataset_category.csv
    4. Seed books         → app/infrastructure/db/data/bukoo_dataset_book.csv
       - Downloads cover image from URL, uploads to MinIO as pub/cover/{book_id}
       - Populates: publishers, authors, books, books_authors tables
       - 'N/A' values are treated as NULL for optional columns
"""

from __future__ import annotations

import asyncio
import csv
import random
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.util import uuid7_str
from app.infrastructure.storage.minio_storage import MinIOStorage

from ..session import session_scope

DATA_DIR = Path(__file__).parent / "data"

COLLECTION_CSV = DATA_DIR / "bukoo_dataset_collection.csv"
CATEGORY_CSV = DATA_DIR / "bukoo_dataset_category.csv"
BOOK_CSV = DATA_DIR / "bukoo_dataset_book.csv"

# Tables to truncate in dependency-safe order (most-dependent first)
TRUNCATE_TABLES = [
    "notifications",
    "reviews",
    "payments",
    "order_items",
    "orders",
    "cart_items",
    "carts",
    "wishlist_items",
    "wishlists",
    "books_authors",
    "books",
    "authors",
    "publishers",
    "categories",
    "collections",
    "addresses",
    "accounts",
    "users",
]

storage = MinIOStorage()


def na(value: str) -> str | None:
    """Return None if value is 'N/A' (case-insensitive), else the value."""
    return None if value.strip().upper() == "N/A" else value.strip() or None


def read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


async def download_image(url: str) -> tuple[bytes, str] | None:
    """Download an image from a URL. Returns (bytes, content_type) or None on failure."""
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            content_type = (
                resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
            )
            return resp.content, content_type
    except Exception as exc:
        print(f"    ⚠  Could not download cover from {url}: {exc}")
        return None


# step 1 — Truncate all tables
async def truncate_all_tables(session: AsyncSession) -> None:
    print("\n[1/4] Truncating all tables...")
    tables_joined = ", ".join(TRUNCATE_TABLES)
    await session.execute(
        text(f"TRUNCATE TABLE {tables_joined} RESTART IDENTITY CASCADE")
    )
    await session.commit()
    print(f"    ✅ Truncated {len(TRUNCATE_TABLES)} tables.")


# step 2 — Seed collections
async def seed_collections(session: AsyncSession) -> dict[str, str]:
    """Returns {collection_name: collection_id}"""
    print("\n[2/4] Seeding collections...")
    rows = read_csv(COLLECTION_CSV)
    collection_map: dict[str, str] = {}
    count = 0

    for row in rows:
        cid = uuid7_str()
        name = row["name"].strip()
        url_slug = row["url_slug"].strip()

        await session.execute(
            text(
                "INSERT INTO collections (id, name, url_slug, created_at, updated_at) "
                "VALUES (:id, :name, :url_slug, NOW(), NOW())"
            ),
            {"id": cid, "name": name, "url_slug": url_slug},
        )
        collection_map[name] = cid
        count += 1

    await session.commit()
    print(f"    ✅ Successfully inserted {count} collection(s).")
    return collection_map


# step 3 — Seed categories
async def seed_categories(
    session: AsyncSession,
    collection_map: dict[str, str],
) -> dict[str, str]:
    """Returns {category_name: category_id}"""
    print("\n[3/4] Seeding categories...")
    rows = read_csv(CATEGORY_CSV)
    category_map: dict[str, str] = {}
    count = 0

    for row in rows:
        cid = uuid7_str()
        name = row["name"].strip()
        url_slug = row["url_slug"].strip()
        collection_name = row["collection"].strip()

        collection_id = collection_map.get(collection_name)
        if not collection_id:
            print(
                f"    ⚠  Unknown collection '{collection_name}' for category '{name}' — skipping."
            )
            continue

        await session.execute(
            text(
                "INSERT INTO categories (id, collection_id, name, url_slug, created_at, updated_at) "
                "VALUES (:id, :collection_id, :name, :url_slug, NOW(), NOW())"
            ),
            {
                "id": cid,
                "collection_id": collection_id,
                "name": name,
                "url_slug": url_slug,
            },
        )
        category_map[name] = cid
        count += 1

    await session.commit()
    print(f"    ✅ Successfully inserted {count} category/categories.")
    return category_map


# Step 4 — Seed books (publishers, authors, books, books_authors, MinIO)
async def seed_books(
    session: AsyncSession,
    category_map: dict[str, str],
) -> int:
    """
    Seeds publishers, authors, books, and books_authors tables.
    Uploads cover images to MinIO.
    Returns total number of book rows inserted.
    """
    print("\n[4/4] Seeding books...")
    rows = read_csv(BOOK_CSV)

    # In-memory caches to deduplicate publishers and authors within this run
    publisher_cache: dict[str, str] = {}  # {publisher_name: publisher_id}
    author_cache: dict[str, str] = {}  # {author_name: author_id}

    book_count = 0

    for idx, row in enumerate(rows, start=1):
        title = row["title"].strip()
        isbn = na(row.get("isbn", "N/A"))
        description = na(row.get("description", "N/A"))
        cover_url_src = na(row.get("cover_url", "N/A"))
        price_raw = na(row.get("price", "N/A"))
        page_count_raw = na(row.get("page_count", "N/A"))
        language = row.get("language", "English").strip() or "English"
        published_date_raw = na(row.get("published_date", "N/A"))
        publisher_name = na(row.get("publisher_name", "N/A"))
        author_names_raw = na(row.get("author_name", "N/A"))
        category_name = row.get("category", "").strip() or None

        # skip empty row
        if not title:
            continue

        # parse numeric fields
        rand_price = Decimal(
            str(random.randint(2000, 30000) / 100)
        )  # ensures 2 decimal places
        try:
            price = Decimal(price_raw) if price_raw else rand_price
        except ValueError:
            price = rand_price

        try:
            page_count = int(page_count_raw) if page_count_raw else None
        except ValueError:
            page_count = None

        stock_quantity = random.randint(2, 10)

        category_id = category_map.get(category_name) if category_name else None

        # publisher (deduplicate by name)
        publisher_id: str | None = None
        if publisher_name:
            if publisher_name in publisher_cache:
                publisher_id = publisher_cache[publisher_name]
            else:
                publisher_id = uuid7_str()
                await session.execute(
                    text(
                        "INSERT INTO publishers (id, name, created_at, updated_at) "
                        "VALUES (:id, :name, NOW(), NOW()) "
                        "ON CONFLICT (name) DO NOTHING"
                    ),
                    {"id": publisher_id, "name": publisher_name},
                )
                # re-fetch id in case ON CONFLICT suppressed insertion
                result = await session.execute(
                    text("SELECT id FROM publishers WHERE name = :name"),
                    {"name": publisher_name},
                )
                publisher_id = result.scalar_one()
                assert publisher_id is not None
                publisher_cache[publisher_name] = publisher_id

        book_id = uuid7_str()

        # download & upload cover image to MinIO
        cover_key: str | None = None
        if cover_url_src:
            print(f"    [{idx}/{len(rows)}] Downloading cover for '{title}'...")
            image_data = await download_image(cover_url_src)
            if image_data:
                img_bytes, content_type = image_data
                cover_key = f"pub/covers/{book_id}"
                try:
                    await storage.upload(
                        key=cover_key, data=img_bytes, content_type=content_type
                    )
                    print(f"         ✅ Uploaded cover → {cover_key}")
                except Exception as exc:
                    print(f"         ⚠  MinIO upload failed for '{title}': {exc}")
                    cover_key = None

        published_date = (
            datetime.strptime(published_date_raw, "%Y-%m-%d").date()
            if published_date_raw is not None
            else None
        )

        # insert book
        await session.execute(
            text(
                """
                INSERT INTO books (
                    id, title, isbn, description, cover_url,
                    price, stock_quantity, page_count, language,
                    published_date, publisher_id, category_id,
                    created_at, updated_at
                ) VALUES (
                    :id, :title, :isbn, :description, :cover_url,
                    :price, :stock_quantity, :page_count, :language,
                    :published_date, :publisher_id, :category_id,
                    NOW(), NOW()
                )
                """
            ),
            {
                "id": book_id,
                "title": title,
                "isbn": isbn,
                "description": description,
                "cover_url": cover_key,
                "price": price,
                "stock_quantity": stock_quantity,
                "page_count": page_count,
                "language": language.lower(),
                "published_date": published_date,
                "publisher_id": publisher_id,
                "category_id": category_id,
            },
        )

        if author_names_raw:
            raw_authors = [a.strip() for a in author_names_raw.split(",") if a.strip()]
            for display_order, author_name in enumerate(raw_authors, start=1):
                if not author_name:
                    continue

                if author_name in author_cache:
                    author_id = author_cache[author_name]
                else:
                    # authors table has no unique constraint on name —
                    # deduplication is handled purely in-memory via the cache.
                    author_id = uuid7_str()
                    await session.execute(
                        text(
                            "INSERT INTO authors (id, name, created_at, updated_at) "
                            "VALUES (:id, :name, NOW(), NOW())"
                        ),
                        {"id": author_id, "name": author_name},
                    )
                    author_cache[author_name] = author_id

                await session.execute(
                    text(
                        "INSERT INTO books_authors (book_id, author_id, display_order, created_at, updated_at) "
                        "VALUES (:book_id, :author_id, :display_order, NOW(), NOW()) "
                        "ON CONFLICT DO NOTHING"
                    ),
                    {
                        "book_id": book_id,
                        "author_id": author_id,
                        "display_order": display_order,
                    },
                )

        book_count += 1

    await session.commit()
    print(f"\n    ✅ Successfully inserted {book_count} book(s).")
    return book_count


# main entry point
async def main() -> None:
    print("=" * 60)
    print("  Bukoo Database Seed Script")
    print("=" * 60)

    successful_tables = 0

    async with session_scope() as session:
        # Step 1 — Truncate
        await truncate_all_tables(session)

        # Step 2 — Collections
        collection_map = await seed_collections(session)
        successful_tables += 1

        # Step 3 — Categories
        category_map = await seed_categories(session, collection_map)
        successful_tables += 1

        # Step 4 — Books (+ publishers, authors, books_authors)
        await seed_books(session, category_map)
        # books, publishers, authors, books_authors all seeded in one step
        successful_tables += 4  # books, publishers, authors, books_authors

    print("\n" + "=" * 60)
    print(f"  ✅ Seeding complete. {successful_tables} table(s) seeded successfully.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
