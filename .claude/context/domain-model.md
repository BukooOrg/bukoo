# Domain Model Reference — Bukoo

Complete reference for domain entities, relationships, and invariants.
Read this before adding new entities, writing use cases, or designing repository
interfaces.

---

## Entity Inventory

All entities are pure Python `@dataclass` classes in `app/domain/entities/`.
All IDs are UUIDv7 strings. All entities have `_created_at`, `_updated_at`,
`_deleted_at` tracking fields.

| Entity | File | Purpose |
|--------|------|---------|
| `UserEntity` | `user_entity.py` | Platform account (customer or admin) |
| `AccountEntity` | `account_entity.py` | OAuth provider link (e.g. Google) |
| `AddressEntity` | `address_entity.py` | Shipping/billing address |
| `BookEntity` | `book_entity.py` | Product (book) for sale |
| `AuthorEntity` | `author_entity.py` | Book author |
| `BookAuthorEntity` | `book_author_entity.py` | Book ↔ Author join (with display_order) |
| `PublisherEntity` | `publisher_entity.py` | Book publisher |
| `CategoryEntity` | `category_entity.py` | Book genre/category |
| `CollectionEntity` | `collection_entity.py` | Editorial collection (curated set of books) |
| `CartEntity` | `cart_entity.py` | Active shopping cart (one per user) |
| `CartItemEntity` | `cart_item_entity.py` | Line item in a cart |
| `OrderEntity` | `order_entity.py` | Placed order |
| `OrderItemEntity` | `order_item_entity.py` | Line item in an order (snapshot of book price) |
| `PaymentEntity` | `payment_entity.py` | Payment record for an order |
| `ReviewEntity` | `review_entity.py` | User review of a book |
| `WishlistEntity` | `wishlist_entity.py` | User's wishlist |
| `WishlistItemEntity` | `wishlist_item_entity.py` | Line item in a wishlist |
| `NotificationEntity` | `notification_entity.py` | In-app notification |

---

## Relationships

```
User (1) ──────────── (n) Account          # OAuth provider links
User (1) ──────────── (1) Address          # shipping address
User (1) ──────────── (1) Cart             # one active cart per user
User (1) ──────────── (n) Order            # purchase history
User (1) ──────────── (1) Wishlist         # saved-for-later
User (1) ──────────── (n) Review           # book reviews
User (1) ──────────── (n) Notification     # in-app notifications

Cart (1) ──────────── (n) CartItem
CartItem (n) ─────── (1) Book             # which book is in the cart

Wishlist (1) ─────── (n) WishlistItem
WishlistItem (n) ─── (1) Book

Order (1) ─────────── (n) OrderItem
OrderItem (n) ────── (1) Book             # price is snapshotted at order time
Order (1) ─────────── (1) Payment         # payment for this order

Book (1) ──────────── (n) BookAuthor      # ordered list of authors
BookAuthor (n) ────── (1) Author          # many-to-many Book ↔ Author via join entity
Book (n) ──────────── (1) Category        # genre
Book (n) ──────────── (1) Publisher       # publisher
```

---

## Key Entity Fields

### UserEntity
```
_id: str                   (UUIDv7)
_email: str                (unique)
_full_name: str
_date_of_birth: date
_role: UserRole            (admin | user)
_status: UserStatus        (pending | active | suspended)
_hashed_password: str|None (None for OAuth-only users)
_avatar_url: str|None
_last_login_at: datetime|None
_accounts: list[AccountEntity]   (selectin-loaded)
_address: AddressEntity|None     (selectin-loaded)
```

### BookEntity
```
_id: str                   (UUIDv7)
_title: str
_price: Decimal
_stock_quantity: int
_language: str
_publisher_id: str|None    (FK reference)
_category_id: str|None     (FK reference)
_isbn: str|None            (ISBN-13)
_description: str|None
_cover_url: str|None       (MinIO/S3 object key or full URL)
_page_count: int|None
_published_date: date|None
_deactivated_at: datetime|None   (separate from soft-delete)
_publisher: PublisherEntity|None  (selectin-loaded)
_category: CategoryEntity|None    (selectin-loaded)
_authors: list[BookAuthorEntity]  (selectin-loaded, ordered by display_order)
```

### OrderEntity
```
_id: str                   (UUIDv7)
_user_id: str              (FK reference)
_status: OrderStatus       (pending | paid | shipped | delivered | cancelled)
_total_amount: Decimal     (sum of items at time of order)
_items: list[OrderItemEntity]   (selectin-loaded)
_payment: PaymentEntity|None    (selectin-loaded, 1:1)
```

