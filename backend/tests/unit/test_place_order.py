from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.order_dto import (
    BaseOrderItemResult,
    PlaceOrderCommand,
    PlaceOrderResult,
)
from app.application.use_cases.order.place_order import PlaceOrderUseCase
from app.domain.entities.address_entity import AddressEntity
from app.domain.entities.book_entity import BookEntity
from app.domain.entities.cart_entity import CartEntity
from app.domain.entities.cart_item_entity import CartItemEntity
from app.domain.entities.order_entity import OrderEntity
from app.domain.exceptions import (
    AddressNotFoundError,
    BookNotFoundError,
    CartItemNotFoundError,
    CartNotFoundError,
    OutOfStockError,
)
from app.domain.repositories import IBookRepository, ICartRepository, IOrderRepository
from app.domain.repositories.address_repository import IAddressRepository
from app.domain.repositories.book_repository import BookStatusFilter

# ---------------------------------------------------------------------------
# Entity factories
# ---------------------------------------------------------------------------


def _make_book(
    book_id: str = "book-001",
    title: str = "Test Book",
    price: Decimal = Decimal("29.99"),
    stock_quantity: int = 10,
) -> BookEntity:
    now = datetime.now(UTC)
    return BookEntity(
        _id=book_id,
        _title=title,
        _price=price,
        _stock_quantity=stock_quantity,
        _language="English",
        _publisher_id=None,
        _category_id=None,
        _isbn=None,
        _description=None,
        _cover_url=None,
        _page_count=None,
        _published_date=None,
        _deactivated_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_cart_item(
    item_id: str = "item-001",
    cart_id: str = "cart-001",
    book_id: str = "book-001",
    quantity: int = 2,
) -> CartItemEntity:
    now = datetime.now(UTC)
    return CartItemEntity(
        _id=item_id,
        _cart_id=cart_id,
        _book_id=book_id,
        _quantity=quantity,
        _created_at=now,
        _updated_at=now,
    )


def _make_cart(
    user_id: str = "user-001",
    items: list[CartItemEntity] | None = None,
) -> CartEntity:
    now = datetime.now(UTC)
    return CartEntity(
        _id="cart-001",
        _user_id=user_id,
        _created_at=now,
        _updated_at=now,
        _cart_items=items or [],
    )


def _make_address(user_id: str = "user-001", state: str = "Selangor") -> AddressEntity:
    now = datetime.now(UTC)
    return AddressEntity(
        _id="address-001",
        _user_id=user_id,
        _recipient_name="John Doe",
        _phone="+60123456789",
        _address_line1="No. 1, Jalan Test",
        _address_line2=None,
        _city="Kuala Lumpur",
        _state=state,
        _postcode="50450",
        _country="Malaysia",
        _created_at=now,
        _updated_at=now,
    )


# ---------------------------------------------------------------------------
# Fake repositories
# ---------------------------------------------------------------------------


class FakeCartRepository(ICartRepository):
    def __init__(self, cart: CartEntity | None = None) -> None:
        self._cart = cart
        self.deleted_item_ids: list[str] = []

    async def find_by_user_id(self, user_id: str) -> CartEntity | None:
        if self._cart and self._cart.user_id == user_id:
            return self._cart
        return None

    async def delete_item_by_item_id(self, item_id: str) -> None:
        self.deleted_item_ids.append(item_id)

    async def delete_items_by_cart_id(self, cart_id: str) -> None:
        pass

    async def save(self, cart: CartEntity) -> None:
        pass


class FakeAddressRepository(IAddressRepository):
    def __init__(self, address: AddressEntity | None = None) -> None:
        self._address = address

    async def save(self, address: AddressEntity) -> None:
        pass

    async def find_address_by_user_id(self, user_id: str) -> AddressEntity | None:
        if self._address and self._address.user_id == user_id:
            return self._address
        return None


class FakeBookRepository(IBookRepository):
    def __init__(self, books: dict[str, BookEntity] | None = None) -> None:
        self._books = books or {}
        self.saved_books: list[BookEntity] = []

    async def find_by_id(
        self, book_id: str, filters: BookStatusFilter
    ) -> BookEntity | None:
        return self._books.get(book_id)

    async def find_all(self, query: object, filters: object) -> object:  # type: ignore[override]
        raise NotImplementedError

    async def find_by_isbn(self, isbn: str) -> BookEntity | None:
        raise NotImplementedError

    async def save(
        self, book: BookEntity, should_skip_book_authors: bool = True
    ) -> None:
        self.saved_books.append(book)


class FakeOrderRepository(IOrderRepository):
    def __init__(self) -> None:
        self.saved_order: OrderEntity | None = None

    async def find_by_id(self, order_id: str) -> OrderEntity | None:
        pass

    async def save(self, order: OrderEntity, should_skip_items: bool = True) -> None:
        self.saved_order = order

    async def find_all(self, *args: Any, **kwargs: Any) -> Any:
        return []


# ---------------------------------------------------------------------------
# Use case factory
# ---------------------------------------------------------------------------


def _make_use_case(
    cart: CartEntity | None = None,
    address: AddressEntity | None = None,
    books: dict[str, BookEntity] | None = None,
    db_session: AsyncMock | None = None,
) -> tuple[
    PlaceOrderUseCase,
    FakeCartRepository,
    FakeAddressRepository,
    FakeBookRepository,
    FakeOrderRepository,
]:
    cart_repo = FakeCartRepository(cart=cart)
    address_repo = FakeAddressRepository(address=address)
    book_repo = FakeBookRepository(books=books)
    order_repo = FakeOrderRepository()
    use_case = PlaceOrderUseCase(
        db_session=db_session or AsyncMock(),
        cart_repo=cart_repo,
        book_repo=book_repo,
        address_repo=address_repo,
        order_repo=order_repo,
    )
    return use_case, cart_repo, address_repo, book_repo, order_repo


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPlaceOrderUseCase:
    # --- Happy path ---

    async def test_returns_result_with_pending_status_and_user_id(self) -> None:
        book = _make_book()
        item = _make_cart_item()
        cart = _make_cart(items=[item])
        address = _make_address()
        use_case, _, _, _, order_repo = _make_use_case(
            cart=cart, address=address, books={"book-001": book}
        )
        cmd = PlaceOrderCommand(user_id="user-001", cart_item_ids=["item-001"])

        result = await use_case.execute(cmd)

        assert isinstance(result, PlaceOrderResult)
        assert result.status.value == "pending"
        assert order_repo.saved_order is not None
        assert order_repo.saved_order.user_id == "user-001"

    async def test_shipping_cost_is_5_for_peninsular_malaysia(self) -> None:
        book = _make_book()
        item = _make_cart_item()
        cart = _make_cart(items=[item])
        address = _make_address(state="Selangor")
        use_case, *_ = _make_use_case(
            cart=cart, address=address, books={"book-001": book}
        )
        cmd = PlaceOrderCommand(user_id="user-001", cart_item_ids=["item-001"])

        result = await use_case.execute(cmd)

        assert result.shipping_cost == Decimal("5.00")

    async def test_shipping_cost_is_10_for_sabah(self) -> None:
        book = _make_book()
        item = _make_cart_item()
        cart = _make_cart(items=[item])
        address = _make_address(state="Sabah")
        use_case, *_ = _make_use_case(
            cart=cart, address=address, books={"book-001": book}
        )
        cmd = PlaceOrderCommand(user_id="user-001", cart_item_ids=["item-001"])

        result = await use_case.execute(cmd)

        assert result.shipping_cost == Decimal("10.00")

    async def test_shipping_cost_is_10_for_sarawak(self) -> None:
        book = _make_book()
        item = _make_cart_item()
        cart = _make_cart(items=[item])
        address = _make_address(state="Sarawak")
        use_case, *_ = _make_use_case(
            cart=cart, address=address, books={"book-001": book}
        )
        cmd = PlaceOrderCommand(user_id="user-001", cart_item_ids=["item-001"])

        result = await use_case.execute(cmd)

        assert result.shipping_cost == Decimal("10.00")

    async def test_shipping_cost_is_case_insensitive_for_east_malaysia_states(
        self,
    ) -> None:
        book = _make_book()
        item = _make_cart_item()
        cart = _make_cart(items=[item])
        use_case_lower, *_ = _make_use_case(
            cart=cart,
            address=_make_address(state="sabah"),
            books={"book-001": book},
        )
        use_case_upper, *_ = _make_use_case(
            cart=_make_cart(items=[_make_cart_item()]),
            address=_make_address(state="SARAWAK"),
            books={"book-001": book},
        )
        cmd = PlaceOrderCommand(user_id="user-001", cart_item_ids=["item-001"])

        result_lower = await use_case_lower.execute(cmd)
        result_upper = await use_case_upper.execute(cmd)

        assert result_lower.shipping_cost == Decimal("10.00")
        assert result_upper.shipping_cost == Decimal("10.00")

    async def test_total_equals_subtotal_plus_shipping_cost(self) -> None:
        book_a = _make_book(book_id="book-001", price=Decimal("29.99"))
        book_b = _make_book(book_id="book-002", price=Decimal("19.99"))
        item_a = _make_cart_item(item_id="item-001", book_id="book-001", quantity=2)
        item_b = _make_cart_item(item_id="item-002", book_id="book-002", quantity=1)
        cart = _make_cart(items=[item_a, item_b])
        address = _make_address(state="Selangor")
        use_case, *_ = _make_use_case(
            cart=cart,
            address=address,
            books={"book-001": book_a, "book-002": book_b},
        )
        cmd = PlaceOrderCommand(
            user_id="user-001", cart_item_ids=["item-001", "item-002"]
        )

        result = await use_case.execute(cmd)

        expected_subtotal = Decimal("29.99") * 2 + Decimal("19.99") * 1
        expected_total = expected_subtotal + Decimal("5.00")
        assert result.subtotal == expected_subtotal
        assert result.total == expected_total

    async def test_items_carry_book_title_and_price_snapshots(self) -> None:
        book = _make_book(title="The Great Gatsby", price=Decimal("54.97"))
        item = _make_cart_item(quantity=2)
        cart = _make_cart(items=[item])
        address = _make_address()
        use_case, *_ = _make_use_case(
            cart=cart, address=address, books={"book-001": book}
        )
        cmd = PlaceOrderCommand(user_id="user-001", cart_item_ids=["item-001"])

        result = await use_case.execute(cmd)

        assert len(result.items) == 1
        order_item = result.items[0]
        assert isinstance(order_item, BaseOrderItemResult)
        assert order_item.book_title == "The Great Gatsby"
        assert order_item.unit_price == Decimal("54.97")
        assert order_item.quantity == 2
        assert order_item.line_total == Decimal("109.94")

    async def test_partial_selection_only_selected_items_in_result(self) -> None:
        book_a = _make_book(book_id="book-001")
        book_b = _make_book(book_id="book-002")
        book_c = _make_book(book_id="book-003")
        item_a = _make_cart_item(item_id="item-001", book_id="book-001")
        item_b = _make_cart_item(item_id="item-002", book_id="book-002")
        item_c = _make_cart_item(item_id="item-003", book_id="book-003")
        cart = _make_cart(items=[item_a, item_b, item_c])
        address = _make_address()
        use_case, *_ = _make_use_case(
            cart=cart,
            address=address,
            books={"book-001": book_a, "book-002": book_b, "book-003": book_c},
        )
        cmd = PlaceOrderCommand(
            user_id="user-001", cart_item_ids=["item-001", "item-003"]
        )

        result = await use_case.execute(cmd)

        assert len(result.items) == 2
        result_book_ids = {i.book_id for i in result.items}
        assert result_book_ids == {"book-001", "book-003"}

    async def test_only_selected_cart_items_are_deleted(self) -> None:
        book_a = _make_book(book_id="book-001")
        book_b = _make_book(book_id="book-002")
        book_c = _make_book(book_id="book-003")
        item_a = _make_cart_item(item_id="item-001", book_id="book-001")
        item_b = _make_cart_item(item_id="item-002", book_id="book-002")
        item_c = _make_cart_item(item_id="item-003", book_id="book-003")
        cart = _make_cart(items=[item_a, item_b, item_c])
        address = _make_address()
        use_case, cart_repo, *_ = _make_use_case(
            cart=cart,
            address=address,
            books={"book-001": book_a, "book-002": book_b, "book-003": book_c},
        )
        cmd = PlaceOrderCommand(
            user_id="user-001", cart_item_ids=["item-001", "item-003"]
        )

        await use_case.execute(cmd)

        assert sorted(cart_repo.deleted_item_ids) == ["item-001", "item-003"]
        assert "item-002" not in cart_repo.deleted_item_ids

    async def test_book_stock_is_decremented_for_each_selected_item(self) -> None:
        book = _make_book(stock_quantity=10)
        item = _make_cart_item(quantity=3)
        cart = _make_cart(items=[item])
        address = _make_address()
        use_case, _, _, book_repo, _ = _make_use_case(
            cart=cart, address=address, books={"book-001": book}
        )
        cmd = PlaceOrderCommand(user_id="user-001", cart_item_ids=["item-001"])

        await use_case.execute(cmd)

        assert len(book_repo.saved_books) == 1
        assert book_repo.saved_books[0].stock_quantity == 7

    async def test_address_snapshot_matches_to_snapshot_output(self) -> None:
        book = _make_book()
        item = _make_cart_item()
        cart = _make_cart(items=[item])
        address = _make_address(state="Penang")
        use_case, *_ = _make_use_case(
            cart=cart, address=address, books={"book-001": book}
        )
        cmd = PlaceOrderCommand(user_id="user-001", cart_item_ids=["item-001"])

        result = await use_case.execute(cmd)

        assert result.address_snapshot == address.to_snapshot()

    async def test_commit_called_exactly_once(self) -> None:
        book = _make_book()
        item = _make_cart_item()
        cart = _make_cart(items=[item])
        address = _make_address()
        db_session = AsyncMock()
        use_case, *_ = _make_use_case(
            cart=cart, address=address, books={"book-001": book}, db_session=db_session
        )
        cmd = PlaceOrderCommand(user_id="user-001", cart_item_ids=["item-001"])

        await use_case.execute(cmd)

        db_session.commit.assert_called_once()

    # --- Error cases ---

    async def test_raises_cart_not_found_when_user_has_no_cart(self) -> None:
        use_case, *_ = _make_use_case(cart=None)
        cmd = PlaceOrderCommand(user_id="user-001", cart_item_ids=["item-001"])

        with pytest.raises(CartNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_cart_item_not_found_when_id_not_in_cart(self) -> None:
        cart = _make_cart(items=[])
        use_case, *_ = _make_use_case(cart=cart)
        cmd = PlaceOrderCommand(user_id="user-001", cart_item_ids=["nonexistent-id"])

        with pytest.raises(CartItemNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_address_not_found_when_user_has_no_address(self) -> None:
        book = _make_book()
        item = _make_cart_item()
        cart = _make_cart(items=[item])
        use_case, *_ = _make_use_case(cart=cart, address=None, books={"book-001": book})
        cmd = PlaceOrderCommand(user_id="user-001", cart_item_ids=["item-001"])

        with pytest.raises(AddressNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_book_not_found_when_book_not_in_catalogue(self) -> None:
        item = _make_cart_item(book_id="book-001")
        cart = _make_cart(items=[item])
        address = _make_address()
        use_case, *_ = _make_use_case(cart=cart, address=address, books={})
        cmd = PlaceOrderCommand(user_id="user-001", cart_item_ids=["item-001"])

        with pytest.raises(BookNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_out_of_stock_when_quantity_exceeds_stock(self) -> None:
        book = _make_book(stock_quantity=1)
        item = _make_cart_item(quantity=5)
        cart = _make_cart(items=[item])
        address = _make_address()
        use_case, *_ = _make_use_case(
            cart=cart, address=address, books={"book-001": book}
        )
        cmd = PlaceOrderCommand(user_id="user-001", cart_item_ids=["item-001"])

        with pytest.raises(OutOfStockError):
            await use_case.execute(cmd)

    # --- Edge cases ---

    async def test_no_mutations_when_second_item_fails_stock_check(self) -> None:
        book_a = _make_book(book_id="book-001", stock_quantity=10)
        book_b = _make_book(book_id="book-002", stock_quantity=0)
        item_a = _make_cart_item(item_id="item-001", book_id="book-001", quantity=1)
        item_b = _make_cart_item(item_id="item-002", book_id="book-002", quantity=1)
        cart = _make_cart(items=[item_a, item_b])
        address = _make_address()
        use_case, cart_repo, _, book_repo, order_repo = _make_use_case(
            cart=cart,
            address=address,
            books={"book-001": book_a, "book-002": book_b},
        )
        cmd = PlaceOrderCommand(
            user_id="user-001", cart_item_ids=["item-001", "item-002"]
        )

        with pytest.raises(OutOfStockError):
            await use_case.execute(cmd)

        assert book_repo.saved_books == []
        assert cart_repo.deleted_item_ids == []
        assert order_repo.saved_order is None
