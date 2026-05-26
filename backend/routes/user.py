from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.user import User as UserModel, Business as BusinessModel
from middlewares.auth import auth

from schemas.user import User as UserProfile, Business as BusinessDetails

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


