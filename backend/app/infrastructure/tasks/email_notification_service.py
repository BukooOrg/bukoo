from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, override

from app.application.dtos.payment_dto import PaymentReceiptItem
from app.application.interfaces.email_notification_service import (
    IEmailNotificationService,
)
from app.core.config import get_configs
from app.core.util import construct_order_ref
from app.infrastructure.tasks.email_tasks import send_mail

_HEADER_BG = "#1a1a2e"
_CANCEL_ACCENT = "#c0392b"
_CANCEL_BG = "#fff5f5"
_SHIP_ACCENT = "#2980b9"
_SHIP_BG = "#f0f7ff"
_DELIVER_ACCENT = "#27ae60"
_DELIVER_BG = "#f0faf4"


def _header_html(brand_name: str) -> str:
    return (
        f'<div style="background:{_HEADER_BG};padding:28px 24px;text-align:center;">'
        f'<h1 style="color:#fff;margin:0;font-size:26px;letter-spacing:1px;">{brand_name}</h1>'
        f'<p style="color:#aaa;margin:4px 0 0;font-size:13px;">Your Premium Bookstore</p>'
        f"</div>"
    )


def _footer_html(brand_name: str) -> str:
    return (
        f'<div style="background:#f5f5f5;padding:20px 24px;text-align:center;font-size:12px;color:#888;'
        f'border-top:1px solid #e0e0e0;">'
        f'<p style="margin:0 0 4px;">Questions? Contact us at '
        f'<a href="mailto:support@bukoo.com" style="color:{_HEADER_BG};">support@bukoo.com</a></p>'
        f'<p style="margin:0;">&copy; 2026 {brand_name}. All rights reserved.</p>'
        f"</div>"
    )


def _item_rows_html(items: list[PaymentReceiptItem]) -> str:
    return "".join(
        f"<tr>"
        f'<td style="padding:8px 6px;border-bottom:1px solid #eee;">{item.book_title}</td>'
        f'<td style="padding:8px 6px;border-bottom:1px solid #eee;text-align:center;">{item.quantity}</td>'
        f'<td style="padding:8px 6px;border-bottom:1px solid #eee;text-align:right;">RM {item.unit_price:.2f}</td>'
        f'<td style="padding:8px 6px;border-bottom:1px solid #eee;text-align:right;">RM {item.line_total:.2f}</td>'
        f"</tr>"
        for item in items
    )


def _item_table_html(items: list[PaymentReceiptItem], section_title: str) -> str:
    return (
        f'<h3 style="font-size:15px;border-bottom:2px solid #eee;padding-bottom:8px;margin-bottom:12px;">'
        f"{section_title}</h3>"
        f'<table width="100%" cellpadding="0" cellspacing="0" style="font-size:13px;border-collapse:collapse;">'
        f"<thead>"
        f'<tr style="background:#f5f5f5;">'
        f'<th style="padding:8px 6px;text-align:left;font-weight:600;">Title</th>'
        f'<th style="padding:8px 6px;text-align:center;font-weight:600;">Qty</th>'
        f'<th style="padding:8px 6px;text-align:right;font-weight:600;">Unit Price</th>'
        f'<th style="padding:8px 6px;text-align:right;font-weight:600;">Subtotal</th>'
        f"</tr>"
        f"</thead>"
        f"<tbody>{_item_rows_html(items)}</tbody>"
        f"</table>"
    )


def _total_row_html(label: str, total: Decimal) -> str:
    return (
        f'<table width="100%" cellpadding="0" cellspacing="0"'
        f' style="font-size:14px;margin-top:16px;border-collapse:collapse;">'
        f'<tr style="border-top:2px solid #333;">'
        f'<td style="padding:10px 0;font-size:16px;font-weight:bold;">{label}</td>'
        f'<td style="padding:10px 0;text-align:right;font-size:16px;font-weight:bold;">RM {total:.2f}</td>'
        f"</tr>"
        f"</table>"
    )


