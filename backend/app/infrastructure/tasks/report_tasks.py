from __future__ import annotations

import asyncio
import csv
import io
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from typing import cast as typing_cast

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import Date, cast, desc, extract, func, literal
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import OrderStatus, ReportFormat, ReportType
from app.infrastructure.db.models import (
    AuthorModel,
    BookAuthorModel,
    BookModel,
    CategoryModel,
    OrderItemModel,
    OrderModel,
    ReportJobModel,
)
from app.infrastructure.db.repositories.report_job_repository_impl import (
    ReportJobRepositoryImpl,
)
from app.infrastructure.storage.minio_storage import MinIOStorage
from app.infrastructure.tasks.celery_app import celery_app
from app.infrastructure.tasks.task_db import task_db_session

_QUALIFYING_STATUSES = [
    OrderStatus.PAID,
    OrderStatus.SHIPPED,
    OrderStatus.DELIVERED,
]
_DEFAULT_LIMIT: int = 20

_BRAND_DARK = colors.HexColor("#1a1a2e")
_HEADER_TEXT_COLOR = colors.white
_ROW_ALT_COLOR = colors.HexColor("#f5f5f5")


# internal data structures
@dataclass
class SalesSummaryData:
    total_revenue: Decimal
    total_orders: int
    average_order_value: Decimal
    total_units_sold: int
    total_unique_customers: int


@dataclass
class TopBooksRow:
    rank: int
    book_id: str
    title: str
    isbn: str
    author_names: str
    category_name: str
    units_sold: int
    revenue: Decimal


@dataclass
class TopAuthorsRow:
    rank: int
    author_id: str
    author_name: str
    total_units_sold: int
    total_revenue: Decimal
    titles_sold: int


@dataclass
class MonthlyVolumeRow:
    year_month: str
    order_count: int
    revenue: Decimal
    units_sold: int


ReportData = (
    SalesSummaryData | list[TopBooksRow] | list[TopAuthorsRow] | list[MonthlyVolumeRow]
)


# query helpers
async def _query_sales_summary(
    session: AsyncSession, job: ReportJobModel
) -> SalesSummaryData:
    from sqlalchemy import select

    stmt = (
        select(
            func.coalesce(func.sum(OrderItemModel.line_total), Decimal("0")).label(
                "total_revenue"
            ),
            func.count(OrderModel.id.distinct()).label("total_orders"),
            func.coalesce(func.sum(OrderItemModel.quantity), 0).label(
                "total_units_sold"
            ),
            func.count(OrderModel.user_id.distinct()).label("total_unique_customers"),
        )
        .join(OrderItemModel, OrderItemModel.order_id == OrderModel.id)
        .where(
            OrderModel.status.in_(_QUALIFYING_STATUSES),
            cast(OrderModel.created_at, Date) >= job.date_from,
            cast(OrderModel.created_at, Date) <= job.date_to,
        )
    )
    row = (await session.execute(stmt)).one()
    total_revenue = Decimal(str(row.total_revenue))
    total_orders = int(row.total_orders)
    avg = total_revenue / total_orders if total_orders > 0 else Decimal("0")
    return SalesSummaryData(
        total_revenue=total_revenue,
        total_orders=total_orders,
        # round to 2 decimal places
        average_order_value=avg.quantize(Decimal("0.01")),
        total_units_sold=int(row.total_units_sold),
        total_unique_customers=int(row.total_unique_customers),
    )