### OrderItemEntity
```
_id: str
_order_id: str
_book_id: str
_quantity: int
_unit_price: Decimal       (price snapshot at order time — does not change if book price changes)
_book: BookEntity|None     (selectin-loaded)
```

---

## Aggregate Boundaries

An aggregate is a cluster of entities treated as a unit for persistence. The
aggregate root is the entity through which all modifications must go.

| Aggregate Root | Members | Notes |
|----------------|---------|-------|
| `UserEntity` | `AccountEntity`, `AddressEntity` | Only save/update via UserRepository |
| `BookEntity` | `BookAuthorEntity` | Use `book.set_author()` to modify authors |
| `OrderEntity` | `OrderItemEntity`, `PaymentEntity` | Order status transitions via `order` methods |
| `CartEntity` | `CartItemEntity` | Cart operations via `cart` methods |
| `WishlistEntity` | `WishlistItemEntity` | Wishlist operations via `wishlist` methods |

Standalone entities (own aggregate): `Author`, `Publisher`, `Category`,
`Collection`, `Notification`, `Review`.

---

## Soft-Delete Policy

All entities support soft-delete via `_deleted_at: datetime | None`.
A `None` value means the record is live; a datetime means it is soft-deleted.

Repository queries **always** filter `Model.deleted_at.is_(None)` by default.
Use `find_by_id_including_deleted()` (or equivalent) for admin operations
that need to see deleted records.

Entities that also have a `_deactivated_at` field:
- `BookEntity` — `deactivated_at` hides a book from the storefront without
  deleting it. Different from `deleted_at` (admin hard-removal). A book can be
  deactivated while live in the DB.

---

## ID Strategy

All entity IDs are **UUIDv7 strings**.

```python
from uuid_extension import uuid7
id = str(uuid7())
```

UUIDv7 is time-ordered (timestamp in the most-significant bits), which gives
natural insert-order locality in B-tree indexes. Do not use `uuid.uuid4()`.

ORM models auto-generate the ID via `insert_default=uuid7_str` on the `id`
column. When constructing an entity manually (in a use case), generate the ID
with `str(uuid7())` and pass it as `_id=`.

---

## Domain Enums

All enums use `StrEnum` (Python 3.11+) from `app/core/constants.py`.
They are importable from any layer including `domain/`.

```python
class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"

class UserStatus(StrEnum):
    PENDING = "pending"    # registered but email not verified
    ACTIVE = "active"      # verified, can log in
    SUSPENDED = "suspended"

class OrderStatus(StrEnum):
    PENDING = "pending"    # created, not paid
    PAID = "paid"          # payment confirmed
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

class AuthProvider(StrEnum):
    CREDENTIAL = "credential"   # email + password
    GOOGLE = "google"           # OAuth

class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
```

---

## Key Domain Invariants

| Entity | Invariant |
|--------|-----------|
| `UserEntity` | A user with `hashed_password=None` must have at least one OAuth `Account` |
| `UserEntity` | Status transitions: `PENDING → ACTIVE` (via `activate()`), `ACTIVE → SUSPENDED` (via `suspend()`) |
| `BookEntity` | `stock_quantity` must never go below 0; `decrease_stock()` raises `ValueError` if qty > stock |
| `BookEntity` | ISBN must pass ISBN-13 checksum validation (enforced in `application/validators/`) |
| `OrderEntity` | `OrderAlreadyPaidError` if attempting to pay an order with `status != PENDING` |
| `OrderEntity` | `EmptyOrderError` if creating an order with no items |
| `CartEntity` | One active cart per user; duplicate book → increase quantity, not new line item |
| `OrderItemEntity` | `unit_price` is captured at order creation time and must not change afterwards |

---

## Repository Interface Inventory

Current repository interfaces in `app/domain/repositories/`:

| Interface | File | Methods |
|-----------|------|---------|
| `IUserRepository` | `user_repository.py` | `find_by_id`, `find_by_id_including_deleted`, `find_by_email`, `save`, `soft_delete`, `exists_by_email`, `count_including_deleted` |
| `IAccountRepository` | `account_repository.py` | `find_by_provider_and_open_id`, `save` |

All other entity repositories (Book, Order, Cart, etc.) need to be created as
the corresponding use cases are built. Follow the pattern in `user_repository.py`.