class CeleryEmailNotificationService(IEmailNotificationService):
    @override
    def send_welcome(self, to: str, full_name: str) -> None:
        configs = get_configs()
        send_mail.delay(
            to=to,
            subject=f"Welcome to {configs.APP_NAME.capitalize()}!",
            body_html=(
                f"<h1>Welcome, {full_name}!</h1>"
                f"<p>Your account has been created. Please verify your email to get started.</p>"
            ),
        )

    @override
    def send_verification_email(self, to: str, otp: str) -> None:
        send_mail.delay(
            to=to,
            subject="Verify your email address",
            body_html=(
                f"<h1>Email Verification</h1>"
                f"<p>Your verification code is: <strong>{otp}</strong></p>"
                f"<p>This code expires in 15 minutes.</p>"
            ),
        )

    @override
    def send_password_reset_email(self, to: str, otp: str) -> None:
        send_mail.delay(
            to=to,
            subject="Reset your password",
            body_html=(
                f"<h1>Password Reset</h1>"
                f"<p>Your password reset code is: <strong>{otp}</strong></p>"
                f"<p>This code expires in 15 minutes.</p>"
            ),
        )

    @override
    def send_payment_receipt(
        self,
        to: str,
        full_name: str,
        order_id: str,
        payment_ref: str,
        payment_method_display: str,
        items: list[PaymentReceiptItem],
        subtotal: Decimal,
        shipping_cost: Decimal,
        total: Decimal,
        address_snapshot: dict[str, Any],
        paid_at: datetime,
    ) -> None:
        configs = get_configs()
        brand_name = configs.APP_NAME.capitalize()
        order_ref = construct_order_ref(order_id)
        paid_at_str = paid_at.strftime("%d %b %Y, %I:%M %p UTC")

        addr = address_snapshot
        address_lines = "<br>".join(
            line
            for line in [
                str(addr.get("recipient_name", "")),
                str(addr.get("phone", "")),
                str(addr.get("street_address", "")),
                f"{addr.get('city', '')} {addr.get('postcode', '')}".strip(),
                f"{addr.get('state', '')}, {addr.get('country', '')}".strip(", "),
            ]
            if line.strip()
        )

        body_html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333;background:#fff;">

  {_header_html(brand_name)}

  <div style="background:{_DELIVER_BG};padding:24px;border-left:4px solid {_DELIVER_ACCENT};">
    <h2 style="color:{_DELIVER_ACCENT};margin:0 0 8px;">&#10003; Payment Confirmed</h2>
    <p style="margin:0;font-size:15px;">Hi <strong>{full_name}</strong>,</p>
    <p style="margin:8px 0 0;font-size:14px;color:#555;">
      Thank you for your purchase! We have received your payment and your order
      is now being prepared for shipment.
    </p>
  </div>

  <div style="padding:24px;">
    <h3 style="font-size:15px;border-bottom:2px solid #eee;padding-bottom:8px;margin-bottom:12px;">
      Receipt Details
    </h3>
    <table width="100%" cellpadding="0" cellspacing="0"
           style="font-size:14px;border-collapse:collapse;">
      <tr>
        <td style="padding:6px 0;color:#666;width:50%;">Order Reference</td>
        <td style="padding:6px 0;text-align:right;font-weight:bold;">{order_ref}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#666;">Payment Reference</td>
        <td style="padding:6px 0;text-align:right;">{payment_ref}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#666;">Payment Method</td>
        <td style="padding:6px 0;text-align:right;">{payment_method_display}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#666;">Date &amp; Time</td>
        <td style="padding:6px 0;text-align:right;">{paid_at_str}</td>
      </tr>
    </table>

    <div style="margin-top:24px;">
      {_item_table_html(items, "Items Ordered")}
    </div>

    <table width="100%" cellpadding="0" cellspacing="0"
           style="font-size:14px;margin-top:16px;border-collapse:collapse;">
      <tr>
        <td style="padding:5px 0;color:#666;">Subtotal</td>
        <td style="padding:5px 0;text-align:right;">RM {subtotal:.2f}</td>
      </tr>
      <tr>
        <td style="padding:5px 0;color:#666;">Shipping Fee</td>
        <td style="padding:5px 0;text-align:right;">RM {shipping_cost:.2f}</td>
      </tr>
      <tr style="border-top:2px solid #333;">
        <td style="padding:10px 0;font-size:16px;font-weight:bold;">Total Paid</td>
        <td style="padding:10px 0;text-align:right;font-size:16px;font-weight:bold;">
          RM {total:.2f}
        </td>
      </tr>
    </table>

    <h3 style="font-size:15px;border-bottom:2px solid #eee;padding-bottom:8px;margin:24px 0 12px;">
      Delivery Address
    </h3>
    <p style="font-size:14px;line-height:1.7;margin:0;">{address_lines}</p>
  </div>

  {_footer_html(brand_name)}

