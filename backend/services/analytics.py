import calendar
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import case, cast, Date, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.invoice import Invoice, InvoiceItem, InvoiceStatus, Customer, Payment
from models.products import Product
from models.user import Business


async def _get_authorized_business(
    db: AsyncSession, current_user_id: int, business_id: int
) -> Business:
    result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = result.scalar_one_or_none()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    if business.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this business",
        )
    return business


async def total_revenue(
    db: AsyncSession,
    current_user_id: int,
    business_id: int,
) -> dict:
    await _get_authorized_business(db, current_user_id, business_id)

    now = datetime.now(timezone.utc)

    curr_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day = calendar.monthrange(now.year, now.month)[1]
    curr_month_end = curr_month_start.replace(day=last_day, hour=23, minute=59, second=59)

    if now.month == 1:
        prev_year, prev_month = now.year - 1, 12
    else:
        prev_year, prev_month = now.year, now.month - 1

    prev_month_start = curr_month_start.replace(year=prev_year, month=prev_month, day=1)
    prev_last_day = calendar.monthrange(prev_year, prev_month)[1]
    prev_month_end = prev_month_start.replace(day=prev_last_day, hour=23, minute=59, second=59)

    curr_query = select(func.sum(Invoice.total)).where(
        Invoice.business_id == business_id,
        Invoice.status == InvoiceStatus.PAID,
        Invoice.created_at >= curr_month_start,
        Invoice.created_at <= curr_month_end,
    )
    curr_result = await db.execute(curr_query)
    current_month_revenue = float(curr_result.scalar() or 0)

    prev_query = select(func.sum(Invoice.total)).where(
        Invoice.business_id == business_id,
        Invoice.status == InvoiceStatus.PAID,
        Invoice.created_at >= prev_month_start,
        Invoice.created_at <= prev_month_end,
    )
    prev_result = await db.execute(prev_query)
    last_month_revenue = float(prev_result.scalar() or 0)

    if last_month_revenue > 0:
        pct_change = round(
            ((current_month_revenue - last_month_revenue) / last_month_revenue) * 100, 2
        )
    else:
        pct_change = 100.0 if current_month_revenue > 0 else 0.0

    return {
        "currentMonth": calendar.month_name[now.month],
        "currentMonthRevenue": current_month_revenue,
        "lastMonth": calendar.month_name[prev_month],
        "lastMonthRevenue": last_month_revenue,
        "percentageChange": pct_change,
    }


async def top_selling_products(
    db: AsyncSession,
    current_user_id: int,
    business_id: int,
    limit: int = 5,
    days: int = 30,
) -> list[dict]:
    await _get_authorized_business(db, current_user_id, business_id)

    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        select(
            Product.id,
            Product.name,
            Product.selling_price,
            func.sum(InvoiceItem.quantity).label("total_qty"),
            func.sum(InvoiceItem.quantity * Product.selling_price).label("total_revenue"),
        )
        .join(InvoiceItem, InvoiceItem.product_id == Product.id)
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .where(
            Invoice.business_id == business_id,
            Invoice.status == InvoiceStatus.PAID,
            Invoice.created_at >= since,
        )
        .group_by(Product.id, Product.name, Product.selling_price)
        .order_by(func.sum(InvoiceItem.quantity).desc())
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "productId": r.id,
            "name": r.name,
            "sellingPrice": float(r.selling_price),
            "totalQty": int(r.total_qty),
            "totalRevenue": float(r.total_revenue),
        }
        for r in rows
    ]


async def low_stock_products(
    db: AsyncSession,
    current_user_id: int,
    business_id: int,
    threshold: int = 10,
) -> list[dict]:
    await _get_authorized_business(db, current_user_id, business_id)

    query = (
        select(Product.id, Product.name, Product.stock, Product.category)
        .where(
            Product.business_id == business_id,
            Product.stock <= threshold,
        )
        .order_by(Product.stock.asc())
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "productId": r.id,
            "name": r.name,
            "stock": r.stock,
            "category": r.category,
        }
        for r in rows
    ]


