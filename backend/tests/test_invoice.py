import sys
import os
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_path)

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

import models.user
import models.products
import models.invoice
import models.ai
import models.auth

from models.invoice import Invoice as InvoiceModel, InvoiceItem as InvoiceItemModel, InvoiceStatus, InvoiceSource
from models.products import Product as ProductModel
from models.user import Business as BusinessModel
from schemas.invoice import InvoiceCreatePayload, InvoiceItemInput, CustomerInput
from services.invoice import (
    _to_decimal,
    _quantize_money,
    _calculate_totals,
    get_invoice_by_id,
    create_invoice,
)
from exceptions.invoice import InvalidInvoiceException, InsufficientStockException
from exceptions.business import UnauthorisedBusinessAccess

def mock_db_result(value=None):
    mock_res = MagicMock()
    if isinstance(value, list):
        mock_res.scalars.return_value.all.return_value = value
        mock_res.scalars.return_value.first.return_value = value[0] if value else None
    else:
        mock_res.scalar_one_or_none.return_value = value
        mock_res.scalar_one.return_value = value
    return mock_res

def test_decimal_conversion():
    assert _to_decimal(10) == Decimal("10")
    assert _to_decimal("15.50") == Decimal("15.50")
    assert _to_decimal(None) is None

def test_quantize_money():
    assert _quantize_money(Decimal("10.123")) == Decimal("10.12")
    assert _quantize_money(Decimal("10.125")) == Decimal("10.13")

def test_calculate_totals_success():
    payload = InvoiceCreatePayload(
        business_id=1,
        items=[InvoiceItemInput(sku="P1", quantity=2)],
        tax=Decimal("18.00"),
        discount=Decimal("5.00"),
        subtotal=Decimal("200.00"),
        total=Decimal("213.00")
    )
    product = ProductModel(id=100, selling_price=Decimal("100.00"))
    resolved_items = [(product, 2)]
    
    subtotal, tax, discount, total = _calculate_totals(payload, resolved_items)
    assert subtotal == Decimal("200.00")
    assert tax == Decimal("18.00")
    assert discount == Decimal("5.00")
    assert total == Decimal("213.00")

def test_calculate_totals_mismatch():
    payload = InvoiceCreatePayload(
        business_id=1,
        items=[InvoiceItemInput(sku="P1", quantity=2)],
        subtotal=Decimal("100.00")
    )
    product = ProductModel(id=100, selling_price=Decimal("100.00"))
    resolved_items = [(product, 2)]
    
    with pytest.raises(InvalidInvoiceException) as excinfo:
        _calculate_totals(payload, resolved_items)
    assert "Subtotal mismatch" in str(excinfo.value)

@pytest.mark.asyncio
async def test_get_invoice_by_id_success():
    db = AsyncMock()
    biz_mock = BusinessModel(id=1, user_id=10)
    invoice_mock = InvoiceModel(id=500, business_id=1, status=InvoiceStatus.PAID)
    
    db.execute.side_effect = [
        mock_db_result(invoice_mock),
        mock_db_result(biz_mock)
    ]
    
    invoice = await get_invoice_by_id(db, invoice_id=500, current_user_id=10)
    assert invoice.id == 500
    assert invoice.status == InvoiceStatus.PAID

@pytest.mark.asyncio
async def test_get_invoice_by_id_unauthorised():
    db = AsyncMock()
    biz_mock = BusinessModel(id=1, user_id=20)  
    invoice_mock = InvoiceModel(id=500, business_id=1)
    
    db.execute.side_effect = [
        mock_db_result(invoice_mock),
        mock_db_result(biz_mock)
    ]
    
    with pytest.raises(UnauthorisedBusinessAccess):
        await get_invoice_by_id(db, invoice_id=500, current_user_id=10)

@pytest.mark.asyncio
async def test_create_invoice_insufficient_stock():
    db = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    
    biz_mock = BusinessModel(id=1, user_id=10)
    product_mock = ProductModel(id=100, business_id=1, selling_price=Decimal("100.00"), stock=2)  
    
    db.execute.side_effect = [
        mock_db_result(biz_mock),
        mock_db_result(product_mock)
    ]
    
    payload = InvoiceCreatePayload(
        business_id=1,
        items=[InvoiceItemInput(product_id=100, quantity=5)],
        status=InvoiceStatus.PAID,
        source=InvoiceSource.ONLINE
    )
    
    with pytest.raises(InsufficientStockException) as excinfo:
        await create_invoice(db, payload, current_user_id=10)
    assert "Insufficient stock" in str(excinfo.value)

@pytest.mark.asyncio
async def test_create_invoice_success():
    db = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    
    biz_mock = BusinessModel(id=1, user_id=10)
    product_mock = ProductModel(id=100, business_id=1, selling_price=Decimal("100.00"), stock=10)
    invoice_mock = InvoiceModel(id=500, business_id=1, status=InvoiceStatus.PAID)
    
    db.execute.side_effect = [
        mock_db_result(biz_mock),
        mock_db_result(product_mock),
        mock_db_result(invoice_mock)
    ]
    
    payload = InvoiceCreatePayload(
        business_id=1,
        items=[InvoiceItemInput(product_id=100, quantity=2)],
        status=InvoiceStatus.PAID,
        source=InvoiceSource.ONLINE
    )
    
    invoice = await create_invoice(db, payload, current_user_id=10)
    assert invoice.id == 500
    assert product_mock.stock == 8
    assert db.add.call_count >= 2  
    assert db.commit.call_count >= 1
