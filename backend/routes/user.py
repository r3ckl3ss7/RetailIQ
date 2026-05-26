from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.user import (
    User as UserModel,
    Business as BusinessModel,
    ContactDetails as ContactDetailsModel,
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
        if not payload.contact_details:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact details are required",
            )

        new_business = BusinessModel(
            user_id=current_user_id,
            business_name=payload.business_name,
            category=payload.category,
            description=payload.description,
            contact_details=ContactDetailsModel(
                phone_number=payload.contact_details.phone_number,
                alt_phone_no=payload.contact_details.alt_phone_no,
                city=payload.contact_details.city,
                district=payload.contact_details.district,
                state=payload.contact_details.state,
                country=payload.contact_details.country,
                postal_code=payload.contact_details.postal_code,
                address_line=payload.contact_details.address_line,
            ),
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
        business.business_name = payload.business_name
        business.category = payload.category
        business.description = payload.description

        if payload.contact_details:
            cd = business.contact_details
            if cd:
                cd.phone_number = payload.contact_details.phone_number
                cd.alt_phone_no = payload.contact_details.alt_phone_no
                cd.city = payload.contact_details.city
                cd.district = payload.contact_details.district
                cd.state = payload.contact_details.state
                cd.country = payload.contact_details.country
                cd.postal_code = payload.contact_details.postal_code
                cd.address_line = payload.contact_details.address_line
            else:
                business.contact_details = ContactDetailsModel(
                    phone_number=payload.contact_details.phone_number,
                    alt_phone_no=payload.contact_details.alt_phone_no,
                    city=payload.contact_details.city,
                    district=payload.contact_details.district,
                    state=payload.contact_details.state,
                    country=payload.contact_details.country,
                    postal_code=payload.contact_details.postal_code,
                    address_line=payload.contact_details.address_line,
                )

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