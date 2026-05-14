"""
Application-wide enumerations and constants.
No external dependencies — safe to import from any layer.
"""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"


class UserStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class PaymentMethod(StrEnum):
    ONLINE_BANKING = "online_banking"
    CARD = "card"


class PaymentProvider(StrEnum):
    # RAZORPAY = "razorpay"
    pass


class ObjectStorageType(StrEnum):
    MINIO = "minio"
    S3 = "s3"


class AuthProvider(StrEnum):
    CREDENTIAL = "credential"
    GOOGLE = "google"
    FACEBOOK = "facebook"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class VerificationTokenType(StrEnum):
    EMAIL_VERIFY = "email_verify"
    PASSWORD_RESET = "password_reset"


class NotificationType(StrEnum):
    PAYMENT_SUCCESS = "payment_success"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"


ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_AVATAR_BYTES = 5 * 1024 * 1024  # 5MB

ALLOWED_COVER_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_COVER_BYTES = 1 * 1024 * 1024  # 10MB

EAST_MALAYSIA_STATES = ["sabah", "sarawak"]
ALLOWED_CANCELLED_STATUS_FOR_ADMIN = [OrderStatus.PENDING, OrderStatus.PAID]


ALLOWED_UPDATE_STATUS_FOR_ADMIN = [OrderStatus.SHIPPED, OrderStatus.DELIVERED]

ORDER_STATUS_TRANSITION_MAP: dict[OrderStatus, OrderStatus] = {
    OrderStatus.PENDING: OrderStatus.PAID,
    OrderStatus.PAID: OrderStatus.SHIPPED,
    OrderStatus.SHIPPED: OrderStatus.DELIVERED,
}