async def _query_top_books(
    session: AsyncSession, job: ReportJobModel
) -> list[TopBooksRow]:
    from sqlalchemy import select

    effective_limit = job.limit if job.limit is not None else _DEFAULT_LIMIT

    stmt = (
        select(
            OrderItemModel.book_id,
            BookModel.title,
            BookModel.isbn,
            func.sum(OrderItemModel.quantity).label("units_sold"),
            func.sum(OrderItemModel.quantity * OrderItemModel.unit_price).label(
                "revenue"
            ),
        )
        .join(OrderModel, OrderModel.id == OrderItemModel.order_id)
        .join(BookModel, BookModel.id == OrderItemModel.book_id)
        .where(
            OrderModel.status.in_(_QUALIFYING_STATUSES),
            cast(OrderModel.created_at, Date) >= job.date_from,
            cast(OrderModel.created_at, Date) <= job.date_to,
        )
        .group_by(OrderItemModel.book_id, BookModel.title, BookModel.isbn)
        .order_by(desc("units_sold"))
        .limit(effective_limit)
    )
    book_rows = (await session.execute(stmt)).all()

    if not book_rows:
        return []

    book_ids = [r.book_id for r in book_rows]

    # Fetch comma-joined author names per book
    author_stmt = (
        select(
            BookAuthorModel.book_id,
            func.string_agg(AuthorModel.name, literal(", ")).label("author_names"),
        )
        .join(AuthorModel, AuthorModel.id == BookAuthorModel.author_id)
        .where(BookAuthorModel.book_id.in_(book_ids))
        .group_by(BookAuthorModel.book_id)
    )
    author_map: dict[str, str] = {
        r.book_id: r.author_names for r in (await session.execute(author_stmt)).all()
    }

    # Fetch category names per book
    cat_stmt = (
        select(BookModel.id.label("book_id"), CategoryModel.name.label("category_name"))
        .join(CategoryModel, CategoryModel.id == BookModel.category_id)
        .where(BookModel.id.in_(book_ids))
    )
    cat_map: dict[str, str] = {
        r.book_id: r.category_name for r in (await session.execute(cat_stmt)).all()
    }

    return [
        TopBooksRow(
            rank=idx + 1,
            book_id=r.book_id,
            title=r.title or "",
            isbn=r.isbn or "",
            author_names=author_map.get(r.book_id, ""),
            category_name=cat_map.get(r.book_id, ""),
            units_sold=int(r.units_sold),
            revenue=Decimal(str(r.revenue)),
        )
        for idx, r in enumerate(book_rows)
    ]


async def _query_top_authors(
    session: AsyncSession, job: ReportJobModel
) -> list[TopAuthorsRow]:
    from sqlalchemy import select

    effective_limit = job.limit if job.limit is not None else _DEFAULT_LIMIT

    stmt = (
        select(
            AuthorModel.id.label("author_id"),
            AuthorModel.name.label("author_name"),
            func.sum(OrderItemModel.quantity).label("total_units_sold"),
            func.sum(OrderItemModel.quantity * OrderItemModel.unit_price).label(
                "total_revenue"
            ),
            func.count(OrderItemModel.book_id.distinct()).label("titles_sold"),
        )
        .join(BookAuthorModel, BookAuthorModel.book_id == OrderItemModel.book_id)
        .join(AuthorModel, AuthorModel.id == BookAuthorModel.author_id)
        .join(OrderModel, OrderModel.id == OrderItemModel.order_id)
        .where(
            OrderModel.status.in_(_QUALIFYING_STATUSES),
            cast(OrderModel.created_at, Date) >= job.date_from,
            cast(OrderModel.created_at, Date) <= job.date_to,
        )
        .group_by(AuthorModel.id, AuthorModel.name)
        .order_by(desc("total_units_sold"))
        .limit(effective_limit)
    )
    rows = (await session.execute(stmt)).all()

    return [
        TopAuthorsRow(
            rank=idx + 1,
            author_id=r.author_id,
            author_name=r.author_name or "",
            total_units_sold=int(r.total_units_sold),
            total_revenue=Decimal(str(r.total_revenue)),
            titles_sold=int(r.titles_sold),
        )
        for idx, r in enumerate(rows)
    ]


def _generate_month_series(date_from: date, date_to: date) -> list[str]:
    months: list[str] = []
    year, month = date_from.year, date_from.month
    end_year, end_month = date_to.year, date_to.month
    while (year, month) <= (end_year, end_month):
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


async def _query_monthly_volume(
    session: AsyncSession, job: ReportJobModel
) -> list[MonthlyVolumeRow]:
    from sqlalchemy import select

    stmt = (
        select(
            extract("year", OrderModel.created_at).label("year"),
            extract("month", OrderModel.created_at).label("month"),
            func.count(OrderModel.id.distinct()).label("order_count"),
            func.sum(OrderItemModel.line_total).label("revenue"),
            func.sum(OrderItemModel.quantity).label("units_sold"),
        )
        .join(OrderItemModel, OrderItemModel.order_id == OrderModel.id)
        .where(
            OrderModel.status.in_(_QUALIFYING_STATUSES),
            cast(OrderModel.created_at, Date) >= job.date_from,
            cast(OrderModel.created_at, Date) <= job.date_to,
        )
        .group_by("year", "month")
        .order_by("year", "month")
    )
    db_rows = {
        f"{int(r.year):04d}-{int(r.month):02d}": r
        for r in (await session.execute(stmt)).all()
    }

    return [
        MonthlyVolumeRow(
            year_month=ym,
            order_count=int(db_rows[ym].order_count) if ym in db_rows else 0,
            revenue=Decimal(str(db_rows[ym].revenue))
            if ym in db_rows
            else Decimal("0"),
            units_sold=int(db_rows[ym].units_sold) if ym in db_rows else 0,
        )
        for ym in _generate_month_series(job.date_from, job.date_to)
    ]


