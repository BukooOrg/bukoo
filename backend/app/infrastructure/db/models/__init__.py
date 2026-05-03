"""
models/__init__.py

Import every ORM model here so that:
  1. SQLAlchemy's mapper registry is fully populated before any query runs.
  2. All string-based relationship() forward references resolve correctly.
  3. Alembic's autogenerate can discover every table via Base.metadata.

Import order follows the FK dependency chain:
    users/accounts → addresses
    → collections → categories → publishers → authors → books → books_authors
    → wishlists/wishlist_items
    → carts/cart_items
    → orders → order_items → payments
    → reviews
    → notifications
"""

# models
from .account_model import AccountModel
from .address_model import AddressModel
from .author_model import AuthorModel
from .book_author_model import BookAuthorModel
from .book_model import BookModel
from .cart_item_model import CartItemModel
from .cart_model import CartModel
from .category_model import CategoryModel
from .collection_model import CollectionModel
from .notification_model import NotificationModel
from .order_item_model import OrderItemModel
from .order_model import OrderModel
from .payment_model import PaymentModel
from .publisher_model import PublisherModel
from .review_model import ReviewModel
from .user_model import UserModel
from .wishlist_item_model import WishlistItemModel
from .wishlist_model import WishlistModel

__all__ = [
    "UserModel",
    "AccountModel",
    "AddressModel",
    "CollectionModel",
    "CategoryModel",
    "PublisherModel",
    "AuthorModel",
    "BookModel",
    "BookAuthorModel",
    "WishlistModel",
    "WishlistItemModel",
    "CartModel",
    "CartItemModel",
    "OrderModel",
    "OrderItemModel",
    "PaymentModel",
    "ReviewModel",
    "NotificationModel",
]
