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

from models.products import Product as ProductModel
from models.user import Business as BusinessModel
from schemas.products import ProductCreate, ProductUpdate
from services.products import (
    list_products,
    search_products,
    get_product_by_id,
    create_product,
    update_product,
    delete_product,
)
from exceptions.pruduct import ProductNotFound
from exceptions.business import BusinessNotFoundException, UnauthorisedBusinessAccess

def mock_db_result(value=None):
    mock_res = MagicMock()
    if isinstance(value, list):
        mock_res.scalars.return_value.all.return_value = value
    else:
        mock_res.scalar_one_or_none.return_value = value
    return mock_res

@pytest.mark.asyncio
async def test_list_products_success():
    db = AsyncMock()
    biz_mock = BusinessModel(id=1, user_id=10, name="My Shop")
    prods_mock = [
        ProductModel(id=100, name="Phone", business_id=1, selling_price=Decimal("15000")),
        ProductModel(id=101, name="Laptop", business_id=1, selling_price=Decimal("50000"))
    ]
    db.execute.side_effect = [
        mock_db_result(biz_mock),
        mock_db_result(prods_mock)
    ]
    
    products = await list_products(db, business_id=1, current_user_id=10)
    assert len(products) == 2
    assert products[0].name == "Phone"
    assert products[1].name == "Laptop"

@pytest.mark.asyncio
async def test_list_products_unauthorised_business():
    db = AsyncMock()
    biz_mock = BusinessModel(id=1, user_id=20, name="Other Shop")
    db.execute.return_value = mock_db_result(biz_mock)
    
    with pytest.raises(UnauthorisedBusinessAccess):
        await list_products(db, business_id=1, current_user_id=10)

@pytest.mark.asyncio
async def test_get_product_by_id_success():
    db = AsyncMock()
    prod_mock = ProductModel(id=100, name="Phone", business_id=1)
    biz_mock = BusinessModel(id=1, user_id=10)
    db.execute.side_effect = [
        mock_db_result(prod_mock),
        mock_db_result(biz_mock)
    ]
    
    product = await get_product_by_id(db, product_id=100, current_user_id=10)
    assert product.id == 100
    assert product.name == "Phone"

@pytest.mark.asyncio
async def test_get_product_by_id_not_found():
    db = AsyncMock()
    db.execute.return_value = mock_db_result(None)
    
    with pytest.raises(ProductNotFound):
        await get_product_by_id(db, product_id=999, current_user_id=10)

@pytest.mark.asyncio
async def test_search_products_by_name():
    db = AsyncMock()
    biz_mock = BusinessModel(id=1, user_id=10)
    prods_mock = [ProductModel(id=100, name="Phone", business_id=1)]
    db.execute.side_effect = [
        mock_db_result(biz_mock),
        mock_db_result(prods_mock)
    ]
    
    products = await search_products(db, business_id=1, sku=None, barcode=None, name="phone", current_user_id=10)
    assert len(products) == 1
    assert products[0].name == "Phone"

@pytest.mark.asyncio
async def test_create_product_success():
    db = AsyncMock()
    db.add = MagicMock()
    biz_mock = BusinessModel(id=1, user_id=10)
    db.execute.return_value = mock_db_result(biz_mock)
    
    def mock_refresh(instance):
        instance.id = 102
    db.refresh.side_effect = mock_refresh
    
    payload = ProductCreate(
        name="Keyboard",
        business_id=1,
        original_price=Decimal("1000"),
        selling_price=Decimal("1500"),
        stock=50,
        category="Electronics",
        sku="KEY-12",
        barcode="1234567890",
        description="USB Keyboard"
    )
    
    product = await create_product(db, payload, current_user_id=10)
    assert product.name == "Keyboard"
    assert product.id == 102
    assert product.business_id == 1
    assert db.add.call_count >= 1
    assert db.commit.call_count >= 1

@pytest.mark.asyncio
async def test_update_product_success():
    db = AsyncMock()
    prod_mock = ProductModel(id=100, name="Phone", business_id=1, stock=10)
    biz_mock = BusinessModel(id=1, user_id=10)
    db.execute.side_effect = [
        mock_db_result(prod_mock),
        mock_db_result(biz_mock)
    ]
    
    payload = ProductUpdate(name="Phone V2", stock=20)
    updated_prod = await update_product(db, product_id=100, payload=payload, current_user_id=10)
    assert updated_prod.name == "Phone V2"
    assert updated_prod.stock == 20
    assert db.commit.call_count >= 1

@pytest.mark.asyncio
async def test_delete_product_success():
    db = AsyncMock()
    prod_mock = ProductModel(id=100, name="Phone", business_id=1)
    biz_mock = BusinessModel(id=1, user_id=10)
    db.execute.side_effect = [
        mock_db_result(prod_mock),
        mock_db_result(biz_mock)
    ]
    
    await delete_product(db, product_id=100, current_user_id=10)
    assert db.delete.await_count >= 1
    assert db.commit.call_count >= 1