async def _query_report_data(session: AsyncSession, job: ReportJobModel) -> ReportData:
    match job.report_type:
        case ReportType.SALES_SUMMARY:
            return await _query_sales_summary(session, job)
        case ReportType.TOP_BOOKS:
            return await _query_top_books(session, job)
        case ReportType.TOP_AUTHORS:
            return await _query_top_authors(session, job)
        case ReportType.MONTHLY_VOLUME:
            return await _query_monthly_volume(session, job)


# CSV rendering
def _render_csv(job: ReportJobModel, data: ReportData) -> bytes:
    buf = io.StringIO()

    if isinstance(data, SalesSummaryData):
        writer = csv.DictWriter(
            buf,
            fieldnames=["metric", "value"],
            lineterminator="\r\n",
        )
        writer.writeheader()
        writer.writerow(
            {"metric": "Total Revenue", "value": f"{data.total_revenue:.2f}"}
        )
        writer.writerow({"metric": "Total Orders", "value": str(data.total_orders)})
        writer.writerow(
            {
                "metric": "Average Order Value",
                "value": f"{data.average_order_value:.2f}",
            }
        )
        writer.writerow(
            {"metric": "Total Units Sold", "value": str(data.total_units_sold)}
        )
        writer.writerow(
            {
                "metric": "Total Unique Customers",
                "value": str(data.total_unique_customers),
            }
        )

    elif isinstance(data, list) and (not data or isinstance(data[0], TopBooksRow)):
        fieldnames = [
            "rank",
            "title",
            "isbn",
            "author_names",
            "category_name",
            "units_sold",
            "revenue",
        ]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\r\n")
        writer.writeheader()
        for row in data:
            assert isinstance(row, TopBooksRow)
            writer.writerow(
                {
                    "rank": row.rank,
                    "title": row.title,
                    "isbn": row.isbn,
                    "author_names": row.author_names,
                    "category_name": row.category_name,
                    "units_sold": row.units_sold,
                    "revenue": f"{row.revenue:.2f}",
                }
            )

    elif isinstance(data, list) and (not data or isinstance(data[0], TopAuthorsRow)):
        fieldnames = [
            "rank",
            "author_name",
            "total_units_sold",
            "total_revenue",
            "titles_sold",
        ]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\r\n")
        writer.writeheader()
        for row in data:
            assert isinstance(row, TopAuthorsRow)
            writer.writerow(
                {
                    "rank": row.rank,
                    "author_name": row.author_name,
                    "total_units_sold": row.total_units_sold,
                    "total_revenue": f"{row.total_revenue:.2f}",
                    "titles_sold": row.titles_sold,
                }
            )

    else:
        monthly_rows = typing_cast(list[MonthlyVolumeRow], data)
        fieldnames = ["year_month", "order_count", "revenue", "units_sold"]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\r\n")
        writer.writeheader()
        for row in monthly_rows:
            writer.writerow(
                {
                    "year_month": row.year_month,
                    "order_count": row.order_count,
                    "revenue": f"{row.revenue:.2f}",
                    "units_sold": row.units_sold,
                }
            )

    return buf.getvalue().encode("utf-8-sig")


# PDF rendering
_TABLE_HEADER_CMDS: list[tuple[Any, ...]] = [
    ("BACKGROUND", (0, 0), (-1, 0), _BRAND_DARK),
    ("TEXTCOLOR", (0, 0), (-1, 0), _HEADER_TEXT_COLOR),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 9),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
    ("TOPPADDING", (0, 0), (-1, 0), 8),
    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 1), (-1, -1), 8),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ROW_ALT_COLOR]),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
    ("TOPPADDING", (0, 1), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("WORDWRAP", (0, 0), (-1, -1), True),
]
_TABLE_HEADER_STYLE = TableStyle(_TABLE_HEADER_CMDS)


class _NumberedCanvas(rl_canvas.Canvas):
    """Two-pass canvas that renders 'Page X of Y' in the footer."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()  # type: ignore[attr-defined] # pyright: ignore[reportAttributeAccessIssue]

    def save(self) -> None:
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_footer(total_pages)
            rl_canvas.Canvas.showPage(self)
        rl_canvas.Canvas.save(self)

    def _draw_page_footer(self, total_pages: int) -> None:
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#888888"))
        self.drawRightString(
            A4[0] - 2 * cm,
            1.2 * cm,
            f"Page {self._pageNumber} of {total_pages}",  # type: ignore[attr-defined] # pyright: ignore[reportAttributeAccessIssue]
        )


def _draw_page_header(
    canvas: Any,
    doc: Any,
    title: str,
    date_from: date,
    date_to: date,
    generated_at: str,
) -> None:
    canvas.saveState()
    page_width = A4[0]
    header_top = A4[1] - 1.5 * cm
    header_height = 1.8 * cm
    canvas.setFillColor(_BRAND_DARK)
    canvas.rect(
        1.5 * cm,
        header_top - header_height,
        page_width - 3 * cm,
        header_height,
        fill=1,
        stroke=0,
    )
    canvas.setFillColor(_HEADER_TEXT_COLOR)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(2 * cm, header_top - 1 * cm, "BUKOO")
    canvas.setFont("Helvetica", 10)
    canvas.drawString(2 * cm, header_top - 1.45 * cm, title)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#aaaaaa"))
    period_text = f"Period: {date_from}  to  {date_to}   |   Generated: {generated_at}"
    canvas.drawRightString(page_width - 2 * cm, header_top - 1.45 * cm, period_text)
    canvas.restoreState()


def _report_title(report_type: ReportType) -> str:
    return {
        ReportType.SALES_SUMMARY: "Sales Summary Report",
        ReportType.TOP_BOOKS: "Top Books Report",
        ReportType.TOP_AUTHORS: "Top Authors Report",
        ReportType.MONTHLY_VOLUME: "Monthly Volume Report",
    }[report_type]


def _render_pdf(job: ReportJobModel, data: ReportData) -> bytes:
    buf = io.BytesIO()
    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle(
        "cell",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        wordWrap="CJK",
    )
    no_data_style = ParagraphStyle(
        "nodata",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#666666"),
        spaceAfter=12,
    )
    title = _report_title(job.report_type)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    def _on_page(canvas: Any, doc: Any) -> None:
        _draw_page_header(canvas, doc, title, job.date_from, job.date_to, generated_at)

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=4.2 * cm,
        bottomMargin=2.5 * cm,
    )

    story: list[Any] = []

    if isinstance(data, SalesSummaryData):
        # Render as a 2-column KV table (no "no data" case — aggregates always exist)
        table_data = [
            ["Metric", "Value"],
            ["Total Revenue", f"RM {data.total_revenue:,.2f}"],
            ["Total Orders", f"{data.total_orders:,}"],
            ["Average Order Value", f"RM {data.average_order_value:,.2f}"],
            ["Total Units Sold", f"{data.total_units_sold:,}"],
            ["Total Unique Customers", f"{data.total_unique_customers:,}"],
        ]
        page_width = A4[0] - 3 * cm
        table = Table(
            table_data, colWidths=[page_width * 0.55, page_width * 0.45], repeatRows=1
        )
        table.setStyle(_TABLE_HEADER_STYLE)
        story.append(table)

    elif isinstance(data, list) and (not data or isinstance(data[0], TopBooksRow)):
        if not data:
            story.append(
                Paragraph("No data available for the selected period.", no_data_style)
            )
        else:
            headers = [
                "#",
                "Title",
                "ISBN",
                "Authors",
                "Category",
                "Units Sold",
                "Revenue",
            ]
            page_width = A4[0] - 3 * cm
            col_widths = [
                page_width * 0.04,
                page_width * 0.22,
                page_width * 0.12,
                page_width * 0.22,
                page_width * 0.14,
                page_width * 0.12,
                page_width * 0.14,
            ]
            rows: list[list[Any]] = [headers]
            for row in data:
                assert isinstance(row, TopBooksRow)
                rows.append(
                    [
                        str(row.rank),
                        Paragraph(row.title, cell_style),
                        row.isbn,
                        Paragraph(row.author_names, cell_style),
                        Paragraph(row.category_name, cell_style),
                        f"{row.units_sold:,}",
                        f"RM {row.revenue:,.2f}",
                    ]
                )
            style = TableStyle(
                [*_TABLE_HEADER_CMDS]
                + [
                    ("ALIGN", (5, 1), (-1, -1), "RIGHT"),
                ]
            )
            table = Table(rows, colWidths=col_widths, repeatRows=1)
            table.setStyle(style)
            story.append(table)

    elif isinstance(data, list) and (not data or isinstance(data[0], TopAuthorsRow)):
        if not data:
            story.append(
                Paragraph("No data available for the selected period.", no_data_style)
            )
        else:
            headers = ["#", "Author Name", "Units Sold", "Revenue", "Titles Sold"]
            page_width = A4[0] - 3 * cm
            col_widths = [
                page_width * 0.05,
                page_width * 0.40,
                page_width * 0.18,
                page_width * 0.20,
                page_width * 0.17,
            ]
            rows = [headers]
            for row in data:
                assert isinstance(row, TopAuthorsRow)
                rows.append(
                    [
                        str(row.rank),
                        Paragraph(row.author_name, cell_style),
                        f"{row.total_units_sold:,}",
                        f"RM {row.total_revenue:,.2f}",
                        f"{row.titles_sold:,}",
                    ]
                )
            style = TableStyle(
                [*_TABLE_HEADER_CMDS]
                + [
                    ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ]
            )
            table = Table(rows, colWidths=col_widths, repeatRows=1)
            table.setStyle(style)
            story.append(table)

    else:
        # MonthlyVolumeRow
        monthly_data = typing_cast(list[MonthlyVolumeRow], data)
        if not monthly_data or not isinstance(monthly_data[0], MonthlyVolumeRow):
            story.append(
                Paragraph("No data available for the selected period.", no_data_style)
            )
        else:
            headers = ["Month", "Orders", "Revenue", "Units Sold"]
            page_width = A4[0] - 3 * cm
            col_widths = [
                page_width * 0.25,
                page_width * 0.20,
                page_width * 0.30,
                page_width * 0.25,
            ]
            rows = [headers]
            for row in monthly_data:
                rows.append(
                    [
                        row.year_month,
                        f"{row.order_count:,}",
                        f"RM {row.revenue:,.2f}",
                        f"{row.units_sold:,}",
                    ]
                )
            style = TableStyle(
                [*_TABLE_HEADER_CMDS]
                + [
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ]
            )
            table = Table(rows, colWidths=col_widths, repeatRows=1)
            table.setStyle(style)
            story.append(table)

    story.append(Spacer(1, 0.5 * cm))
    doc.build(
        story, onFirstPage=_on_page, onLaterPages=_on_page, canvasmaker=_NumberedCanvas
    )
    return buf.getvalue()


# celery task
def _render_file(job: ReportJobModel, data: ReportData) -> bytes:
    if job.report_format == ReportFormat.CSV:
        return _render_csv(job, data)
    return _render_pdf(job, data)


def _content_type(report_format: ReportFormat) -> str:
    if report_format == ReportFormat.CSV:
        return "text/csv"
    return "application/pdf"


async def _run(job_id: str) -> None:
    async with task_db_session() as session:
        repo = ReportJobRepositoryImpl(session)

        job = await repo.find_by_id(job_id)
        if job is None:
            return

        # Load the ORM model directly for use in queries (task is infra layer)
        from sqlalchemy import select

        model_stmt = select(ReportJobModel).where(ReportJobModel.id == job_id)
        model_result = await session.execute(model_stmt)
        orm_job = model_result.scalar_one_or_none()
        if orm_job is None:
            return

        job.mark_processing()
        await repo.save(job)
        await session.commit()

        try:
            data = await _query_report_data(session, orm_job)
            file_bytes = _render_file(orm_job, data)
            key = f"pub/reports/{orm_job.report_format}/{orm_job.id}.{orm_job.report_format}"
            await MinIOStorage().upload(
                key, file_bytes, _content_type(orm_job.report_format)
            )

            job.mark_completed(file_key=key)
            await repo.save(job)
            await session.commit()

        except Exception as exc:
            job.mark_failed(error_message=str(exc))
            await repo.save(job)
            await session.commit()
            # re-raise so Celery marks task as FAILURE
            raise


@celery_app.task(name="report.generate_report", queue="default")
def generate_report(job_id: str) -> None:
    asyncio.run(_run(job_id))
