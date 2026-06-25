from schemas.user import User as UserProfile
from fastapi import HTTPException, status,Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.user import User as UserModel, Business as BusinessModel
from schemas.user import Business as BusinessDetails, UpdatedBusiness, UpdateUserProfile
from services.auth import hash_password
from exceptions.database import (
    DuplicateGSTNumberException,
    DatabaseIntegrityException,
    DatabaseUnexpectedException,
)
from exceptions.user import (
    UserException,
    ProfileModificationForbiddenException,
    UserNotFoundException,
    EmailAlreadyInUseException,
    PasswordTooShortException,
)


async def get_user_profile(db: AsyncSession, user_id: int) -> UserModel:
    result = await db.execute(
        select(UserModel)
        .options(selectinload(UserModel.businesses))
        .where(UserModel.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


async def get_business_details(
    db: AsyncSession,
    user_id: int,
    business_id: int,
) -> BusinessModel:
    result = await db.execute(
        select(BusinessModel).where(BusinessModel.id == business_id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    if business.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this business",
        )
    return business


async def create_business(
    db: AsyncSession,
    payload: BusinessDetails,
    current_user_id: int,
) -> BusinessModel:
    if payload.gst_number:
        result = await db.execute(
            select(BusinessModel).where(BusinessModel.gst_number == payload.gst_number)
        )
        existing_business = result.scalar_one_or_none()
        if existing_business:
            raise DuplicateGSTNumberException(
                "A business with this GST number already exists."
            )

    try:
        new_business = BusinessModel(
            user_id=current_user_id,
            name=payload.name,
            gst_number=payload.gst_number,
            phone=payload.phone,
            email=payload.email,
            address=payload.address,
            city=payload.city,
            state=payload.state,
            country=payload.country,
            postal_code=payload.postal_code,
            logo_url=payload.logo_url,
            invoice_prefix=payload.invoice_prefix,
            currency=payload.currency,
            timezone=payload.timezone,
        )
        db.add(new_business)
        await db.commit()
        await db.refresh(new_business)
        return new_business
    except IntegrityError as exc:
        await db.rollback()
        raise DatabaseIntegrityException(
            "Database integrity violation. Please check that unique constraints are satisfied."
        ) from exc
    except Exception as exc:
        await db.rollback()
        raise DatabaseUnexpectedException(
            "An unexpected error occurred while creating the business."
        ) from exc


async def update_profile(
    db: AsyncSession,
    payload: UpdateUserProfile,
    user_id: int,
    current_user_id: int,
) ->UserProfile:
    if current_user_id != user_id:
        raise ProfileModificationForbiddenException()

    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFoundException()

    try:
        if payload.name is not None:
            user.name = payload.name

        if payload.email is not None:
            existing_result = await db.execute(
                select(UserModel).where(
                    UserModel.email == payload.email,
                    UserModel.id != user_id,
                )
            )
            existing = existing_result.scalar_one_or_none()
            if existing:
                raise EmailAlreadyInUseException()
            user.email = payload.email
        if payload.avatar_url is not None:
            user.avatar_url = payload.avatar_url

        if payload.password is not None:
            if len(payload.password) >= 8:
                user.password = hash_password(payload.password)
            else:
                raise PasswordTooShortException()

        db.add(user)
        await db.commit()

        result = await db.execute(
            select(UserModel)
            .options(selectinload(UserModel.businesses))
            .where(UserModel.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        return user
    except (HTTPException, UserException):
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


async def update_business(
    db: AsyncSession,
    payload: UpdatedBusiness,
    business_id: int,
    current_user_id: int,
) -> BusinessModel:
    result = await db.execute(
        select(BusinessModel).where(BusinessModel.id == business_id)
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
            detail="You are not allowed to modify this business",
        )

    # Explicitly check for duplicate GST number to return a friendly HTTP 400 Bad Request
    if payload.gst_number:
        result = await db.execute(
            select(BusinessModel).where(
                BusinessModel.gst_number == payload.gst_number,
                BusinessModel.id != business_id,
            )
        )
        existing_business = result.scalar_one_or_none()
        if existing_business:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A business with this GST number already exists.",
            )

    try:
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(business, key, value)

        db.add(business)
        await db.commit()
        await db.refresh(business)
        return business
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity violation. Please check that unique constraints are satisfied.",
        ) from exc
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the business.",
        ) from exc


async def delete_user(
    db: AsyncSession,
    user_id: int,
    current_user_id: int,
) -> None:
    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this user",
        )
    try:
        result = await db.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        await db.delete(user)
        await db.commit()
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


async def delete_business(
    db: AsyncSession,
    business_id: int,
    current_user_id: int,
) -> None:
    result = await db.execute(
        select(BusinessModel).where(BusinessModel.id == business_id)
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
            detail="You are not allowed to delete this business",
        )

    try:
        await db.delete(business)
        await db.commit()
        return Response(content="Business information deleted successfully",
                        status_code=200)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
