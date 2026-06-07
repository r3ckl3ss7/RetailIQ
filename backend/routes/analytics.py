from fastapi import APIRouter, Depends, status, HTTPException
from middlewares.auth import current_user
from db.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum
from typing import Optional
from sqlalchemy import func, select
from models.invoice import Invoice, InvoiceStatus, Customer
from models.user import Business
from datetime import datetime, timedelta, timezone

router = APIRouter(
    prefix='/dashboard',
    tags=['dashboard']
)

class Time(str, Enum):
    today = 'today'
    week = 'week'
    month = 'month'
    year = 'year'
    all = 'all'

@router.get('/')
async def numeric_analytics(
    business_id: int,
    time: Time = Time.month,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db)
):
    business_result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = business_result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if business.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    now = datetime.now(timezone.utc)
    if time == Time.today:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time == Time.week:
        start_date = now - timedelta(days=7)
    elif time == Time.month:
        start_date = now - timedelta(days=30)
    elif time == Time.year:
        start_date = now - timedelta(days=365)
    else:
        start_date = datetime.min.replace(tzinfo=timezone.utc)

    sales_query = select(func.sum(Invoice.total)).where(
        Invoice.business_id == business_id,
        Invoice.status == InvoiceStatus.PAID,
        Invoice.created_at >= start_date
    )
    sales_result = await db.execute(sales_query)
    total_sales = sales_result.scalar() or 0.0

    count_query = select(func.count(Invoice.id)).where(
        Invoice.business_id == business_id,
        Invoice.created_at >= start_date
    )
    count_result = await db.execute(count_query)
    total_invoices = count_result.scalar() or 0

    customer_query = select(func.count(func.distinct(Invoice.customer_id))).where(
        Invoice.business_id == business_id,
        Invoice.customer_id.isnot(None),
        Invoice.created_at >= start_date
    )
    customer_result = await db.execute(customer_query)
    recent_customers = customer_result.scalar() or 0

    return {
        "totalSales": float(total_sales),
        "totalInvoices": total_invoices,
        "recentCustomers": recent_customers
    }
