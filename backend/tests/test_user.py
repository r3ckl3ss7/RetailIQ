import sys
import os
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_path)

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException, status

import models.user
import models.products
import models.invoice
import models.ai
import models.auth

from models.user import User as UserModel, Business as BusinessModel
from schemas.user import Business as BusinessDetails, UpdatedBusiness, UpdateUserProfile
from services.user import (
    get_user_profile,
    get_business_details,
    create_business,
    update_profile,
    update_business,
    delete_user,
    delete_business,
)
from exceptions.database import DuplicateGSTNumberException
from exceptions.user import ProfileModificationForbiddenException, UserDeletionForbiddenException
from exceptions.business import BusinessNotFoundException, BusinessModificationForbiddenException, BusinessDeletionForbiddenException

def mock_db_result(value=None):
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = value
    return mock_res

@pytest.mark.asyncio
async def test_get_user_profile_success():
    db = AsyncMock()
    user_mock = UserModel(id=1, email="test@example.com", name="Test User")
    db.execute.return_value = mock_db_result(user_mock)
    
    user = await get_user_profile(db, 1)
    assert user.id == 1
    assert user.name == "Test User"
    assert user.email == "test@example.com"

@pytest.mark.asyncio
async def test_get_user_profile_not_found():
    db = AsyncMock()
    db.execute.return_value = mock_db_result(None)
    
    with pytest.raises(HTTPException) as excinfo:
        await get_user_profile(db, 999)
    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert excinfo.value.detail == "User not found"

@pytest.mark.asyncio
async def test_get_business_details_success():
    db = AsyncMock()
    biz_mock = BusinessModel(id=10, user_id=1, name="My Store")
    db.execute.return_value = mock_db_result(biz_mock)
    
    business = await get_business_details(db, user_id=1, business_id=10)
    assert business.id == 10
    assert business.name == "My Store"
    assert business.user_id == 1

@pytest.mark.asyncio
async def test_get_business_details_forbidden():
    db = AsyncMock()
    biz_mock = BusinessModel(id=10, user_id=2, name="Not My Store")
    db.execute.return_value = mock_db_result(biz_mock)
    
    with pytest.raises(HTTPException) as excinfo:
        await get_business_details(db, user_id=1, business_id=10)
    assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
    assert "not allowed to access" in excinfo.value.detail

@pytest.mark.asyncio
async def test_create_business_success():
    db = AsyncMock()
    db.add = MagicMock()
    db.execute.return_value = mock_db_result(None)
    
    def mock_refresh(instance):
        instance.id = 55
    db.refresh.side_effect = mock_refresh
    
    payload = BusinessDetails(
        name="Fresh Shop",
        gst_number="27GSTNUMBER1234Z",
        phone="9999999999",
        email="fresh@example.com"
    )
    
    new_biz = await create_business(db, payload, current_user_id=1)
    assert new_biz.name == "Fresh Shop"
    assert new_biz.user_id == 1
    assert new_biz.id == 55
    assert db.add.call_count >= 1
    assert db.commit.call_count >= 1

@pytest.mark.asyncio
async def test_create_business_duplicate_gst():
    db = AsyncMock()
    existing_biz = BusinessModel(id=20, user_id=2, gst_number="27GSTNUMBER1234Z", name="Other Shop")
    db.execute.return_value = mock_db_result(existing_biz)
    
    payload = BusinessDetails(
        name="Fresh Shop",
        gst_number="27GSTNUMBER1234Z"
    )
    
    with pytest.raises(DuplicateGSTNumberException):
        await create_business(db, payload, current_user_id=1)

@pytest.mark.asyncio
async def test_update_profile_success():
    db = AsyncMock()
    db.add = MagicMock()
    user_mock = UserModel(id=1, email="old@example.com", name="Old Name")
    db.execute.side_effect = [
        mock_db_result(user_mock),
        mock_db_result(None),
        mock_db_result(user_mock)
    ]
    
    payload = UpdateUserProfile(name="New Name", email="new@example.com")
    updated_user = await update_profile(db, payload, user_id=1, current_user_id=1)
    assert updated_user.name == "New Name"
    assert updated_user.email == "new@example.com"
    assert db.commit.call_count >= 1

@pytest.mark.asyncio
async def test_update_profile_forbidden():
    db = AsyncMock()
    payload = UpdateUserProfile(name="Hacker")
    
    with pytest.raises(ProfileModificationForbiddenException):
        await update_profile(db, payload, user_id=2, current_user_id=1)

@pytest.mark.asyncio
async def test_delete_business_success():
    db = AsyncMock()
    biz_mock = BusinessModel(id=10, user_id=1, name="My Shop")
    db.execute.return_value = mock_db_result(biz_mock)
    
    response = await delete_business(db, business_id=10, current_user_id=1)
    assert response.status_code == 200
    assert db.delete.await_count >= 1
    assert db.commit.call_count >= 1

@pytest.mark.asyncio
async def test_delete_business_forbidden():
    db = AsyncMock()
    biz_mock = BusinessModel(id=10, user_id=2, name="Other Shop")
    db.execute.return_value = mock_db_result(biz_mock)
    
    with pytest.raises(BusinessDeletionForbiddenException):
        await delete_business(db, business_id=10, current_user_id=1)