async def daily_revenue_trend(
    db: AsyncSession,
    current_user_id: int,
    business_id: int,
    days: int = 30,
) -> list[dict]:
    await _get_authorized_business(db, current_user_id, business_id)

    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        select(
            cast(Invoice.created_at, Date).label("date"),
            func.sum(Invoice.total).label("revenue"),
            func.count(Invoice.id).label("invoices"),
        )
        .where(
            Invoice.business_id == business_id,
            Invoice.status == InvoiceStatus.PAID,
            Invoice.created_at >= since,
        )
        .group_by(cast(Invoice.created_at, Date))
        .order_by(cast(Invoice.created_at, Date))
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "date": str(r.date),
            "revenue": float(r.revenue),
            "invoices": int(r.invoices),
        }
        for r in rows
    ]


async def invoice_status_breakdown(
    db: AsyncSession,
    current_user_id: int,
    business_id: int,
) -> dict:
    await _get_authorized_business(db, current_user_id, business_id)

    query = (
        select(
            Invoice.status,
            func.count(Invoice.id).label("count"),
            func.coalesce(func.sum(Invoice.total), 0).label("amount"),
        )
        .where(Invoice.business_id == business_id)
        .group_by(Invoice.status)
    )
    result = await db.execute(query)
    rows = result.all()

    breakdown = {}
    for r in rows:
        breakdown[r.status.value] = {
            "count": int(r.count),
            "amount": float(r.amount),
        }

    for s in InvoiceStatus:
        if s.value not in breakdown:
            breakdown[s.value] = {"count": 0, "amount": 0.0}

    return breakdown


async def average_order_value(
    db: AsyncSession,
    current_user_id: int,
    business_id: int,
    days: int = 30,
) -> dict:
    await _get_authorized_business(db, current_user_id, business_id)

    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        select(
            func.avg(Invoice.total).label("avg_value"),
            func.min(Invoice.total).label("min_value"),
            func.max(Invoice.total).label("max_value"),
            func.count(Invoice.id).label("order_count"),
        )
        .where(
            Invoice.business_id == business_id,
            Invoice.status == InvoiceStatus.PAID,
            Invoice.created_at >= since,
        )
    )
    result = await db.execute(query)
    row = result.one()

    return {
        "averageOrderValue": round(float(row.avg_value or 0), 2),
        "minOrderValue": float(row.min_value or 0),
        "maxOrderValue": float(row.max_value or 0),
        "orderCount": int(row.order_count),
    }


async def top_customers(
    db: AsyncSession,
    current_user_id: int,
    business_id: int,
    limit: int = 5,
    days: int = 90,
) -> list[dict]:
    await _get_authorized_business(db, current_user_id, business_id)

    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        select(
            Customer.id,
            Customer.name,
            Customer.phone_number,
            func.sum(Invoice.total).label("total_spent"),
            func.count(Invoice.id).label("order_count"),
        )
        .join(Invoice, Invoice.customer_id == Customer.id)
        .where(
            Invoice.business_id == business_id,
            Invoice.status == InvoiceStatus.PAID,
            Invoice.created_at >= since,
        )
        .group_by(Customer.id, Customer.name, Customer.phone_number)
        .order_by(func.sum(Invoice.total).desc())
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "customerId": r.id,
            "name": r.name,
            "phone": r.phone_number,
            "totalSpent": float(r.total_spent),
            "orderCount": int(r.order_count),
        }
        for r in rows
    ]


async def profit_margins(
    db: AsyncSession,
    current_user_id: int,
    business_id: int,
    days: int = 30,
) -> dict:
    await _get_authorized_business(db, current_user_id, business_id)

    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        select(
            func.sum(InvoiceItem.quantity * Product.selling_price).label("total_revenue"),
            func.sum(InvoiceItem.quantity * Product.original_price).label("total_cost"),
            func.sum(
                InvoiceItem.quantity * (Product.selling_price - Product.original_price)
            ).label("total_profit"),
        )
        .join(InvoiceItem, InvoiceItem.product_id == Product.id)
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .where(
            Invoice.business_id == business_id,
            Invoice.status == InvoiceStatus.PAID,
            Invoice.created_at >= since,
        )
    )
    result = await db.execute(query)
    row = result.one()

    total_revenue = float(row.total_revenue or 0)
    total_cost = float(row.total_cost or 0)
    total_profit = float(row.total_profit or 0)
    margin_pct = round((total_profit / total_revenue) * 100, 2) if total_revenue > 0 else 0.0

    return {
        "totalRevenue": total_revenue,
        "totalCost": total_cost,
        "totalProfit": total_profit,
        "marginPercent": margin_pct,
    }
