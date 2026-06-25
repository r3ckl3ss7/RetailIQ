from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_async_db
from middlewares.auth import auth, current_user
from exceptions.database import (
    DuplicateGSTNumberException,
    DatabaseIntegrityException,
    DatabaseUnexpectedException,
)
from exceptions.business import BusinessException
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

@router.get("/{user_id}", response_model=UserProfile)
async def user_profile(
    user_id: int,
    _: int = Depends(auth),
    db: AsyncSession = Depends(get_async_db),
) -> UserProfile:
    return await get_user_profile_service(db, user_id)

@router.get('/{user_id}/{business_id}', response_model=BusinessDetails)
async def business_details(
    user_id: int,
    business_id: int,
    _: int = Depends(auth),
    db: AsyncSession = Depends(get_async_db),
) -> BusinessDetails:
    return await get_business_details_service(db, user_id, business_id)

@router.post('/business', response_model=BusinessDetails)
async def create_business(
    payload: BusinessDetails,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
) -> BusinessDetails:
    try:
        return await create_business_service(db, payload, current_user_id)
    except DuplicateGSTNumberException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )
    except DatabaseIntegrityException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )
    except DatabaseUnexpectedException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        )

from exceptions.user import UserException


@router.patch('/{user_id}', response_model=UserProfile)
async def update_profile(
    payload: UpdateUserProfile,
    user_id: int,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
) -> UserProfile:
    try:
        return await update_profile_service(db, payload, user_id, current_user_id)
    except UserException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "error_code": exc.error_code}
        )

@router.patch('/business/{business_id}', response_model=BusinessDetails)
async def update_business_details(
    payload: UpdatedBusiness,
    business_id: int,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
) -> BusinessDetails:
    try:
        return await update_business_service(db, payload, business_id, current_user_id)
    except BusinessException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.error_message,
        )
    except DatabaseIntegrityException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )
    except DatabaseUnexpectedException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        )


@router.delete('/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user_id:int=Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await delete_user_service(db, user_id, current_user_id)
    except UserException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )
    except DatabaseUnexpectedException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        )

@router.delete('/business/{business_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: int,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await delete_business_service(db, business_id, current_user_id)
    except BusinessException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.error_message,
        )
    except DatabaseUnexpectedException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        )