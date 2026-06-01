from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_async_db
from middlewares.auth import auth, current_user
from services.user import (
    create_business as create_business_service,
    delete_business as delete_business_service,
    delete_user as delete_user_service,
    get_business_details as get_business_details_service,
    get_user_profile as get_user_profile_service,
    update_business as update_business_service,
    update_profile as update_profile_service,
)

from schemas.user import (
    User as UserProfile,
    Business as BusinessDetails,
    UpdatedBusiness,
    UpdateUserProfile,
)

router = APIRouter(prefix="/user", tags=["user"])

# GET - Profile
@router.get("/{user_id}", response_model=UserProfile)
async def user_profile(
    user_id: int,
    _: int = Depends(auth),
    db: AsyncSession = Depends(get_async_db),
) -> UserProfile:
    return await get_user_profile_service(db, user_id)

# GET - Business
@router.get('/{user_id}/{business_id}', response_model=BusinessDetails)
async def business_details(
    user_id: int,
    business_id: int,
    _: int = Depends(auth),
    db: AsyncSession = Depends(get_async_db),
) -> BusinessDetails:
    return await get_business_details_service(db, user_id, business_id)

# POST - Business
@router.post('/business', response_model=BusinessDetails)
async def create_business(
    payload: BusinessDetails,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
) -> BusinessDetails:
    return await create_business_service(db, payload, current_user_id)

# PATCH - Profile
@router.patch('/{user_id}', response_model=UserProfile)
async def update_profile(
    payload: UpdateUserProfile,
    user_id: int,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
) -> UserProfile:
    return await update_profile_service(db, payload, user_id, current_user_id)

# PATCH - Business
@router.patch('/business/{business_id}', response_model=BusinessDetails)
async def update_business_details(
    payload: UpdatedBusiness,
    business_id: int,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
) -> BusinessDetails:
    return await update_business_service(db, payload, business_id, current_user_id)


# DELETE - User
@router.delete('/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user_id:int=Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
):
    return await delete_user_service(db, user_id, current_user_id)

# DELETE Business 
@router.delete('/business/{business_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: int,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
):
    return await delete_business_service(db, business_id, current_user_id)