</div>
"""
        send_mail.delay(
            to=to,
            subject=f"Your {brand_name} Receipt — {order_ref}",
            body_html=body_html,
        )

    @override
    def send_order_cancellation(
        self,
        to: str,
        full_name: str,
        order_id: str,
        items: list[PaymentReceiptItem],
        total: Decimal,
        cancelled_at: datetime,
    ) -> None:
        configs = get_configs()
        brand_name = configs.APP_NAME.capitalize()
        order_ref = construct_order_ref(order_id)
        cancelled_at_str = cancelled_at.strftime("%d %b %Y, %I:%M %p UTC")

        body_html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333;background:#fff;">

  {_header_html(brand_name)}

  <div style="background:{_CANCEL_BG};padding:24px;border-left:4px solid {_CANCEL_ACCENT};">
    <h2 style="color:{_CANCEL_ACCENT};margin:0 0 8px;">&#10007; Order Cancelled</h2>
    <p style="margin:0;font-size:15px;">Hi <strong>{full_name}</strong>,</p>
    <p style="margin:8px 0 0;font-size:14px;color:#555;">
      Your order <strong>{order_ref}</strong> has been cancelled on {cancelled_at_str}.
      If you did not request this cancellation, please contact our support team immediately.
    </p>
  </div>

  <div style="padding:24px;">
    {_item_table_html(items, "Cancelled Items")}
    {_total_row_html("Order Total", total)}

    <div style="margin-top:24px;padding:16px;background:#f9f9f9;border:1px solid #e0e0e0;
                border-radius:4px;font-size:13px;color:#666;line-height:1.6;">
      <strong style="color:#333;">Refund Information</strong><br>
      If payment was already processed for this order, a full refund of
      <strong>RM {total:.2f}</strong> will be credited to your original payment method
      within 3&ndash;5 business days. Processing times may vary depending on your bank or
      card issuer.
    </div>
  </div>

  {_footer_html(brand_name)}

</div>
"""
        send_mail.delay(
            to=to,
            subject=f"Your {brand_name} Order {order_ref} Has Been Cancelled",
            body_html=body_html,
        )

    @override
    def send_order_shipped(
        self,
        to: str,
        full_name: str,
        order_id: str,
        items: list[PaymentReceiptItem],
        total: Decimal,
        shipped_at: datetime,
    ) -> None:
        configs = get_configs()
        brand_name = configs.APP_NAME.capitalize()
        order_ref = construct_order_ref(order_id)
        shipped_at_str = shipped_at.strftime("%d %b %Y, %I:%M %p UTC")

        body_html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333;background:#fff;">

  {_header_html(brand_name)}

  <div style="background:{_SHIP_BG};padding:24px;border-left:4px solid {_SHIP_ACCENT};">
    <h2 style="color:{_SHIP_ACCENT};margin:0 0 8px;">&#128666; Order Shipped</h2>
    <p style="margin:0;font-size:15px;">Hi <strong>{full_name}</strong>,</p>
    <p style="margin:8px 0 0;font-size:14px;color:#555;">
      Great news! Your order <strong>{order_ref}</strong> was shipped on {shipped_at_str}
      and is now on its way to you.
    </p>
  </div>

  <div style="padding:24px;">
    {_item_table_html(items, "Shipped Items")}
    {_total_row_html("Order Total", total)}
  </div>

  {_footer_html(brand_name)}

</div>
"""
        send_mail.delay(
            to=to,
            subject=f"Your {brand_name} Order {order_ref} Has Been Shipped",
            body_html=body_html,
        )

    @override
    def send_order_delivered(
        self,
        to: str,
        full_name: str,
        order_id: str,
        items: list[PaymentReceiptItem],
        total: Decimal,
        delivered_at: datetime,
    ) -> None:
        configs = get_configs()
        brand_name = configs.APP_NAME.capitalize()
        order_ref = construct_order_ref(order_id)
        delivered_at_str = delivered_at.strftime("%d %b %Y, %I:%M %p UTC")

        body_html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333;background:#fff;">

  {_header_html(brand_name)}

  <div style="background:{_DELIVER_BG};padding:24px;border-left:4px solid {_DELIVER_ACCENT};">
    <h2 style="color:{_DELIVER_ACCENT};margin:0 0 8px;">&#10003; Order Delivered</h2>
    <p style="margin:0;font-size:15px;">Hi <strong>{full_name}</strong>,</p>
    <p style="margin:8px 0 0;font-size:14px;color:#555;">
      Your order <strong>{order_ref}</strong> was delivered on {delivered_at_str}.
      We hope you enjoy your books!
    </p>
  </div>

  <div style="padding:24px;">
    {_item_table_html(items, "Delivered Items")}
    {_total_row_html("Order Total", total)}
  </div>

  {_footer_html(brand_name)}

</div>
"""
        send_mail.delay(
            to=to,
            subject=f"Your {brand_name} Order {order_ref} Has Been Delivered",
            body_html=body_html,
        )
