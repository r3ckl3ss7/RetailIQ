from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.user import (
    User as UserModel,
    Business as BusinessModel,
)
from middlewares.auth import auth, current_user
from services.auth import hash_password

from schemas.user import (
    User as UserProfile,
    Business as BusinessDetails,
    UpdatedBusiness,
    UpdateUserProfile,
)

router = APIRouter(prefix="/user", tags=["user"])

# GET - Profile
@router.get("/{user_id}", response_model=UserProfile)
def user_profile(
    user_id: int,
    _: int = Depends(auth),
    db: Session = Depends(get_db),
) -> UserProfile:
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user

# GET - Business
@router.get('/{user_id}/{business_id}', response_model=BusinessDetails)
async def business_details(
    user_id: int,
    business_id: int,
    _: int = Depends(auth),
    db: Session = Depends(get_db),
) -> BusinessDetails:
    business = (
        db.query(BusinessModel).filter(BusinessModel.id == business_id).first()
    )

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

# POST - Business
@router.post('/business', response_model=BusinessDetails)
async def create_business(
    payload: BusinessDetails,
    current_user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
) -> BusinessDetails:
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
        db.commit()
        db.refresh(new_business)

        return new_business

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

# PATCH - Profile
@router.patch('/{user_id}', response_model=UserProfile)
async def update_profile(
    payload: UpdateUserProfile,
    user_id: int,
    current_user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to modify this profile",
        )

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        if payload.name is not None:
            user.name = payload.name

        if payload.email is not None:
            existing = (
                db.query(UserModel)
                .filter(
                    UserModel.email == payload.email,
                    UserModel.id != user_id,
                )
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use",
                )
            user.email = payload.email

        if payload.password is not None:
            user.password = hash_password(payload.password)

        db.add(user)
        db.commit()
        db.refresh(user)

        return user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

# PATCH - Business
@router.patch('/business/{business_id}', response_model=BusinessDetails)
async def update_business_details(
    payload: UpdatedBusiness,
    business_id: int,
    current_user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
) -> BusinessDetails:
    business = (
        db.query(BusinessModel)
        .filter(BusinessModel.id == business_id)
        .first()
    )
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

    try:
        if payload.name is not None:
            business.name = payload.name
        if payload.gst_number is not None:
            business.gst_number = payload.gst_number
        if payload.phone is not None:
            business.phone = payload.phone
        if payload.email is not None:
            business.email = payload.email
        if payload.address is not None:
            business.address = payload.address
        if payload.city is not None:
            business.city = payload.city
        if payload.state is not None:
            business.state = payload.state
        if payload.country is not None:
            business.country = payload.country
        if payload.postal_code is not None:
            business.postal_code = payload.postal_code
        if payload.logo_url is not None:
            business.logo_url = payload.logo_url
        if payload.invoice_prefix is not None:
            business.invoice_prefix = payload.invoice_prefix
        if payload.currency is not None:
            business.currency = payload.currency
        if payload.timezone is not None:
            business.timezone = payload.timezone

        db.add(business)
        db.commit()
        db.refresh(business)

        return business
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# DELETE - User
@router.delete('/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user_id:int=Depends(current_user),
    db: Session = Depends(get_db),
):
    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this user",
        )
    try:
        user=db.query(UserModel).filter(UserModel.id==user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )        
        db.delete(
            user
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

# DELETE Business 
@router.delete('/business/{business_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: int,
    current_user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    business=db.query(BusinessModel).filter(BusinessModel.id==business_id).first()
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
        db.delete(business)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )